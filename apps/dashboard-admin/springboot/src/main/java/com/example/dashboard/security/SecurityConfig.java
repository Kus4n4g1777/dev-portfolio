package com.example.dashboard.security;

import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

/**
 * Security configuration for the application.
 *
 * Responsibilities:
 * - Configure which endpoints require authentication
 * - Configure the JWT authentication filter
 * - Disable CSRF (not needed for stateless APIs)
 * - Configure stateless sessions
 */
@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtAuthenticationFilter jwtAuthenticationFilter;

    /**
     * Configures the security filter chain.
     *
     * Evaluation order (important):
     * 1. Rules are evaluated IN THE ORDER they appear
     * 2. The first matching rule is applied (others are ignored)
     * 3. That's why the most specific rules are placed FIRST
     *
     * @param http HttpSecurity builder
     * @return Configured SecurityFilterChain
     */
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                // Disable CSRF (Cross-Site Request Forgery)
                // Not needed because:
                // - We use JWT (stateless)
                // - We do not use session cookies
                // - The token is sent in the Authorization header
                .csrf(csrf -> csrf.disable())

                // Configure endpoint authorization
                .authorizeHttpRequests(auth -> auth
                        // ========== PUBLIC (no authentication required) ==========

                        // Health check (for Kubernetes, Docker, monitoring)
                        .requestMatchers("/actuator/health", "/actuator/prometheus").permitAll()

                        // GET posts (public read access)
                        .requestMatchers(HttpMethod.GET, "/api/posts").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/posts/by-author/**").permitAll()

                        // ========== PROTECTED (JWT required) ==========

                        // Create post (requires authentication)
                        .requestMatchers(HttpMethod.POST, "/api/posts").authenticated()

                        // My posts (requires authentication)
                        .requestMatchers("/api/posts/my-posts").authenticated()

                        // Any other endpoint under /api/posts/** requires authentication
                        .requestMatchers("/api/posts/**").authenticated()

                        // ========== DEFAULT ==========

                        // Any other unspecified endpoint: allow
                        // (You could change to .authenticated() to be more restrictive)
                        .anyRequest().permitAll()
                )

                // Stateless sessions (we do not store state on the server)
                // Every request must include its JWT
                .sessionManagement(session -> session
                        .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                );

        // Add our JWT filter BEFORE Spring's authentication filter
        // This allows Spring to process the JWT before checking permissions
        http.addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    /**
     * AuthenticationManager bean (useful if you want to authenticate manually).
     *
     * In your case you are NOT using it because authentication is handled by FastAPI.
     * But we keep it in case you add login through Spring Boot in the future.
     */
    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration config) throws Exception {
        return config.getAuthenticationManager();
    }
}
