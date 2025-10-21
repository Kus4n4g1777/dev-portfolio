# 1️⃣ Build stage
FROM maven:3.9.6-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

# 2️⃣ Runtime stage
FROM eclipse-temurin:21-jdk-alpine

# Install curl and bash
RUN apk add --no-cache curl bash

WORKDIR /app
COPY --from=build /app/target/*.jar app.jar

EXPOSE 8081

# Add health check script
RUN echo '#!/bin/sh' > /healthcheck.sh && \
    echo 'curl -f http://localhost:8081/actuator/health 2>/dev/null || exit 1' >> /healthcheck.sh && \
    chmod +x /healthcheck.sh

ENTRYPOINT ["java", "-jar", "app.jar"]