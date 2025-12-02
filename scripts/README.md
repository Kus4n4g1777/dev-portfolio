# Scripts Directory

Centralized scripts for managing the dev-portfolio project infrastructure.

## Directory Structure

```
scripts/
├── docker/          # Docker container management
├── kafka/           # Kafka/Zookeeper lifecycle scripts
├── testing/         # Cross-service integration tests
├── db/              # Database utilities
└── README.md        # This file
```

---

## 📁 Available Scripts

### Kafka Management (`scripts/kafka/`)

#### `fix-kafka.sh`
**Purpose**: Fix common Kafka startup issues and restart containers in correct order

**Usage**:
```bash
./scripts/kafka/fix-kafka.sh
```

**What it does**:
1. Stops all containers gracefully
2. Removes corrupted Kafka volumes
3. Starts Zookeeper first (required dependency)
4. Waits for Zookeeper to be healthy
5. Starts Kafka
6. Starts remaining services
7. Shows container status and health checks

**When to use**:
- Kafka container exits with error code 1
- "dependency failed to start" errors
- After changing Kafka configuration
- When Zookeeper connection fails

---

### Testing (`scripts/testing/`)

#### `test-cross-service-token.ps1` (PowerShell)
#### `test-cross-service-token.sh` (Bash)

**Purpose**: Test JWT authentication flow between FastAPI and Spring Boot services

**Usage**:
```powershell
# PowerShell (Windows)
.\scripts\testing\test-cross-service-token.ps1

# Bash (Linux/Mac)
./scripts/testing/test-cross-service-token.sh
```

**What it tests**:
1. ✅ FastAPI issues valid JWT token
2. ✅ FastAPI verifies its own tokens
3. ✅ Spring Boot accepts FastAPI tokens
4. ✅ Cross-service authentication works
5. ℹ️  Optional: Kafka message publishing

**Prerequisites**:
- All containers running: `docker-compose up -d`
- User exists in database (username: kus4n4g1)
- SECRET_KEY matches in both services

**Troubleshooting**:
If test fails, check:
1. Container status: `docker-compose ps`
2. Service logs: `docker logs <service_name>`
3. SECRET_KEY in `.env` file
4. CORS configuration

---

## 🚀 Quick Start

### First Time Setup
```bash
# 1. Make scripts executable
chmod +x scripts/**/*.sh

# 2. Start all services
docker-compose up -d

# 3. If Kafka fails, run fix script
./scripts/kafka/fix-kafka.sh

# 4. Test cross-service authentication
./scripts/testing/test-cross-service-token.sh
```

### Common Workflows

**Restart everything cleanly**:
```bash
docker-compose down
docker-compose up -d
```

**Fix Kafka issues**:
```bash
./scripts/kafka/fix-kafka.sh
```

**Test authentication after changes**:
```bash
./scripts/testing/test-cross-service-token.sh
```

**View logs**:
```bash
# All services
docker-compose logs -f

# Specific service
docker logs -f kafka
docker logs -f dashboard_backend
docker logs -f springboot_backend
```

---

## 📝 Best Practices

### When to Use These Scripts

1. **Use `fix-kafka.sh`**:
   - Every time Kafka fails to start
   - After modifying `docker-compose.yml` Kafka config
   - When getting "EndOfStreamException" errors
   - After system restart

2. **Use `test-cross-service-token.sh`**:
   - After changing JWT configuration
   - When debugging authentication issues
   - Before deploying to production
   - As part of CI/CD pipeline

### Script Organization Rules

- **docker/**: Only Docker-specific operations (build, restart, cleanup)
- **kafka/**: Only Kafka/Zookeeper lifecycle management
- **testing/**: Only integration tests between services
- **db/**: Only database operations (migrations, backups, seeds)

**DO NOT**:
- Put application logic in scripts
- Hardcode sensitive data (use .env)
- Create service-specific scripts here (use apps/<service>/scripts/)

---

## 🔧 Adding New Scripts

### Template for New Script

```bash
#!/bin/bash
# ===================================================================
# Script Name
# ===================================================================
# Purpose: Brief description
# Location: scripts/<category>/<script-name>.sh
# Usage: ./scripts/<category>/<script-name>.sh
# ===================================================================

set -e  # Exit on error

# Your script here
```

### Checklist
- [ ] Add shebang line (`#!/bin/bash` or `#!/usr/bin/env pwsh`)
- [ ] Include header comment block
- [ ] Use `set -e` for error handling
- [ ] Add colored output for readability
- [ ] Include usage instructions
- [ ] Document in this README
- [ ] Make executable: `chmod +x script.sh`
- [ ] Test on clean system

---

## 🐛 Troubleshooting

### Common Issues

**"Permission denied" when running script**:
```bash
chmod +x scripts/kafka/fix-kafka.sh
./scripts/kafka/fix-kafka.sh
```

**Kafka keeps failing**:
1. Check disk space: `docker system df`
2. Check logs: `docker logs kafka --tail=100`
3. Verify Zookeeper: `docker logs zookeeper --tail=100`
4. Check ports: `netstat -an | grep 9092`

**Token test fails**:
1. Verify containers: `docker-compose ps`
2. Check SECRET_KEY matches in all services
3. View FastAPI logs: `docker logs dashboard_backend`
4. View Spring Boot logs: `docker logs springboot_backend`

**Scripts not found**:
```bash
# Run from project root
cd /path/to/dev-portfolio
./scripts/kafka/fix-kafka.sh
```

---

## 📚 Related Documentation

- [Docker Compose Reference](../docker-compose.yml)
- [FastAPI Backend](../apps/dashboard-admin/backend/README.md)
- [Spring Boot Backend](../apps/dashboard-admin/springboot/README.md)
- [Kafka Configuration](../docker-compose.yml#kafka)

---

## 🎯 Interview Tips

These scripts demonstrate:
- **Systems thinking**: Organized, reusable infrastructure management
- **Best practices**: Error handling, logging, documentation
- **Real-world skills**: Container orchestration, service debugging
- **Team readiness**: Scripts teammates can use without asking you

**Story to tell**:
> "I created centralized scripts for common operations. The Kafka fix script 
> handles the startup sequence correctly - Zookeeper first, then Kafka after 
> health check. The token test verifies JWT flow across microservices. This 
> saved the team hours of debugging time and serves as living documentation."

---

## 📧 Questions?

Check the main [README](../README.md) or service-specific documentation.
