# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Development Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run the MCP server (primary method)
python scripts/run_server.py

# Test server functionality
python test_server.py

# Run with debug logging
python scripts/run_server.py --log-level DEBUG

# Run tests with coverage
pytest --cov=src/youtube_mcp_server --cov-report=term-missing

# Code formatting and linting
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests
```

### Entry Points
- `python scripts/run_server.py` - Primary MCP server with full features
- `python mcp_server.py` - MCP Inspector compatible entry point
- `python src/youtube_mcp_server/__main__.py` - Package entry point

## Architecture Overview

This is a **Model Context Protocol (MCP) server** for YouTube analytics built with `fastmcp`. The architecture follows a layered approach:

### Core Architecture Layers
1. **MCP Server Layer** - Handles MCP protocol communication and tool registration
2. **Tools Layer** - 11 MCP tools for YouTube operations (search, analysis, downloads)
3. **Infrastructure Layer** - Cross-cutting concerns (caching, rate limiting, error handling)
4. **API Client Layer** - YouTube Data API integration with retry logic

### Key Architectural Patterns
- **Dependency Injection**: Configuration and services injected into tools
- **Resource Management**: MCP resources for sessions, cached data, and search results
- **Tool Orchestration**: `core_tools.py` acts as the main coordinator
- **Modular Infrastructure**: Separate managers for cache, rate limiting, retries, and errors

### Configuration System
- **Pydantic-based**: Type-safe configuration with validation in `core/config.py`
- **Environment Variables**: All settings configurable via `.env` file
- **Feature Flags**: Enable/disable functionality (caching, downloads, analytics)
- **API Quota Management**: Built-in YouTube API quota tracking and rate limiting

### Data Flow
1. MCP client calls tools through the protocol
2. Tools use YouTube API client with rate limiting and caching
3. Data processed through pandas/numpy for analytics
4. Results cached in `youtube_cache/` and returned to client
5. Resources (sessions, search results) managed in `output/resources/`

## Critical Development Notes

### API Integration Requirements
- **YouTube Data API v3 key required** in `GOOGLE_API_KEY` environment variable
- API calls are rate-limited (default 1.0 calls/second) and cached (1 hour TTL)
- Quota management prevents exceeding daily API limits

### Tool System Design
All tools in `tools/core_tools.py` follow this pattern:
- Accept standardized parameters with Pydantic validation
- Use dependency-injected services (API client, cache, rate limiter)
- Return structured data with error handling
- Support both synchronous and asynchronous operations

### Resource and Session Management
- **Sessions**: Track user workflows in `output/resources/sessions/`
- **Cache**: API responses cached in `youtube_cache/` directory
- **Search Results**: Persistent search data in `output/resources/searches/`
- **Downloads**: Video files stored in `downloads/` directory

### Infrastructure Services
- **CacheManager**: File-based caching with TTL and size limits
- **RateLimiter**: Token bucket algorithm for API throttling
- **RetryManager**: Exponential backoff for failed API calls
- **ErrorHandler**: Structured error logging and user-friendly messages

### Testing Strategy
- **Unit tests**: Fast, isolated tests for individual components
- **Integration tests**: Test API integrations and tool interactions
- **E2E tests**: Full workflow testing with real API calls
- Use markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`

### Key Dependencies to Understand
- `fastmcp` - MCP server framework (handles protocol, tool registration)
- `google-api-python-client` - YouTube Data API integration
- `yt-dlp` - Video downloading with format selection
- `pandas/numpy` - Data analysis and metrics calculation
- `matplotlib/plotly` - Visualization generation