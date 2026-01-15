FROM dart:stable AS build

WORKDIR /app

# Copy dependency files
COPY pubspec.yaml pubspec.lock ./
RUN dart pub get

# Copy all source (routes/)
COPY . .

# Install dart_frog CLI
RUN dart pub global activate dart_frog_cli

# Add dart pub global bin to PATH
ENV PATH="${PATH}:/root/.pub-cache/bin"

# Build dart_frog (generates complete server in build/)
RUN dart_frog build

# Runtime stage
FROM dart:stable

WORKDIR /app

# Copy the generated build
COPY --from=build /app/build /app

# Install dependencies for the generated server
RUN cd /app && dart pub get

EXPOSE 8080

# Run the generated server directly (no compile needed)
CMD ["dart", "bin/server.dart"]
