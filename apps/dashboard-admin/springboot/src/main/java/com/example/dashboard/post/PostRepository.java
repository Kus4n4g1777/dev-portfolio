package com.example.dashboard.post;

import com.example.dashboard.post.Post;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import org.springframework.stereotype.Repository;

@Repository
public interface PostRepository extends JpaRepository<Post, Long> {
    // Opcional: métodos de búsqueda rápida
    List<Post> findByAuthor(String author);
}
