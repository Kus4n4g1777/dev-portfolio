# 🚀 Dev Portfolio — Distributed Systems Showcase

A production-grade polyglot microservices platform built to demonstrate
senior fullstack engineering capabilities across multiple technology stacks,
databases, communication patterns, and architectural styles.

> **Honest disclaimer:** This isn't a tutorial project I followed — it's a system
> I designed and built iteratively over several months, making real architectural
> decisions, hitting real walls, and evolving the stack as I learned what each
> tool was actually good at. The journey is documented in the Dev Journey section below.

---

## 🏗️ System Architecture

### Service Map (27 containers)

```
                        ┌─────────────────────────────────────┐
                        │         NGINX Reverse Proxy          │
                        │         :8080 (HTTP) / :443          │
                        └──────────────┬──────────────────────┘
                                       │
               ┌───────────────────────┼───────────────────────┐
               │                       │                       │
               ▼                       ▼                       ▼
   ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
   │  Angular Dashboard  │ │   React Portfolio   │ │  GraphQL Gateway    │
   │  dashboard_frontend │ │ portfolio_frontend  │ │    Apollo Server    │
   │      :4200          │ │      :3001          │ │      :4000          │
   └─────────────────────┘ └─────────────────────┘ └──────┬──────────────┘
                                                           │
                         ┌─────────────────────────────────┼──────────────────┐
                         │                                 │                  │
                         ▼                                 ▼                  ▼
             ┌─────────────────────┐         ┌────────────────────┐  ┌──────────────────┐
             │  FastAPI Backend    │         │  Spring Boot API   │  │ Express Analytics│
             │  Python / Uvicorn   │         │  Java / REST + JWT │  │  Node.js / KafkaJS│
             │      :8000          │         │      :8081         │  │      :3000        │
             └──────────┬──────────┘         └─────────┬──────────┘  └────────┬─────────┘
                        │                              │                       │
           ┌────────────┼────────────┐                 │                       │
           │            │            │                 │                       │
           ▼            ▼            ▼                 ▼                       ▼
    ┌────────────┐ ┌─────────┐ ┌──────────┐    ┌────────────┐          ┌────────────┐
    │ PostgreSQL │ │pgvector │ │  Oracle  │    │ PostgreSQL │          │  MongoDB   │
    │  (primary) │ │  (RAG)  │ │   XE 21  │    │  (shared)  │          │ (analytics)│
    │   :5432    │ │  :5433  │ │  :1521   │    │            │          │  :27017    │
    └────────────┘ └─────────┘ └──────────┘    └─────────┬──┘          └────────────┘
                                                          │
                                                          ▼
                                               ┌──────────────────┐
                                               │  Apache Kafka    │
                                               │  + Zookeeper     │
                                               │  :9092 / :2181   │
                                               └──────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                        LLM GATEWAY SUBSYSTEM

    ┌─────────────────────────────────────────────────────┐
    │              LLM Gateway (FastAPI)  :8002            │
    │                                                      │
    │   Redis LRU Cache → ~80% hit rate → ~0.03ms         │
    │        ↓ on miss                                     │
    │   ┌──────────┬──────────┬──────────┬─────────┐      │
    │   │  Gemini  │   Dart   │    Go    │  Ollama │      │
    │   │ 2.5 Flash│ Runtime  │ Runtime  │ (local) │      │
    │   │  :8002   │  :8090   │  :8091   │ :11434  │      │
    │   └──────────┴──────────┴──────────┴─────────┘      │
    │        ↓ publishes to Kafka                          │
    │   llm.inference.events → Express Analytics → MongoDB │
    └─────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Databases (5 different engines — polyglot persistence)

| Database | Engine | Port | Purpose |
|----------|--------|------|---------|
| `dashboard_db` | PostgreSQL 16 | 5432 | Primary — users, auth, detections |
| `vector_db` | pgvector/pg16 | 5433 | RAG embeddings (LLM semantic search) |
| `oracle-db` | Oracle XE 21 | 1521 | Enterprise DB demo |
| `mongodb` | MongoDB 7.0 | 27017 | LLM inference analytics (flexible schema) |
| Redis | (in-process LRU) | — | LLM Gateway cache (~80% hit rate) |

### Backend Services

| Service | Stack | Port | Responsibility |
|---------|-------|------|---------------|
| `dashboard_backend` | FastAPI / Python 3.11 | 8000 | Auth, user management, detection persistence |
| `springboot_backend` | Spring Boot 3 / Java 21 | 8081 | User CRUD, Kafka producer, JWT |
| `llm-gateway` | FastAPI / Python + aiokafka | 8002 | Multi-runtime LLM routing + Redis LRU cache |
| `express-analytics` | Express / Node.js 20 | 3000 | Kafka consumer → MongoDB + REST analytics API |
| `graphql-gateway` | Apollo Server / Node.js 20 | 4000 | Unified GraphQL API for all backends |

### LLM Runtimes

| Runtime | Stack | Port | Notes |
|---------|-------|------|-------|
| `dart-runtime` | Dart Frog | 8090 | Gemini via Dart SDK |
| `go-runtime` | Go 1.21 | 8091 | Gemini via Go HTTP client |
| `ollama` | Ollama | 11434 | Local LLM (llama3.2, no API cost) |

### Frontend

| App | Stack | Port | Purpose |
|-----|-------|------|---------|
| `dashboard_frontend` | Angular 17+ (standalone) | 4200 | Admin dashboard |
| `portfolio_frontend` | React + Vite | 3001 | Public portfolio / users view |

### Infrastructure

| Service | Purpose |
|---------|---------|
| Kafka + Zookeeper | Event streaming (inference events, detection logs) |
| NGINX | Reverse proxy, SSL termination |
| Docker Compose | 27-service orchestration |

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/Kus4n4g1777/dev-portfolio.git
cd dev-portfolio

# 2. Copy env
cp .env.example .env
# Edit .env with your values (see Environment Setup section)

# 3. Start everything
docker compose up -d --build

# 4. Verify all 27 containers are healthy
docker compose ps

# 5. Run DB migrations
docker compose run --rm dashboard_backend alembic upgrade head
```

### Service URLs

| URL | Service |
|-----|---------|
| http://localhost:4200 | Angular Dashboard |
| http://localhost:3001 | React Portfolio |
| http://localhost:4000 | GraphQL Gateway (Apollo Sandbox) |
| http://localhost:8000/docs | FastAPI Swagger |
| http://localhost:8081/actuator/health | Spring Boot health |
| http://localhost:8002/docs | LLM Gateway Swagger |
| http://localhost:3000/health | Express Analytics health |
| http://localhost:11434 | Ollama API |

---

## ⚙️ Environment Setup

```env
# PostgreSQL
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=portfolio_db
DB_HOST=dashboard_db

# Oracle
ORACLE_PASSWORD=your_oracle_password
ORACLE_XE_DB=XEPDB1

# MongoDB
MONGO_USER=admin
MONGO_PASSWORD=your_mongo_password
MONGO_DB=portfolio_analytics

# FastAPI
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:5432/${DB_NAME}
SECRET_KEY=change_me_32_chars_minimum
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM
GEMINI_API_KEY=your_gemini_api_key
JWT_SECRET=your_jwt_secret

# AWS (Lambda integration)
LAMBDA_URL=your_lambda_url
```

---

## 📡 Analytics Pipeline

One of the more interesting pieces of this system — a complete observability
pipeline for the LLM Gateway:

```
Flutter app → POST /buffer/add-detection (4 detections buffer)
                    ↓ buffer full → LLM call
              LLM Gateway generates response
                    ↓ fire-and-forget (asyncio.create_task)
              Kafka producer → llm.inference.events
                    ↓
              Express Analytics (KafkaJS consumer)
                    ↓
              MongoDB inference_logs collection
                    ↓
              REST endpoints (:3000/analytics/*)
                    ↓
              GraphQL Gateway (Apollo Server)
                    ↓
              Angular Dashboard
```

### Analytics Endpoints (Express → GraphQL)

```bash
# Via REST directly
GET /analytics/cache-hit-rate
GET /analytics/runtime-distribution
GET /analytics/latency-percentiles
GET /analytics/top-detections
GET /analytics/recent

# Via GraphQL
query {
  analyticsCacheHitRate { total cacheHits hitRate }
  analyticsRuntimeDistribution { runtime count avgLatencyMs }
  analyticsLatencyPercentiles { runtime p50 p95 p99 }
  analyticsTopDetections { label count avgConfidence }
}
```

### Why MongoDB for analytics and not PostgreSQL?

Each LLM runtime (Gemini, Ollama, Dart, Go, cache) returns slightly different
metadata. A cache hit has no `prompt_tokens`. Ollama has `model_name`.
Gemini has `safety_ratings`. PostgreSQL would need null columns or a JSONB
column for this variance. MongoDB's document model handles it natively —
no migrations, no null fields, clean aggregation pipelines.

This is the textbook case for a document store over relational: variable
schema per document type within the same collection.

---

## 🐳 Docker Cheat Sheet

```bash
# Start everything
docker compose up -d --build

# Rebuild a single service (fast iteration)
docker compose up -d --build express-analytics

# Follow logs for a specific service
docker compose logs express-analytics --follow

# Check all container health
docker compose ps

# Stop everything (keep volumes)
docker compose down

# Nuclear option (removes volumes too — data loss!)
docker compose down -v
docker system prune -a --volumes

# Enter a container
docker compose exec dashboard_backend bash
docker exec -it mongodb mongosh -u admin -p yourpassword --authenticationDatabase admin
```

---

## 🔧 PostgreSQL Reference

```bash
# Connect
docker exec -it dashboard_db psql -U $DB_USER -d $DB_NAME

# Useful commands
\dt                    # list tables
\d <table_name>        # describe table
\q                     # exit

# From host
docker compose exec db psql -U $DB_USER -d $DB_NAME -c "\dt"
```

---

## 📜 Alembic Migrations (FastAPI)

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "add detection tables"

# Apply
alembic upgrade head

# Rollback one
alembic downgrade -1

# Check current revision
alembic current
```

Migrations run automatically on container startup via `run.sh`.

---

## 🧪 Testing the Stack

```bash
# Test LLM Gateway buffer (fires Gemini on 4th detection)
for i in 1 2 3 4; do
  curl -s -X POST http://localhost:8002/buffer/add-detection \
    -H "Content-Type: application/json" \
    -d '{"detection": {"label": "heart", "confidence": 0.97, "bbox": [0.1, 0.2, 0.4, 0.5]}}' | jq .
  sleep 1
done

# Verify event landed in MongoDB
curl -s http://localhost:3000/analytics/recent | jq .

# Check cache hit rate
curl -s http://localhost:3000/analytics/cache-hit-rate | jq .

# Query via GraphQL
curl -s -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ analyticsCacheHitRate { total cacheHits hitRate } }"}' | jq .
```

---

## 🚧 Work in Progress

- [ ] Angular dashboard — analytics visualization components (Apollo Client setup pending)
- [ ] Flutter app — AI message panel display (emulator config for external VSCode)
- [ ] Django service — user management + Django Admin panel (planned addition)
- [ ] React portfolio — login → welcome page (content TBD)
- [ ] Refresh token implementation (FastAPI)
- [ ] On-device TFLite inference (Flutter)

---

## 🔥 Dev Journey — The Honest Version

*From a blank docker-compose to 27 containers. Nothing went smoothly. That's the point.*

### The original vision vs. reality

Started with a simple goal: FastAPI + PostgreSQL + Angular. Clean, simple, done.

Then I realized the system had no interesting story to tell. Every junior dev has
a CRUD app with a REST API. I wanted something that showed real architectural
thinking — systems that talk to each other, services that have distinct responsibilities,
tradeoffs that I could defend in an interview.

So I kept adding layers. And kept hitting walls.

### Kafka: "Future: Kafka Integration" → Kafka has been running for months

The original README had a whole section called "Future: Kafka Integration" with
a diagram showing how it *would* work someday. That section is gone now because
Kafka is no longer future — it's the backbone of the analytics pipeline.

The inference events from the LLM Gateway flow through Kafka, get consumed by
the Express Analytics service, and land in MongoDB. I built the thing I said I
would build. That felt good.

### The LLM Gateway: the most fun I've had engineering in years

Multi-runtime LLM routing with Redis LRU caching was not in the original plan.
It happened because I was exploring how to make the Flutter app feel more alive —
the AI commentary on detections was cool, but 3000ms per response killed the UX.

The insight: detection patterns repeat. If the model sees a heart 10 times in a
session, it doesn't need a fresh Gemini call each time. An LRU cache keyed on
detection context hit ~80% of the time, dropping average latency from ~3000ms
to ~300ms. That's the kind of optimization that comes from actually using the
system, not from reading about caching strategies.

The four runtimes (Python/Gemini, Dart, Go, Ollama) exist partly to demonstrate
polyglot architecture and partly because I was genuinely curious whether the
response quality varied. Spoiler: it does.

### MongoDB: right tool, right job

PostgreSQL is my default. But when I started designing the inference log schema,
I kept running into the same problem: each LLM runtime returns different metadata.
A cache hit has no `prompt_tokens`. Ollama has `model_name`. Gemini has
`safety_ratings`. In PostgreSQL I'd need nullable columns or a JSONB blob.

MongoDB's document model solved this cleanly. One collection, variable schema
per document, aggregation pipelines that read naturally. This was the first time
I genuinely reached for MongoDB because it was the right tool rather than because
someone told me to use it. That distinction matters.

### 5 databases, 1 lesson

PostgreSQL (primary), pgvector (RAG), Oracle XE (enterprise demo), MongoDB
(analytics), Redis (LRU cache in-process). Each one is here for a reason I
can defend:

- PostgreSQL: relational data with ACID requirements
- pgvector: semantic similarity search for RAG — needs vector operations
- Oracle: demonstrates I can work in enterprise environments (common in Mexico/LATAM)
- MongoDB: flexible schema for multi-runtime metadata (see above)
- Redis: sub-millisecond cache for LLM responses — latency matters here

The lesson: the question isn't "which database?" but "what are the access patterns,
consistency requirements, and schema stability for this specific data?"

### What's next

The Angular dashboard is mostly empty right now — boilerplate standalone components,
no Apollo Client, no real routes. That's the next big chunk of work: connecting the
GraphQL gateway to Angular with proper service injection, typed queries, and actual
UI for the analytics data that's been flowing into MongoDB.

After that: a Django service for user management + Django Admin (because FastAPI and
Django solve different problems, and a portfolio that only uses one Python web framework
is selling the language short).

---

## 📊 Interview-Ready Stories

### Story 1: The Redis LRU Cache

> "The LLM Gateway was generating 3000ms responses on every detection. I profiled
> the usage and noticed detection patterns repeat heavily — if you hold a heart in
> front of the camera, the model sees it dozens of times per session. I built an
> LRU cache keyed on detection context bucket (label + confidence tier). Cache hits
> respond in ~0.03ms. With ~80% hit rate, average latency dropped from ~3000ms to
> ~300ms. The Flutter client shows a ⚡ badge on cache hits — the user literally
> sees the performance difference in real time."

### Story 2: MongoDB for variable-schema analytics

> "I was designing the inference log schema and kept running into nullable column
> hell in PostgreSQL. Each runtime returns different metadata — cache hits have no
> prompt_tokens, Ollama has model_name, Gemini has safety_ratings. Instead of
> fighting the relational model, I moved inference logs to MongoDB. Document model,
> no migrations, native aggregation pipelines for the analytics endpoints.
> This was the first time I reached for MongoDB because it genuinely fit better,
> not because it was trendy."

### Story 3: Kafka as the decoupling layer

> "The LLM Gateway publishes inference events to Kafka using asyncio.create_task()
> — fire and forget. The Flutter client gets its response immediately; Kafka
> persistence happens in parallel. The Express Analytics service consumes those
> events independently. If analytics goes down, events queue in Kafka and
> replay when it comes back. The gateway has zero knowledge that analytics exists.
> That's the architectural benefit of Kafka beyond just 'async processing'."

### Story 4: Atomic transactions in PostgreSQL

> "The detection create endpoint writes to three tables simultaneously — parent
> detection result, metrics, and multiple bounding boxes. I use db.flush() to get
> the parent ID without committing, create all children with that ID, then commit
> everything atomically. On any error, db.rollback() prevents partial writes.
> A detection with metrics but no bounding boxes would be corrupt data — the
> transaction boundary prevents that state from ever existing."

---

## 🤝 Contributing

This is a portfolio project, but architectural suggestions are welcome.

---

## 👨‍💻 Author

**Sunny Orukwo Escalante** — Senior Fullstack/Backend Engineer

- GitHub: [@Kus4n4g1777](https://github.com/Kus4n4g1777)
- LinkedIn: [sunny-orukwo](https://www.linkedin.com/in/sunny-orukwo/)

---

## 🙏 Credits

This system was built with the help of several AI tools — each played a different role:

**Claude (Anthropic)** — primary architecture partner throughout the project.
System design, BLoC migration, LLM Gateway design, Redis caching strategy,
MongoDB schema decisions, Kafka producer patterns, GraphQL resolver structure.
The reason I understand why the Emitter scope doesn't survive a Timer callback.

**Gemini (Google)** — the LLM that actually runs inside the system as a runtime.
Also useful for quick lookups and second opinions during development.

**Perplexity** — research and documentation lookups. Honest footnote: a good
chunk of Perplexity's answers during this project were powered by Claude's model
anyway, so the line blurs a bit.

**ChatGPT (OpenAI)** — alternative perspectives and debugging in the early stages.

**GitHub Copilot** — used very briefly at the beginning. Genuinely not great at
the time for the kind of architectural work this project needed, but it helped
where it could. Improved a lot since then apparently, but I'd already moved on.

---

## 📖 Want the full story?

The battles, the bugs, the "why won't these bounding boxes align" at 2am,
and the honest account of every architectural decision that didn't work the
first time — all documented in [DEV_JOURNEY.md](./DEV_JOURNEY.md).

Warning: it's long, opinionated, and contains real frustration. That's the point.

---

*Last updated: June 2026 — 27 containers healthy, analytics pipeline live end-to-end*
