# 🔥 The Dev Journey — From Chaos to (Somewhat) Clean Architecture

*A first-person account of the battles, bugs, breakthroughs, and one very
deliberate architectural U-turn. And then another one. And then a few more.*

Hey there, future me (and anyone curious about the real process). 👋

This isn't the polished README. That's [README.md](./README.md).
This is the raw, unfiltered account of building a distributed system while
simultaneously learning Flutter, Spring Boot, Kafka, WebSockets, BLoC, MongoDB,
and whatever else sounded like a good idea at 2am.

Buckle up. 😅

---

## 🔥 The Beginning: "How hard can it be?"

Started with a simple goal: detect hearts and stars in real-time using YOLOv8
on a Flutter app. Sounds clean, right?

First major realization: my code was a mess. Controllers calling APIs directly,
hardcoded URLs everywhere, no separation of concerns. It worked, sure — but like
a house of cards.

Cold shower moment 💦: the architecture wasn't interview-ready. Not portfolio-worthy.

Then came the refactor. Which became an overhaul. Which became "let me just add
Kafka." Which became 27 containers.

I regret nothing.

---

## ⚡ The GetX Phase: The Seduction of Simplicity

With GetX, things clicked fast. Reactive state in one line:

```dart
final isCameraInitialized = false.obs;
// UI rebuilds automatically. No setState. No boilerplate. Pure magic.
```

And it *was* magic. For a while.

The `VideoDetectionController` grew. Then it kept growing. Camera lifecycle,
WebSocket streams, typewriter timers, cursor blink timers, AI response metadata
— all in one file. 300 lines. Then 400. Every method knew too much about
everything else.

And then I tried to write a test. 😭

`Get.find<VideoDetectionController>()` inside `AIMessagePanel` meant the widget
was hard-coupled to GetX's service locator. Testing in isolation? Basically
impossible without spinning up the entire GetX container.

GetX wasn't wrong. It was the right tool for the prototype phase. The problem
was staying there too long.

---

## 🏗️ The Great Migration: GetX → BLoC

The decision to migrate wasn't dramatic. It was just... obvious.

The migration was surgical:
- `VideoDetectionController` → `VideoDetectionBloc` (3 files: bloc, event, state)
- `Obx(() => ...)` → `context.select()` with Dart Records
- `Get.find<VideoDetectionController>()` → `context.read<VideoDetectionBloc>()`
- `Get.toNamed(AppRoutes.home)` → `Navigator.pushNamed(context, AppRoutes.home)`
- `GetMaterialApp` → `MaterialApp`
- 7 `.obs` variables → 1 immutable `VideoDetectionState` with `copyWith()`

The nested `Obx()` inside `AIMessagePanel` (a reactive scope inside another
reactive scope for the cursor blink) became a plain `AnimatedOpacity` reading
a bool from state. Cleaner. Testable. No hidden subscriptions.

The typewriter timer dispatching `_TypewriterTicked` events every 50ms was the
most interesting design decision — timers can't call `emit()` directly because
they outlive the event handler's `Emitter` scope. The solution: dispatch internal
events via `add()` from the timer callback, re-entering the BLoC pipeline safely.
A subtle but important pattern.

**The lesson:** GetX for speed, BLoC for scale. Knowing *when* to switch is more
valuable than dogmatically picking one from the start.

---

## 🎯 The Bounding Box Nightmare

This one tested my sanity. Detections worked, WebSocket sent frames, backend
responded... but the bounding boxes floated in space like a Dalí painting. 🎨

The problem: coordinate transformations. YOLO returns normalized coordinates (0-1)
but I was multiplying by image size, then scaling to screen, forgetting
letterboxing, camera rotation, aspect ratios — all at once.

```dart
print('Raw bbox: $bbox');
print('Normalized: x1=$x1_norm, y1=$y1_norm');
print('Screen pixels: left=$left, top=$top');
```

Logs everywhere. Console looked like The Matrix. But it worked — got those boxes
aligned perfectly and understood every coordinate space involved. ✅

---

## 🔌 Android Emulator: "10.0.2.2? What sorcery is this?"

2 hours of 404 errors from a backend that was clearly running. URL correct,
ports open, backend healthy...

The emulator is its own virtual machine. `localhost` is itself. `10.0.2.2`
is your machine.

```dart
if (Platform.isAndroid) return "http://10.0.2.2:8000";  // Magic IP
```

Lesson: read the docs before debugging for hours. 📚

---

## 🕸️ WebSocket Reconnection: The Silent Killer

WebSocket would connect, send a few frames, then... silence. No errors. No crashes.
Dead air.

Built a proper reconnection system: max 5 attempts, 3-second delay, graceful
degradation.

```dart
void _scheduleReconnect() {
  if (_reconnectAttempts >= _maxReconnectAttempts) return;
  _reconnectTimer = Timer(const Duration(seconds: 3), () => connect());
}
```

Drop WiFi? Auto-reconnects when you're back. That's resilience. 🔄

---

## 🧠 The LLM Gateway: The Part I'm Most Proud Of

The concept: every 4 frames, the backend doesn't just return YOLO detections —
it sends back an AI-generated commentary about what it sees. But a raw Gemini
call on every 4th frame would be expensive and slow (~3000ms).

The solution: Redis LRU cache keyed on detection context.

```
Detection patterns → Redis lookup → cache hit (0.03ms) ⚡
                                 → cache miss → Gemini/Ollama/Go/Dart (~3000ms)
```

80% cache hit rate. Average latency dropped from ~3000ms to ~300ms.

The Flutter side shows this in real time: the ⚡ Instant badge fires on cache
hits. The personality colors change based on which runtime responded (purple for
Gemini, pink for Dart, blue for Go, green for cache/Ollama). The typewriter
animation paces the response at 2 chars per 50ms tick.

Four runtimes (Python/Gemini, Dart, Go, Ollama) exist partly to demonstrate
polyglot architecture and partly because I was genuinely curious whether the
response quality varied. Spoiler: it does.

---

## 📦 Kafka: From "Future Plan" to Production

For an embarrassingly long time, the README had a section called
"Future: Kafka Integration" with a pretty diagram of how it *would* work someday.

Then I built it.

The inference events from the LLM Gateway flow through Kafka → Express Analytics
→ MongoDB. The Kafka producer uses `asyncio.create_task()` — fire and forget.
The Flutter client gets its response immediately; Kafka persistence happens in
parallel. The Express Analytics service consumes those events independently.

If analytics goes down, events queue in Kafka and replay when it comes back.
The gateway has zero knowledge that analytics exists.

That's the architectural benefit of Kafka beyond just "async processing."

---

## 🍃 MongoDB: Right Tool, Right Job (Finally Understanding What That Means)

PostgreSQL is my default. But when I started designing the inference log schema,
I kept running into nullable column hell.

Each LLM runtime returns different metadata. A cache hit has no `prompt_tokens`.
Ollama has `model_name`. Gemini has `safety_ratings`. In PostgreSQL I'd need
nullable columns everywhere or a JSONB blob.

MongoDB's document model solved this cleanly. This was the first time I genuinely
reached for MongoDB because it genuinely fit better, not because someone told me
to. That distinction matters.

---

## 🐳 Docker: The "It Works on My Machine" Killer

Backend in Docker, frontend in emulator — should be simple, right?

Plot twist #1: Docker containers have their own network. Backend on
`localhost:8000` inside Docker isn't accessible from emulator's `10.0.2.2:8000`.

Solution: expose ports properly in `docker-compose.yml`.

Plot twist #2: Android emulator ran out of disk space. Those AVDs eat storage.

Solution: move emulator to another drive. Also `flutter clean` is your friend.
Run it regularly.

Plot twist #3: `docker compose up` with a YAML parsing error because I accidentally
pasted the entire compose file twice. Line 299, "did not find expected key."

Solution: `sed -n '290,310p' docker-compose.yml` — identify the duplicate, delete it.

---

## 🪲 The `pydantic-core` Incident

Created a Python venv with Python 3.14 (Fedora 44's default). `pydantic-core`
tried to compile from source using Rust because no pre-built wheel existed for 3.14.
Rust compilation failed. Took 10 minutes to figure out why `pip install` was
downloading Rust.

Solution: `python3.12 -m venv .venv`. Problem solved in 30 seconds.

This is the kind of debugging that doesn't show up in tutorials but takes up
real time in real projects.

---

## 🏋️ The Google Interview

Reached Google's final round (L4, Messages team, Kraków) after 187+ hours of
algorithm preparation — tackling the hardest problems first. The behavioral round
was apparently among the best the recruiter had seen. Fell short on the coding round.

Google retained my profile. The process taught me more about my own strengths
and gaps than any resource online. 0 regrets.

Also reached final stages at Amazon, Microsoft, IBM, and Capital One during the
same period. None converted. Each one sharpened something.

---

## 🧠 Lessons Learned (The Hard Way)

**1. GetX is great — until it isn't.**
Prototype with it. Migrate when the complexity demands it. Knowing *when* to
switch is more valuable than dogmatically picking one from the start.

**2. BLoC verbosity is a feature.**
The extra files force you to think about the shape of your state machine before
you write a single handler. That thinking pays off.

**3. Caching is a superpower.**
The Redis LRU layer turned a 3000ms bottleneck into a 0.03ms response 80% of
the time. Always ask: "what repeats here, and can I cache it?"

**4. Platform quirks are real.**
Android emulator networking, iOS permission flows, Python 3.14 breaking
pydantic-core — test on real devices early and often, and always check what
Python version your venv is using.

**5. Comments are documentation.**
Every architectural decision in this codebase is explained in-line. Future me
(and recruiters) thank past me for this every time.

**6. The right tool for the right job takes experience to see.**
You don't know MongoDB is better for variable-schema data until you've fought
PostgreSQL's nullable columns for an afternoon. Experience is expensive and
non-transferable.

**7. AI assistants are game-changers — but you still debug it yourself.**
Claude helped think through BLoC migration patterns, Redis caching strategy,
Kafka producer design, MongoDB schema decisions. The bugs were still mine to fix.
The architectural instincts are still mine. The AI accelerates — it doesn't replace.

---

## 🎯 What's Next

- Angular dashboard — Apollo Client setup, analytics visualization components
- Django service — user management + Django Admin (FastAPI and Django solve different problems)
- Flutter AI message panel — fix display on emulator (VSCode external config)
- React portfolio — content for the login → welcome page
- BLoC unit tests with `bloc_test` package

---

## 💬 Final Thoughts

This project taught me more than any tutorial could. The GetX phase, the BLoC
migration, the LRU caching insight, the coordinate math, the WebSocket resilience,
the Kafka pipeline, the MongoDB schema decision — none of that came from a course.
It came from building something real and hitting real walls.

If you're reading this as a recruiter: I don't just know these technologies. I know
*why* architectural decisions get made, when to change them, and how to execute
that change cleanly. The git history on this repo shows the full arc.

If you're reading this as a fellow dev: the migration from GetX to BLoC mid-project
felt terrifying before I started and obvious in retrospect. Do it when the codebase
tells you to. It will tell you.

And to future me: remember when you thought GetX was the final form? Look how far
you've come. Keep building. 💪

---

*Built with ❤️, late nights ☕, a Redis cache that hit 80% of the time 🚀,
and an LRU cache key that still makes me happy every time I see that ⚡ badge*

---

## 🤖 Credits

**Claude (Anthropic)** — primary partner throughout. Architecture, debugging,
BLoC migration strategy, Redis caching design, Kafka patterns, GraphQL resolvers,
MongoDB schema, and explaining why the Emitter scope doesn't survive a Timer
callback approximately three times until it clicked.

**Gemini (Google)** — the LLM that runs *inside* the system as a runtime.
Also useful for second opinions during development.

**Perplexity** — research and documentation. Honest footnote: a significant
portion of Perplexity's answers during this project were powered by Claude's
model anyway. The line blurs.

**ChatGPT (OpenAI)** — alternative perspectives and debugging in early stages.

**GitHub Copilot** — used briefly at the beginning. Not great for architectural
work at the time, genuinely unhelpful more than once, but it showed up. That counts.
I hear it's much better now. I moved on before finding out.

*You all turned midnight debugging sessions into learning experiences.
Some of you more than others, but everyone gets a medal. 🥇*
