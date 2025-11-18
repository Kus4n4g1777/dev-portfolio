package com.example.dashboard.post;

import com.example.dashboard.kafka.PostProducer;
import com.example.dashboard.post.dto.PostRequestDTO;
import com.example.dashboard.post.dto.PostResponseDTO;
import com.example.dashboard.post.mapper.PostMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * Service layer for Post business logic.
 *
 * Responsibilities:
 * - Business validation
 * - Coordination between Repository, Kafka, and other dependencies
 * - Transaction management
 *
 * Should NOT:
 * - Handle HTTP (that's the Controller's job)
 * - Know database details (that's the Repository's job)
 */
@Service
@Transactional           // ALL operations are transactional by default
@RequiredArgsConstructor // Lombok generates constructor with all 'final' fields
@Slf4j                   // Lombok generates: private static final Logger log = ...
public class PostService {

    // Constructor injection (final + @RequiredArgsConstructor)
    private final PostRepository postRepository;
    private final PostProducer postProducer;
    private final PostMapper postMapper;

    /**
     * Creates a new post.
     *
     * Flow:
     * 1. Convert DTO → Entity (using mapper)
     * 2. Set author from JWT (business logic)
     * 3. Save to DB (transactional)
     * 4. Publish event to Kafka (asynchronous, best effort)
     * 5. Convert Entity → Response DTO (using mapper)
     * 6. Return DTO to Controller
     *
     * @param request DTO with data from the client
     * @param username Username extracted from JWT (comes from Controller)
     * @return Response DTO with the created post (includes id, createdAt)
     */
    public PostResponseDTO createPost(PostRequestDTO request, String username) {
        log.debug("Creating post with title: '{}' for user: '{}'", request.getTitle(), username);

        // 1. Convert DTO → Entity
        Post post = postMapper.toEntity(request);

        // 2. Set author (business logic - NOT from client)
        post.setAuthor(username);

        // 3. Save to DB (JPA generates ID and sets createdAt here)
        Post savedPost = postRepository.save(post);
        log.info("Post created successfully with ID: {}", savedPost.getId());

        // 4. Publish to Kafka (asynchronous, should not fail the request)
        try {
            postProducer.sendPost(savedPost);
            log.debug("Post published to Kafka topic");
        } catch (Exception e) {
            // Log error but DO NOT propagate the exception
            // Post is already saved in DB, that's the source of truth
            log.error("Failed to publish post to Kafka: {}", e.getMessage(), e);
            // TODO: Implement retry or DLQ (Dead Letter Queue) for Kafka failures
        }

        // 5. Convert Entity → Response DTO
        return postMapper.toResponseDTO(savedPost);
    }

    /**
     * Retrieves all posts.
     *
     * @Transactional(readOnly = true) optimizes the transaction for read-only:
     * - Hibernate does not do automatic flush()
     * - Some DBs optimize read-only queries
     * - More resource-efficient
     *
     * @return List of posts as Response DTOs
     */
    @Transactional(readOnly = true)
    public List<PostResponseDTO> getAllPosts() {
        log.debug("Fetching all posts");

        List<Post> posts = postRepository.findAll();
        log.debug("Found {} posts", posts.size());

        return postMapper.toResponseDTOList(posts);
    }

    /**
     * Retrieves all posts by a specific author.
     *
     * @param author Username of the author
     * @return List of posts by the author as Response DTOs
     */
    @Transactional(readOnly = true)
    public List<PostResponseDTO> getPostsByAuthor(String author) {
        log.debug("Fetching posts for author: '{}'", author);

        List<Post> posts = postRepository.findByAuthor(author);
        log.debug("Found {} posts for author '{}'", posts.size(), author);

        return postMapper.toResponseDTOList(posts);
    }
}