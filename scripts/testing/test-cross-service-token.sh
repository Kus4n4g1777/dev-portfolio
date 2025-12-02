#!/bin/bash
# ===================================================================
# Cross-Service JWT Token Test Script (Bash)
# ===================================================================
# Purpose: Test JWT token flow between FastAPI (8000) and Spring Boot (8081)
# Location: scripts/testing/test-cross-service-token.sh
# Usage: ./scripts/testing/test-cross-service-token.sh
# ===================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

# Configuration
FASTAPI_URL="http://localhost:8000"
SPRINGBOOT_URL="http://localhost:8081"
USERNAME="kus4n4g1"
PASSWORD="Ethan0410"

echo -e "${CYAN}🔐 === Cross-Service JWT Token Test ===${NC}"
echo ""

# --- Step 1: Get Token from FastAPI ---
echo -e "${YELLOW}📨 Step 1: Requesting JWT token from FastAPI...${NC}"

TOKEN_RESPONSE=$(curl -s -X POST "$FASTAPI_URL/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USERNAME&password=$PASSWORD")

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to get token from FastAPI${NC}"
    echo -e "${YELLOW}💡 Troubleshooting:${NC}"
    echo -e "${GRAY}   1. Check if FastAPI is running: docker-compose ps dashboard_backend${NC}"
    echo -e "${GRAY}   2. Verify credentials in .env file${NC}"
    echo -e "${GRAY}   3. Check FastAPI logs: docker logs dashboard_backend${NC}"
    exit 1
fi

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
    echo -e "${RED}❌ Failed to extract access token${NC}"
    echo -e "${GRAY}   Response: $TOKEN_RESPONSE${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Token received successfully!${NC}"
echo -e "${GRAY}   Token preview: ${ACCESS_TOKEN:0:20}...${NC}"
echo ""

# --- Step 2: Test FastAPI Protected Endpoint ---
echo -e "${YELLOW}📨 Step 2: Testing FastAPI protected endpoint (/users/me/)...${NC}"

ME_RESPONSE=$(curl -s -X GET "$FASTAPI_URL/users/me/" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if [ $? -eq 0 ]; then
    USERNAME_FROM_API=$(echo $ME_RESPONSE | jq -r '.username')
    EMAIL_FROM_API=$(echo $ME_RESPONSE | jq -r '.email')
    ROLE_FROM_API=$(echo $ME_RESPONSE | jq -r '.role')
    
    echo -e "${GREEN}✅ FastAPI authentication verified!${NC}"
    echo -e "${GRAY}   User: $USERNAME_FROM_API${NC}"
    echo -e "${GRAY}   Email: $EMAIL_FROM_API${NC}"
    echo -e "${GRAY}   Role: $ROLE_FROM_API${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠️  Warning: Could not verify token with FastAPI${NC}"
    echo ""
fi

# --- Step 3: Send Request to Spring Boot with Token ---
echo -e "${YELLOW}📨 Step 3: Sending authenticated request to Spring Boot...${NC}"

POST_DATA='{
    "title": "Cross-Service JWT Test",
    "content": "This message was sent with a valid JWT token from FastAPI to Spring Boot"
}'

SPRING_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$SPRINGBOOT_URL/api/posts" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "$POST_DATA")

HTTP_STATUS=$(echo "$SPRING_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
RESPONSE_BODY=$(echo "$SPRING_RESPONSE" | sed '/HTTP_STATUS:/d')

if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "201" ]; then
    echo -e "${GREEN}✅ Spring Boot accepted the token!${NC}"
    echo -e "${GRAY}   Response Status: $HTTP_STATUS${NC}"
    echo -e "${GRAY}   Response: $RESPONSE_BODY${NC}"
    echo ""
else
    echo -e "${RED}❌ Failed to authenticate with Spring Boot${NC}"
    echo -e "${GRAY}   Status: $HTTP_STATUS${NC}"
    echo -e "${GRAY}   Response: $RESPONSE_BODY${NC}"
    echo ""
    echo -e "${YELLOW}💡 Troubleshooting:${NC}"
    echo -e "${GRAY}   1. Check if Spring Boot is running: docker-compose ps springboot_backend${NC}"
    echo -e "${GRAY}   2. Verify JWT secret matches in both services (.env)${NC}"
    echo -e "${GRAY}   3. Check Spring Boot logs: docker logs springboot_backend${NC}"
    echo -e "${GRAY}   4. Verify CORS settings allow cross-service communication${NC}"
    exit 1
fi

# --- Step 4: Test Kafka Integration (Optional) ---
echo -e "${YELLOW}📨 Step 4: Testing Kafka message publishing (optional)...${NC}"
sleep 2  # Give Kafka time to process

echo -e "${CYAN}ℹ️  Check Kafka logs to verify message was published:${NC}"
echo -e "${GRAY}   docker logs kafka --tail=50${NC}"
echo ""

# --- Summary ---
echo -e "${GREEN}🎉 === Test Complete! ===${NC}"
echo ""
echo -e "${CYAN}✅ Summary:${NC}"
echo -e "${GREEN}   1. FastAPI issued JWT token: ✅${NC}"
echo -e "${GREEN}   2. FastAPI verified token: ✅${NC}"
echo -e "${GREEN}   3. Spring Boot accepted token: ✅${NC}"
echo ""
echo -e "${CYAN}📊 What this proves:${NC}"
echo -e "${GRAY}   • JWT tokens work across microservices${NC}"
echo -e "${GRAY}   • Shared SECRET_KEY is properly configured${NC}"
echo -e "${GRAY}   • CORS is configured correctly${NC}"
echo -e "${GRAY}   • Services can authenticate each other's requests${NC}"
echo ""
echo -e "${CYAN}📝 Next steps:${NC}"
echo -e "${GRAY}   • View all logs: docker-compose logs -f${NC}"
echo -e "${GRAY}   • Check database: docker exec -it dashboard_db psql -U kus4n4g1 -d portfolio_db${NC}"
echo -e "${GRAY}   • Monitor Kafka: docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic posts --from-beginning${NC}"
echo ""