package com.example.dashboard.kafka;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

@Service
public class KafkaConsumerService {

    private static final Logger logger = LoggerFactory.getLogger(KafkaConsumerService.class);

    /**
     * This method listens to the "posts" Kafka topic.
     * Whenever a message is produced to that topic, this method is automatically called.
     * @param message The content of the Kafka message, which is the JSON string of our Post object.
     */
    @KafkaListener(topics = "posts", groupId = "portfolio-group") // Using a descriptive group ID
    public void consumePost(String message) {
        // This is for the time being to prove that Kafka consumer received the message
        logger.info("✅ Kafka Consumer received message from 'posts' topic: {}", message);

        // Pending to actually save the post to the database
        // 1. Parse the JSON message string into a Post object.
        // 2. Save that Post object to the database.
    }
}

