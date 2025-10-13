# MergeMind API Tests

This directory contains comprehensive tests for the MergeMind API, including unit tests, integration tests, and end-to-end workflow tests.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py             # Pytest configuration and fixtures
├── test_health.py          # Health check endpoint tests
├── test_mrs.py             # MR list endpoint tests
├── test_mr.py              # Individual MR endpoint tests
├── test_services.py        # Service layer unit tests
├── test_integration.py     # End-to-end integration tests
└── README.md               # This file
```

## Test Categories

### Unit Tests (`test_services.py`)
- **BigQuery Client**: Connection, query execution, error handling
- **GitLab Client**: API calls, diff fetching, error handling
- **Vertex AI Client**: Text generation, diff summarization
- **Reviewer Service**: Reviewer suggestions, co-review graph
- **Risk Service**: Risk calculation, feature validation
- **User Service**: User lookup, caching, search
- **Metrics Service**: Request tracking, SLO monitoring

### Integration Tests (`test_integration.py`)
- **Complete MR Workflow**: Context → Summary → Reviewers → Risk
- **MR List and Detail**: List filtering → Detail view
- **Blocking MRs**: Top blockers identification
- **Health Monitoring**: Health checks → Readiness → Detailed health → Metrics → SLO
- **Error Handling**: 404s, 500s, service failures
- **Concurrent Requests**: Multiple simultaneous requests
- **Caching**: Cache hit/miss scenarios
- **Performance**: Response time validation

### Endpoint Tests
- **Health Endpoints** (`test_health.py`): `/healthz`, `/ready`, `/health/detailed`, `/metrics`
- **MR List Endpoints** (`test_mrs.py`): `/mrs`, `/blockers/top`
- **Individual MR Endpoints** (`test_mr.py`): `/mr/{id}/context`, `/mr/{id}/summary`, `/mr/{id}/reviewers`, `/mr/{id}/risk`

## Running Tests

### Prerequisites
```bash
# Install test dependencies
pip install -r requirements.txt
```

### Basic Test Execution
```bash
# Run all tests
python run_tests.py

# Run with verbose output
python run_tests.py --verbose

# Run with coverage reporting
python run_tests.py --coverage
```

### Specific Test Types
```bash
# Run only unit tests
python run_tests.py --type unit

# Run only integration tests
python run_tests.py --type integration

# Run specific test files
python run_tests.py --type health
python run_tests.py --type mrs
python run_tests.py --type mr
python run_tests.py --type services
```

### Using pytest directly
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_health.py

# Run with markers
pytest -m unit
pytest -m integration

# Run with coverage
pytest --cov=. --cov-report=html tests/
```

## Test Configuration

### Environment Variables
Tests use mock services and don't require real external dependencies. The following environment variables are set automatically:

```bash
GCP_PROJECT_ID=test-project
BQ_DATASET_RAW=test_raw
BQ_DATASET_MODELED=test_modeled
VERTEX_LOCATION=us-central1
GITLAB_BASE_URL=https://test.gitlab.com
GITLAB_TOKEN=test-token
API_BASE_URL=http://localhost:8080
LOG_LEVEL=DEBUG
```

### Fixtures
- `test_client`: FastAPI test client
- `mock_all_services`: Mocked external services
- `sample_mr_data`: Sample MR data
- `sample_mr_list`: Sample MR list
- `sample_summary`: Sample AI summary
- `sample_reviewers`: Sample reviewer suggestions
- `sample_risk_features`: Sample risk features

## Test Coverage

The tests provide comprehensive coverage of:

### API Endpoints
- ✅ Health check endpoints
- ✅ MR list endpoints
- ✅ Individual MR endpoints
- ✅ Error handling (404, 500)
- ✅ Request validation

### Service Layer
- ✅ BigQuery client operations
- ✅ GitLab client operations
- ✅ Vertex AI client operations
- ✅ Reviewer service logic
- ✅ Risk service logic
- ✅ User service operations
- ✅ Metrics collection

### Integration Workflows
- ✅ Complete MR analysis workflow
- ✅ Health monitoring workflow
- ✅ Error handling workflow
- ✅ Performance validation
- ✅ Caching behavior

## Mocking Strategy

### External Services
All external services are mocked to ensure:
- **Fast execution**: No network calls
- **Reliable results**: Consistent test data
- **Isolated testing**: No external dependencies
- **Error simulation**: Easy error scenario testing

### Mock Data
- **Realistic data**: Based on actual GitLab API responses
- **Edge cases**: Empty results, errors, timeouts
- **Performance**: Simulated response times

## Continuous Integration

### GitHub Actions
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python run_tests.py --coverage
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Add hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure you're in the correct directory
   cd api/fastapi_app
   python run_tests.py
   ```

2. **Missing Dependencies**
   ```bash
   # Install all requirements
   pip install -r requirements.txt
   ```

3. **Test Failures**
   ```bash
   # Run with verbose output for debugging
   python run_tests.py --verbose
   
   # Run specific failing test
   pytest tests/test_health.py::test_healthz_endpoint -v
   ```

### Debug Mode
```bash
# Run with debug logging
LOG_LEVEL=DEBUG python run_tests.py --verbose
```

## Contributing

### Adding New Tests
1. Create test file following naming convention: `test_*.py`
2. Use appropriate fixtures from `conftest.py`
3. Add proper docstrings and comments
4. Include both success and failure scenarios
5. Update this README if adding new test categories

### Test Guidelines
- **Isolation**: Each test should be independent
- **Clarity**: Use descriptive test names
- **Coverage**: Test both happy path and error cases
- **Performance**: Keep tests fast (< 1 second each)
- **Maintainability**: Use fixtures and helper functions

### Code Coverage
- Aim for > 90% code coverage
- Focus on critical paths and error handling
- Use coverage reports to identify gaps
- Update tests when adding new features
