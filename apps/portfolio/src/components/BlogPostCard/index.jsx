import React from 'react';
import './BlogPostCard.css';

const BlogPostCard = ({ post }) => {
  return (
    <div className="blog-post-card">
      <h3>{post.title}</h3>
      <p>{post.content}</p>
    </div>
  );
};

export default BlogPostCard;
