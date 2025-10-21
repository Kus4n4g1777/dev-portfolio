package com.example.dashboard.post;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.concurrent.atomic.AtomicLong;

@RestController
@RequestMapping("/api/posts")
public class PostController {

    private static final Logger logger = LoggerFactory.getLogger(PostController.class);
    private final AtomicLong counter = new AtomicLong();

    @Autowired
    private KafkaTemplate<String, Post> kafkaTemplate;

    // This is the correct topic name that matches our consumer and topic config
    private static final String KAFKA_TOPIC = "posts";

    @PostMapping
    public ResponseEntity<Post> createPost(@RequestBody Post post, Authentication authentication) {
        // Get the real username from the validated JWT provided by Spring Security
        String username = authentication.getName();

        // Populate the post object with server-side data
        post.setAuthor(username);
        post.setCreatedAt(LocalDateTime.now());
        post.setId(counter.incrementAndGet()); // Set a temporary ID for the response

        try {
            // Send the complete post object to the correct Kafka topic
            kafkaTemplate.send(KAFKA_TOPIC, post);
            logger.info("✅ Sent post to Kafka: {}", post.getTitle());
            return ResponseEntity.ok(post);

        } catch (Exception e) {
            logger.error("❌ Error sending post to Kafka", e);
            // Return a server error if Kafka is down
            return ResponseEntity.status(500).build();
        }
    }
}