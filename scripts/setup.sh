#!/bin/bash
# ===================================================================
# Scripts Directory Setup - One-Time Initialization
# ===================================================================
# Purpose: Set up the scripts directory structure and make all scripts executable
# Location: scripts/setup.sh
# Usage: ./scripts/setup.sh (run once after cloning repo)
# ===================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🚀 === Scripts Directory Setup ===${NC}"
echo ""

# Step 1: Create directory structure
echo -e "${YELLOW}📁 Creating directory structure...${NC}"
mkdir -p scripts/{docker,kafka,testing,db}
echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# Step 2: Make all scripts executable
echo -e "${YELLOW}🔧 Making scripts executable...${NC}"
if [ -d "scripts" ]; then
    find scripts -type f -name "*.sh" -exec chmod +x {} \;
    echo -e "${GREEN}✅ All .sh scripts are now executable${NC}"
else
    echo -e "${YELLOW}⚠️  Scripts directory not found${NC}"
fi
echo ""

# Step 3: Verify structure
echo -e "${YELLOW}📊 Verifying structure...${NC}"
tree scripts/ -L 2 2>/dev/null || (
    echo "scripts/"
    ls -R scripts/
)
echo ""

# Step 4: List available scripts
echo -e "${CYAN}📜 Available scripts:${NC}"
echo ""
find scripts -type f -name "*.sh" -o -name "*.ps1" | sort | while read script; do
    if [ -x "$script" ] || [[ "$script" == *.ps1 ]]; then
        echo -e "${GREEN}  ✓${NC} $script"
    else
        echo -e "${YELLOW}  !${NC} $script ${YELLOW}(not executable)${NC}"
    fi
done
echo ""

# Step 5: Quick verification
echo -e "${CYAN}🔍 Quick verification:${NC}"
echo ""

# Check if fix-kafka.sh exists
if [ -f "scripts/kafka/fix-kafka.sh" ]; then
    echo -e "${GREEN}✅ Kafka fix script: Ready${NC}"
else
    echo -e "${YELLOW}⚠️  Kafka fix script: Missing${NC}"
fi

# Check if token test exists
if [ -f "scripts/testing/test-cross-service-token.sh" ] || [ -f "scripts/testing/test-cross-service-token.ps1" ]; then
    echo -e "${GREEN}✅ Token test scripts: Ready${NC}"
else
    echo -e "${YELLOW}⚠️  Token test scripts: Missing${NC}"
fi

# Check if README exists
if [ -f "scripts/README.md" ]; then
    echo -e "${GREEN}✅ Documentation: Ready${NC}"
else
    echo -e "${YELLOW}⚠️  Documentation: Missing${NC}"
fi
echo ""

# Step 6: Instructions
echo -e "${CYAN}📝 Next steps:${NC}"
echo ""
echo "  1. Fix Kafka (if needed):"
echo -e "     ${GREEN}./scripts/kafka/fix-kafka.sh${NC}"
echo ""
echo "  2. Test authentication:"
echo -e "     ${GREEN}./scripts/testing/test-cross-service-token.sh${NC}"
echo ""
echo "  3. Read documentation:"
echo -e "     ${GREEN}cat scripts/README.md${NC}"
echo ""

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
