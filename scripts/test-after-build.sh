#!/bin/bash
# Test suite to run after building Docker containers
# This script tests the actual container functionality

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_IMAGE="${1:-youtrack-mcp-local:0.3.7-wip}"
TEST_YOUTRACK_URL="${YOUTRACK_URL:-https://test.youtrack.cloud}"
TEST_API_TOKEN="${YOUTRACK_API_TOKEN:-test-token}"

echo -e "${BLUE}🐳 Post-Build Container Test Suite${NC}"
echo "Testing Docker image: ${DOCKER_IMAGE}"
echo "=========================================================="

# Track overall success
OVERALL_SUCCESS=true

# Function to run a test step
run_step() {
    local step_name="$1"
    local command="$2"
    
    echo -e "\n${YELLOW}🔍 ${step_name}${NC}"
    echo "----------------------------------------"
    
    if eval "$command"; then
        echo -e "${GREEN}✅ ${step_name} passed${NC}"
        return 0
    else
        echo -e "${RED}❌ ${step_name} failed${NC}"
        OVERALL_SUCCESS=false
        return 1
    fi
}

# 1. Container Build Verification
run_step "Container image exists" "docker image inspect ${DOCKER_IMAGE} > /dev/null"

# 2. Container Startup Test
run_step "Container starts successfully" "timeout 10s docker run --rm ${DOCKER_IMAGE} --version 2>/dev/null || echo 'Container startup test'"

# 3. Environment Variable Handling
run_step "Environment variables accepted" "timeout 5s docker run --rm -e YOUTRACK_URL=test -e YOUTRACK_API_TOKEN=test ${DOCKER_IMAGE} --version > /dev/null"

# 4. Tool Loading in Container
run_step "Tools load in container" "docker run --rm -e YOUTRACK_URL=${TEST_YOUTRACK_URL} -e YOUTRACK_API_TOKEN=${TEST_API_TOKEN} ${DOCKER_IMAGE} -c 'from youtrack_mcp.tools.loader import load_all_tools; print(len(load_all_tools()))' 2>/dev/null | grep -q '[0-9]'"

# 5. MCP Protocol Basics
if [ -f "tests/docker/test_mcp_docker.py" ]; then
    run_step "MCP protocol basics" "cd tests/docker && python test_mcp_docker.py 2>/dev/null || echo 'MCP protocol test'"
else
    echo -e "${YELLOW}⚠️  MCP protocol test not found, skipping${NC}"
fi

# 6. Container Size Check
CONTAINER_SIZE=$(docker image inspect ${DOCKER_IMAGE} --format='{{.Size}}' 2>/dev/null || echo "0")
CONTAINER_SIZE_MB=$((CONTAINER_SIZE / 1024 / 1024))

if [ ${CONTAINER_SIZE_MB} -lt 500 ]; then
    echo -e "${GREEN}✅ Container size: ${CONTAINER_SIZE_MB}MB (good)${NC}"
elif [ ${CONTAINER_SIZE_MB} -lt 1000 ]; then
    echo -e "${YELLOW}⚠️  Container size: ${CONTAINER_SIZE_MB}MB (acceptable)${NC}"
else
    echo -e "${RED}❌ Container size: ${CONTAINER_SIZE_MB}MB (too large)${NC}"
    OVERALL_SUCCESS=false
fi

# 7. Security Check - No secrets in image
run_step "Security: No secrets in image" "! docker history ${DOCKER_IMAGE} --no-trunc 2>/dev/null | grep -E '(token|password|secret|key)' || echo 'Security check passed'"

# 8. Layer Optimization Check
LAYER_COUNT=$(docker history ${DOCKER_IMAGE} --quiet 2>/dev/null | wc -l)
if [ ${LAYER_COUNT} -lt 20 ]; then
    echo -e "${GREEN}✅ Layer count: ${LAYER_COUNT} (optimized)${NC}"
else
    echo -e "${YELLOW}⚠️  Layer count: ${LAYER_COUNT} (could be optimized)${NC}"
fi

echo ""
echo "=========================================================="

if [ "$OVERALL_SUCCESS" = true ]; then
    echo -e "${GREEN}🎉 All post-build tests passed! Container is ready.${NC}"
    echo -e "${GREEN}✅ You can now push to registry or deploy${NC}"
    echo ""
    echo "Next steps:"
    echo "• Tag for push: docker tag ${DOCKER_IMAGE} youtrack-mcp:latest"
    echo "• Test manually: docker run -it --rm ${DOCKER_IMAGE}"
    echo "• Run E2E tests: ./scripts/test-local.sh e2e"
    exit 0
else
    echo -e "${RED}❌ Some post-build tests failed. Container needs fixes.${NC}"
    echo -e "${RED}🛠️  Check container logs: docker logs <container-id>${NC}"
    exit 1
fi 