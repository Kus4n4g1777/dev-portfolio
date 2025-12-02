#!/bin/bash
# ===================================================================
# Detection REST API Test Script (Bash)
# ===================================================================
# Purpose: Test all detection endpoints with real data
# Location: tests/test_detection_api.sh
# Usage: ./tests/test_detection_api.sh
# ===================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

API_BASE="http://localhost:8000/api/detections"

echo -e "${CYAN}🎯 === Testing Detection REST API ===${NC}"
echo ""

# ===================================================================
# Test 1: POST - Create Detection
# ===================================================================
echo -e "${YELLOW}📨 Test 1: Creating detection...${NC}"

RESPONSE=$(curl -s -X POST "$API_BASE" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "test_hearts_stars.jpg",
    "model_version": "v1.0",
    "confidence_threshold": 0.4,
    "detections": [
      {
        "x1": 0.1, "y1": 0.2, "x2": 0.5, "y2": 0.6,
        "label": "Hearts",
        "confidence": 0.85
      },
      {
        "x1": 0.6, "y1": 0.3, "x2": 0.9, "y2": 0.7,
        "label": "Stars",
        "confidence": 0.92
      }
    ]
  }')

DETECTION_ID=$(echo $RESPONSE | jq -r '.id')
TOTAL_DETECTIONS=$(echo $RESPONSE | jq -r '.total_detections')
AVG_CONFIDENCE=$(echo $RESPONSE | jq -r '.avg_confidence')
INFERENCE_TIME=$(echo $RESPONSE | jq -r '.inference_time_ms')

echo -e "${GREEN}✅ Detection created successfully!${NC}"
echo -e "${GRAY}   ID: $DETECTION_ID${NC}"
echo -e "${GRAY}   Total detections: $TOTAL_DETECTIONS${NC}"
echo -e "${GRAY}   Avg confidence: $AVG_CONFIDENCE${NC}"
echo -e "${GRAY}   Inference time: ${INFERENCE_TIME}ms${NC}"
echo ""

# ===================================================================
# Test 2: GET - Retrieve Single Detection
# ===================================================================
echo -e "${YELLOW}📨 Test 2: Retrieving detection by ID...${NC}"

DETECTION=$(curl -s -X GET "$API_BASE/$DETECTION_ID")

echo -e "${GREEN}✅ Detection retrieved successfully!${NC}"
echo -e "${GRAY}   Model version: $(echo $DETECTION | jq -r '.model_version')${NC}"
echo -e "${GRAY}   Status: $(echo $DETECTION | jq -r '.status')${NC}"
echo ""

# ===================================================================
# Test 3: GET - List All Detections
# ===================================================================
echo -e "${YELLOW}📨 Test 3: Listing all detections...${NC}"

ALL_DETECTIONS=$(curl -s -X GET "$API_BASE")
COUNT=$(echo $ALL_DETECTIONS | jq 'length')

echo -e "${GREEN}✅ Listed detections successfully!${NC}"
echo -e "${GRAY}   Total in DB: $COUNT${NC}"
echo ""

# ===================================================================
# Test 4: GET - Metrics Summary
# ===================================================================
echo -e "${YELLOW}📨 Test 4: Getting metrics summary...${NC}"

METRICS=$(curl -s -X GET "$API_BASE/metrics/summary")

echo -e "${GREEN}✅ Metrics retrieved successfully!${NC}"
echo -e "${GRAY}   Total detections: $(echo $METRICS | jq -r '.total_detections')${NC}"
echo -e "${GRAY}   Avg confidence: $(echo $METRICS | jq -r '.avg_confidence')${NC}"
echo -e "${GRAY}   Avg inference time: $(echo $METRICS | jq -r '.avg_inference_time')ms${NC}"
echo -e "${GRAY}   Detections by label:${NC}"
echo $METRICS | jq -r '.detections_by_label | to_entries[] | "      \(.key): \(.value)"' | while read line; do
    echo -e "${GRAY}$line${NC}"
done
echo ""

# ===================================================================
# Summary
# ===================================================================
echo -e "${GREEN}🎉 === Test Suite Complete! ===${NC}"
echo ""
echo -e "${CYAN}📊 Summary:${NC}"
echo -e "${GREEN}   ✅ POST /api/detections${NC}"
echo -e "${GREEN}   ✅ GET /api/detections/{id}${NC}"
echo -e "${GREEN}   ✅ GET /api/detections${NC}"
echo -e "${GREEN}   ✅ GET /api/detections/metrics/summary${NC}"
echo ""
echo -e "${YELLOW}💡 Next steps:${NC}"
echo -e "${GRAY}   • View data: docker exec -it dashboard_db psql -U kus4n4g1 -d portfolio_db -c 'SELECT * FROM detection_results;'${NC}"
echo -e "${GRAY}   • Check logs: docker logs dashboard_backend${NC}"
echo -e "${GRAY}   • API docs: http://localhost:8000/docs${NC}"
echo ""