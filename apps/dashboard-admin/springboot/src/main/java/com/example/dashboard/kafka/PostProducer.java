package com.example.dashboard.kafka;

import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;
import com.example.dashboard.post.Post;

@Service
public class PostProducer {

    private final KafkaTemplate<String, Post> kafkaTemplate;

    public PostProducer(KafkaTemplate<String, Post> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    public void sendPost(Post post) {
        kafkaTemplate.send("posts-topic", post);
        System.out.println("✅ Sent post to Kafka: " + post.getTitle());
    }
}
