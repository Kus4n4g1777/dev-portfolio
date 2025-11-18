package com.example.dashboard.controller;

import com.example.dashboard.post.PostService;
import com.example.dashboard.post.dto.PostRequestDTO;
import com.example.dashboard.post.dto.PostResponseDTO;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * REST Controller for Posts.
 *
 * Responsibilities:
 * - Receive HTTP requests
 * - Validate input format (@Valid)
 * - Extract authentication information (JWT)
 * - Delegate business logic to the Service
 * - Return HTTP responses with appropriate status codes
 *
 * It should NOT:
 * - Contain business logic (that's for the Service)
 * - Access the Repository directly
 * - Handle Kafka directly
 * - Convert DTO ↔ Entity (Service uses the Mapper for that)
 *
 * @RestController = @Controller + @ResponseBody on all methods
 * @RequestMapping("/api/posts") = Prefix for all routes
 */
@RestController
@RequestMapping("/api/posts")
@RequiredArgsConstructor
@Slf4j
public class PostController {

    private final PostService postService;

    /**
     * Creates a new post.
     *
     * Endpoint: POST /api/posts
     *
     * Request Body:
     * {
     *   "title": "My Post Title",
     *   "content": "Post content here..."
     * }
     *
     * Response (201 Created):
     * {
     *   "id": 1,
     *   "title": "My Post Title",
     *   "content": "Post content here...",
     *   "author": "john_doe",
     *   "createdAt": "2024-11-17T20:30:00"
     * }
     *
     * @param request DTO with title and content (validated with @Valid)
     * @param authentication Object automatically injected by Spring Security (from JWT)
     * @return Response with the created post and status 201
     *
     * @Valid:
     * - Spring automatically validates the DTO before entering the method
     * - If validation fails (@NotBlank, @Size), 400 Bad Request is returned automatically
     * - Errors are serialized as JSON using your custom messages
     *
     * Authentication:
     * - Injected automatically by Spring Security
     * - Contains the validated JWT information
     * - authentication.getName() returns the username (JWT subject)
     */
    @PostMapping
    public ResponseEntity<PostResponseDTO> createPost(
            @RequestBody @Valid PostRequestDTO request,
            Authentication authentication) {

        // Log the request (useful for debugging)
        log.info("POST /api/posts - User: {} - Title: {}",
                authentication.getName(), request.getTitle());

        // Delegate to the Service
        PostResponseDTO response = postService.createPost(request, authentication.getName());

        // Return 201 Created (not 200 OK) because a resource was created
        return ResponseEntity
                .status(HttpStatus.CREATED)  // 201
                .body(response);
    }

    /**
     * Retrieves all posts.
     *
     * Endpoint: GET /api/posts
     *
     * Response (200 OK):
     * [
     *   { "id": 1, "title": "...", ... },
     *   { "id": 2, "title": "...", ... }
     * ]
     *
     * This endpoint does NOT require authentication in your current config.
     * If you want to secure it, modify SecurityConfig.
     *
     * @return List of all posts
     */
    @GetMapping
    public ResponseEntity<List<PostResponseDTO>> getAllPosts() {
        log.info("GET /api/posts - Fetching all posts");

        List<PostResponseDTO> posts = postService.getAllPosts();

        log.debug("Returning {} posts", posts.size());

        return ResponseEntity.ok(posts);  // 200 OK
    }

    /**
     * Retrieves posts created by the authenticated user (my posts).
     *
     * Endpoint: GET /api/posts/my-posts
     *
     * Response (200 OK):
     * [
     *   { "id": 1, "title": "My first post", "author": "john_doe", ... },
     *   { "id": 3, "title": "My second post", "author": "john_doe", ... }
     * ]
     *
     * This endpoint DOES require authentication (needs JWT).
     *
     * @param authentication Injected by Spring Security
     * @return List of posts by the authenticated user
     */
    @GetMapping("/my-posts")
    public ResponseEntity<List<PostResponseDTO>> getMyPosts(Authentication authentication) {
        String username = authentication.getName();

        log.info("GET /api/posts/my-posts - User: {}", username);

        List<PostResponseDTO> posts = postService.getPostsByAuthor(username);

        log.debug("Returning {} posts for user {}", posts.size(), username);

        return ResponseEntity.ok(posts);  // 200 OK
    }

    /**
     * Retrieves posts by a specific author (public endpoint).
     *
     * Endpoint: GET /api/posts/by-author/{author}
     * Example: GET /api/posts/by-author/john_doe
     *
     * Response (200 OK):
     * [
     *   { "id": 1, "title": "...", "author": "john_doe", ... }
     * ]
     *
     * @param author Username of the author (path variable)
     * @return List of posts by the given author
     *
     * @PathVariable:
     * - Extracts the value from the URL
     * - /by-author/{author} → the value inside {author} is injected into the parameter
     */
    @GetMapping("/by-author/{author}")
    public ResponseEntity<List<PostResponseDTO>> getPostsByAuthor(
            @PathVariable String author) {

        log.info("GET /api/posts/by-author/{} - Fetching posts", author);

        List<PostResponseDTO> posts = postService.getPostsByAuthor(author);

        log.debug("Returning {} posts for author {}", posts.size(), author);

        return ResponseEntity.ok(posts);  // 200 OK
    }
}
