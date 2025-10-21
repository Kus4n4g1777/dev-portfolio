package com.example.dashboard.config;

import org.apache.kafka.clients.admin.NewTopic;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.TopicBuilder;

@Configuration
public class KafkaTopicConfig {

    /**
     * This Bean ensures that the "posts" topic is created on the Kafka broker
     * when the Spring application starts. This is the professional way to manage
     * topics and avoids race conditions with auto-creation.
     */
    @Bean
    public NewTopic postsTopic() {
        return TopicBuilder.name("posts")
                .partitions(1)      // For a single broker setup
                .replicas(1)        // For a single broker setup
                .build();
    }
}