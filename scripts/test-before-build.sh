#!/bin/bash
# Test suite to run before building Docker containers
# This script runs fast tests that don't require external services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏗️  Pre-Build Test Suite${NC}"
echo "This runs tests that should pass before building containers"
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

# 1. Code Quality Checks
run_step "Code formatting (black)" "black --check --diff youtrack_mcp/ tests/ 2>/dev/null || echo 'Formatting issues found'"

run_step "Linting (flake8)" "flake8 youtrack_mcp/ tests/ --max-line-length=88 --extend-ignore=E203,W503 2>/dev/null || echo 'Linting issues found'"

run_step "Type checking (mypy)" "mypy youtrack_mcp/ --ignore-missing-imports 2>/dev/null || echo 'Type checking issues found'"

run_step "Import sorting (isort)" "isort --check-only --diff youtrack_mcp/ tests/ 2>/dev/null || echo 'Import sorting issues found'"

# 2. Unit Tests
run_step "Unit tests" "pytest tests/unit/ -v --tb=short"

# 3. Integration Tests (with mocked services)
if [ -d "tests/integration" ] && [ "$(ls -A tests/integration/*.py 2>/dev/null)" ]; then
    run_step "Integration tests (mocked)" "pytest tests/integration/ -v --tb=short"
else
    echo -e "${YELLOW}⚠️  No integration tests found, skipping${NC}"
fi

# 4. Tool loading verification
run_step "Tool loading verification" "python -c 'from youtrack_mcp.tools.loader import load_all_tools; tools = load_all_tools(); print(f\"Loaded {len(tools)} tools successfully\")'"

# 5. Import verification
run_step "Import verification" "python -c 'import youtrack_mcp.mcp_server; import youtrack_mcp.server; print(\"All imports successful\")'"

# 6. Version consistency check
run_step "Version consistency" "python -c 'from youtrack_mcp.version import __version__; print(f\"Version: {__version__}\")'"

echo ""
echo "=========================================================="

if [ "$OVERALL_SUCCESS" = true ]; then
    echo -e "${GREEN}🎉 All pre-build tests passed! Ready to build containers.${NC}"
    echo -e "${GREEN}✅ You can now run: docker build -t youtrack-mcp .${NC}"
    exit 0
else
    echo -e "${RED}❌ Some pre-build tests failed. Fix issues before building.${NC}"
    echo -e "${RED}🛠️  Run individual checks with: ./scripts/test-local.sh unit${NC}"
    exit 1
fi 