# YouTrack MCP Testing Guide

This document explains the testing strategy, structure, and best practices for the YouTrack MCP project.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_tools.py        # Tool loading tests
│   ├── test_priority.py     # Tool prioritization tests
│   └── ...
├── integration/             # Integration tests (mocked external services)
│   └── ...
├── e2e/                     # End-to-end tests (real services)
│   └── ...
├── docker/                  # Docker container tests
│   ├── test_docker.sh       # Container build/run tests
│   ├── test_mcp_docker.py   # MCP protocol tests
│   └── ...
└── README.md               # This file
```

## Test Types

### 1. Unit Tests (`tests/unit/`)
- **Purpose**: Test individual functions and classes in isolation
- **Speed**: Fast (< 1 second per test)
- **Dependencies**: No external services, all mocked
- **When to run**: Before every commit, in CI/CD

**Example**:
```python
@pytest.mark.unit
def test_tool_loading_basic(self, mock_youtrack_client):
    """Test that tools can be loaded without errors."""
    tools = load_all_tools()
    assert isinstance(tools, dict)
```

### 2. Integration Tests (`tests/integration/`)
- **Purpose**: Test how components work together with mocked external services
- **Speed**: Medium (1-5 seconds per test)
- **Dependencies**: Mocked YouTrack API, real internal components
- **When to run**: Before building containers, in CI/CD

### 3. End-to-End Tests (`tests/e2e/`)
- **Purpose**: Test complete workflows with real YouTrack instance
- **Speed**: Slow (5-30 seconds per test)
- **Dependencies**: Real YouTrack instance and credentials
- **When to run**: Manual testing, release validation

**Note**: E2E tests require valid `YOUTRACK_URL` and `YOUTRACK_API_TOKEN` environment variables.

### 4. Docker Tests (`tests/docker/`)
- **Purpose**: Test Docker container functionality and MCP protocol
- **Speed**: Medium to slow (depends on Docker operations)
- **Dependencies**: Docker daemon, built container images
- **When to run**: After building containers, before deployment

## Running Tests

### Quick Commands

```bash
# Run all unit tests (recommended for development)
./scripts/test-local.sh unit

# Run integration tests
./scripts/test-local.sh integration

# Run end-to-end tests (requires credentials)
./scripts/test-local.sh e2e

# Run Docker tests
./scripts/test-local.sh docker

# Run all tests (skips E2E and Docker in CI)
./scripts/test-local.sh all
```

### Pre-Build Testing

Before building Docker containers, run:

```bash
./scripts/test-before-build.sh
```

This runs:
1. Code quality checks (black, flake8, mypy, isort)
2. Unit tests
3. Integration tests (if available)
4. Import verification
5. Tool loading verification

### Post-Build Testing

After building Docker containers, run:

```bash
./scripts/test-after-build.sh [image-name]
```

This tests:
1. Container exists and starts
2. Environment variable handling
3. Tool loading in container
4. MCP protocol basics
5. Container size and security

### Manual Testing

```bash
# Run pytest directly with specific markers
pytest tests/unit/ -m unit -v

# Run tests with coverage
pytest tests/ --cov=youtrack_mcp --cov-report=html

# Run specific test
pytest tests/unit/test_tools.py::TestToolLoading::test_tool_loading_basic
```

## Development Workflow

### 1. Before Writing Code
```bash
# Ensure existing tests pass
./scripts/test-local.sh unit
```

### 2. While Writing Code
- Write unit tests for new functions
- Use TDD (Test-Driven Development) when possible
- Mock external dependencies

### 3. Before Committing
```bash
# Run comprehensive pre-build tests
./scripts/test-before-build.sh
```

### 4. Before Building Containers
```bash
# All pre-build tests must pass
./scripts/test-before-build.sh

# Build container
docker build -t youtrack-mcp-local .

# Test container
./scripts/test-after-build.sh youtrack-mcp-local
```

## Test Configuration

### Pytest Configuration (`pytest.ini`)
- Sets test discovery patterns
- Configures coverage reporting
- Defines custom markers
- Sets warning filters

### Shared Fixtures (`conftest.py`)
- `mock_youtrack_client`: Mocked YouTrack client
- `test_config`: Test configuration values
- `sample_*_data`: Sample data for testing

### Environment Variables
- `YOUTRACK_URL`: YouTrack instance URL (for E2E tests)
- `YOUTRACK_API_TOKEN`: API token (for E2E tests)

## Writing Good Tests

### Unit Test Guidelines
1. **Fast**: Each test should run in under 1 second
2. **Isolated**: No external dependencies, mock everything
3. **Deterministic**: Same input always produces same output
4. **Single purpose**: Test one thing at a time

### Integration Test Guidelines
1. **Mock external services**: Use real internal components, mock external APIs
2. **Test interactions**: Focus on how components work together
3. **Realistic data**: Use data that represents real usage

### Test Naming
- Use descriptive names: `test_tool_loading_with_invalid_config`
- Follow pattern: `test_<what>_<condition>_<expected_result>`
- Use markers: `@pytest.mark.unit`, `@pytest.mark.integration`, etc.

### Mocking Guidelines
```python
# Good: Mock external dependencies
@patch('youtrack_mcp.api.client.YouTrackClient')
def test_with_mocked_client(mock_client):
    ...

# Good: Use fixtures for common mocks
def test_with_fixture(mock_youtrack_client):
    ...

# Avoid: Testing mocked behavior instead of real logic
```

## CI/CD Integration

### GitHub Actions Workflow
The `.github/workflows/docker-build.yml` includes:
1. **Pre-build tests**: Code quality and unit tests
2. **Container build**: Build test Docker image
3. **Post-build tests**: Container functionality tests

### Test Requirements
- All unit tests must pass before building containers
- Container tests must pass before deployment
- E2E tests are run manually before releases

## Troubleshooting

### Common Issues

1. **Import errors in tests**
   ```bash
   # Fix: Install package in development mode
   pip install -e .
   ```

2. **Mock not working**
   ```python
   # Ensure you're mocking the right path
   @patch('youtrack_mcp.tools.loader.IssueTools')  # Where it's imported
   ```

3. **Tests pass locally but fail in CI**
   - Check Python version compatibility
   - Verify all dependencies are in requirements.txt
   - Check for environment-specific behavior

### Debug Mode
```bash
# Run tests with debug output
pytest tests/unit/ -v -s --tb=long

# Run single test with debugging
pytest tests/unit/test_tools.py::TestToolLoading::test_tool_loading_basic -v -s
```

## Coverage Goals

- **Unit tests**: > 90% coverage for core logic
- **Integration tests**: Cover major user workflows
- **E2E tests**: Cover critical business scenarios
- **Overall**: > 80% code coverage (configured in pytest.ini)

## Best Practices Summary

1. **Test pyramid**: More unit tests, fewer E2E tests
2. **Fast feedback**: Unit tests should be fast and run frequently
3. **Realistic tests**: Integration tests should use realistic scenarios
4. **Clear assertions**: Each test should have clear, specific assertions
5. **Documentation**: Document complex test setups and edge cases
6. **Maintenance**: Keep tests updated as code changes 