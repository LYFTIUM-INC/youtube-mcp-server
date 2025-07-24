# YouTube Analytics MCP Server

A Model Context Protocol (MCP) server for YouTube analytics and data collection. This server provides comprehensive tools for analyzing YouTube videos, channels, comments, transcripts, and downloading content.

## Features

- **Video Analysis**: Search videos, get detailed metadata, analyze performance metrics
- **Channel Analytics**: Get channel information, list channel videos, track statistics
- **Content Collection**: Extract comments, transcripts, and download videos/audio
- **Data Export**: Download videos in various formats with fallback methods
- **Rate Limiting**: Built-in quota management and rate limiting for YouTube API
- **Caching**: Efficient caching system to minimize API calls

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd youtube-mcp-server

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# Required: YouTube Data API key
GOOGLE_API_KEY=your_youtube_data_api_key_here

# Optional: OpenAI API key for AI analysis features
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Test the Server

```bash
# Test that everything is configured correctly
python test_server.py
```

### 4. Run the Server

```bash
# Start the MCP server
python scripts/run_server.py

# Or run with custom options
python scripts/run_server.py --log-level DEBUG --port 8001
```

## Available Tools

The server provides 11 MCP tools:

### Data Collection
- `search_youtube_videos` - Search for videos with advanced filtering
- `get_video_details` - Get detailed video metadata and statistics
- `get_channel_info` - Get channel information and statistics
- `get_channel_videos` - List videos from a specific channel

### Content Analysis
- `get_video_comments` - Extract video comments with sentiment analysis
- `get_video_transcript` - Get video transcripts/captions
- `analyze_video_performance` - Calculate engagement metrics and performance scores
- `get_trending_videos` - Get trending videos by region/category

### Media Operations
- `download_video` - Download videos with multiple quality/format options
- `get_download_formats` - Check available download formats
- `cleanup_downloads` - Clean up old downloaded files

## Usage with Claude Desktop

Add this server to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "youtube-analytics": {
      "command": "python",
      "args": ["/path/to/youtube-mcp-server/scripts/run_server.py"],
      "env": {
        "GOOGLE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Example Usage

Once connected to Claude Desktop or MCP Inspector, you can use commands like:

```
Search for Python tutorial videos uploaded in the last month
Get detailed analytics for video ID dQw4w9WgXcQ
Download the top trending video in 720p quality
Analyze engagement metrics for my channel's latest 10 videos
```

## Configuration Options

Key configuration options in `.env`:

```bash
# API Configuration
GOOGLE_API_KEY=your_key_here
YOUTUBE_API_QUOTA_LIMIT=10000
YOUTUBE_API_RATE_LIMIT=1.0

# Cache Settings
CACHE_DIRECTORY=youtube_cache
CACHE_TTL_SECONDS=3600

# Download Settings
DOWNLOAD_DIRECTORY=downloads
MAX_CONCURRENT_DOWNLOADS=3

# Feature Flags
ENABLE_CACHING=true
ENABLE_RATE_LIMITING=true
ENABLE_ANALYTICS=true
ENABLE_DOWNLOADS=true
```

## Development

### Project Structure

```
youtube-mcp-server/
├── src/youtube_mcp_server/
│   ├── core/              # Core configuration and exceptions
│   ├── tools/             # MCP tools and API clients
│   └── infrastructure/    # Caching, rate limiting, etc.
├── scripts/               # CLI scripts
├── test_server.py         # Test script
└── .env.example          # Configuration template
```

### Running Tests

```bash
# Test server initialization
python test_server.py

# Run specific tool tests (if available)
python -m pytest tests/
```

## Requirements

- Python 3.9+
- YouTube Data API v3 key
- Dependencies listed in `requirements.txt`

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure all dependencies are installed
2. **API quota exceeded**: Check your YouTube API quota usage
3. **Authentication errors**: Verify your API key is correct
4. **Download failures**: Some videos may be restricted or unavailable

### Debug Mode

Run with debug logging to see detailed information:

```bash
python scripts/run_server.py --log-level DEBUG
```

## License

MIT License - see LICENSE file for details.