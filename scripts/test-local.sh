#!/bin/bash
# Local test runner for YouTrack MCP
# Usage: ./scripts/test-local.sh [test-type]
# test-type: unit, integration, e2e, docker, all (default: unit)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default test type
TEST_TYPE="${1:-unit}"

echo -e "${GREEN}🧪 Running YouTrack MCP Tests (${TEST_TYPE})${NC}"
echo "=================================================="

# Function to run tests with proper error handling
run_tests() {
    local test_path="$1"
    local test_name="$2"
    
    echo -e "\n${YELLOW}Running ${test_name} tests...${NC}"
    
    if ./venv/bin/pytest "${test_path}" -m "${test_name}" --tb=short -v; then
        echo -e "${GREEN}✅ ${test_name} tests passed${NC}"
        return 0
    else
        echo -e "${RED}❌ ${test_name} tests failed${NC}"
        return 1
    fi
}

# Function to run linting
run_linting() {
    echo -e "\n${YELLOW}Running code quality checks...${NC}"
    
    # Check if tools are installed in venv
    if ! ./venv/bin/black --check --diff youtrack_mcp/ tests/; then
        echo -e "${YELLOW}⚠️  Code formatting issues found${NC}"
    else
        echo -e "${GREEN}✅ Code formatting is correct${NC}"
    fi
    
    if ! ./venv/bin/flake8 youtrack_mcp/ tests/; then
        echo -e "${YELLOW}⚠️  Linting issues found${NC}"
    else
        echo -e "${GREEN}✅ Linting is correct${NC}"
    fi
    
    if ! ./venv/bin/mypy youtrack_mcp/; then
        echo -e "${YELLOW}⚠️  Type checking issues found${NC}"
    else
        echo -e "${GREEN}✅ Type checking is correct${NC}"
    fi
}

# Main test execution
case "${TEST_TYPE}" in
    "unit")
        run_linting
        run_tests "tests/unit" "unit"
        ;;
    "integration")
        run_tests "tests/integration" "integration"
        ;;
    "e2e")
        echo -e "${YELLOW}⚠️  E2E tests require real YouTrack credentials${NC}"
        echo "Make sure YOUTRACK_URL and YOUTRACK_API_TOKEN are set"
        run_tests "tests/e2e" "e2e"
        ;;
    "docker")
        echo -e "${YELLOW}Running Docker tests...${NC}"
        # Run Docker-specific tests
        ./tests/docker/test_docker.sh
        ./venv/bin/python tests/docker/test_mcp_docker.py
        ;;
    "all")
        echo -e "${YELLOW}Running all test suites...${NC}"
        run_linting
        run_tests "tests/unit" "unit"
        run_tests "tests/integration" "integration"
        echo -e "\n${YELLOW}⚠️  Skipping E2E and Docker tests in 'all' mode${NC}"
        echo "Run them individually with: ./scripts/test-local.sh e2e"
        echo "                            ./scripts/test-local.sh docker"
        ;;
    *)
        echo -e "${RED}❌ Unknown test type: ${TEST_TYPE}${NC}"
        echo "Available types: unit, integration, e2e, docker, all"
        exit 1
        ;;
esac

echo -e "\n${GREEN}🎉 Test execution completed!${NC}" 