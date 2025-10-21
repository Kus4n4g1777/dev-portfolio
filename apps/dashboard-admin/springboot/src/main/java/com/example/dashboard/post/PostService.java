package com.example.dashboard.post;

import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.context.SecurityContextHolder;
import com.example.dashboard.kafka.PostProducer;

@Service
public class PostService {

    private final PostRepository postRepository;
    private final PostProducer postProducer; // ✅ nuevo productor Kafka

    @Autowired
    public PostService(PostRepository postRepository, PostProducer postProducer) {
        this.postRepository = postRepository;
        this.postProducer = postProducer;
    }

    public Post createPost(Post post) {
        // Obtiene el nombre del usuario autenticado
        String username = (String) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        post.setAuthor(username);

        // Guarda el post en la base de datos
        Post savedPost = postRepository.save(post);

        // Envía el post al tópico Kafka
        postProducer.sendPost(savedPost);

        return savedPost;
    }

    public List<Post> getAllPosts() {
        return postRepository.findAll();
    }

    public List<Post> getPostsByAuthor(String author) {
        return postRepository.findByAuthor(author);
    }
}
