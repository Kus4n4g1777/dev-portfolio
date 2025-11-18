package com.example.dashboard.post.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO to create a post.
 * This is the object that receives the controller from the client.
 *
 * int only includes the fields that the client has to deliver.
 * It doesn't include: id(db generated), author(from JWT), createdAt(from server)
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PostRequestDTO {

    /**
     * Post title.
     * Validations:
     * - Mustn't be empty (blank = "", "  ", null)
     * - 200 char max
     */
    @NotBlank(message = "Title is required")
    @Size(max = 200, message = "Title must not exceed 200 characters")
    private String title;

    /**
     * Post content.
     * Validations:
     * - Mustn't be empty
     * - 5000 char max (adjust according to need)
     */
    @NotBlank(message = "Content is required")
    @Size(max = 5000, message = "Content must not exceed 5000 characters")
    private String content;
}
