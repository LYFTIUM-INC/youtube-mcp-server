# YouTube MCP Server - Claude Desktop Setup

## Quick Setup for Claude Desktop

### 1. Copy Configuration to Claude Desktop

The YouTube MCP server only needs a **Google API Key** - no service account required!

**Copy this configuration** to your Claude Desktop settings:

```json
{
  "mcpServers": {
    "youtube-mcp": {
      "command": "python",
      "args": [
        "/home/dell/coding/mcp/youtube-mcp/mcp_server.py"
      ],
      "cwd": "/home/dell/coding/mcp/youtube-mcp",
      "env": {
        "GOOGLE_API_KEY": "your-google-api-key-here",
        "PYTHONPATH": "/home/dell/coding/mcp/youtube-mcp/src"
      }
    }
  }
}
```

### 2. Activate Virtual Environment First

Before starting Claude Desktop, ensure the virtual environment is activated:

```bash
cd /home/dell/coding/mcp/youtube-mcp
source venv/bin/activate
```

### 3. Alternative: Python Path Configuration

If you prefer to use the virtual environment Python directly:

```json
{
  "mcpServers": {
    "youtube-mcp": {
      "command": "/home/dell/coding/mcp/youtube-mcp/venv/bin/python",
      "args": [
        "/home/dell/coding/mcp/youtube-mcp/mcp_server.py"
      ],
      "cwd": "/home/dell/coding/mcp/youtube-mcp",
      "env": {
        "GOOGLE_API_KEY": "your-google-api-key-here",
        "PYTHONPATH": "/home/dell/coding/mcp/youtube-mcp/src"
      }
    }
  }
}
```

## What This MCP Provides

### 🔧 Tools Available (21 total)
- **Search & Discovery**: Search videos, get trending content
- **Video Analysis**: Get details, comments, transcripts
- **Session Management**: Create/manage analysis sessions
- **Data Export**: Export results to various formats
- **Visualization**: Generate charts and analytics

### 📊 Resources Available
- **Analysis Sessions**: Persistent data storage
- **Search Results**: Cached video data
- **Video Details**: Comprehensive metadata

### 💬 Prompts Available (8 total)
- **Content Analysis**: Video performance analysis
- **Trend Analysis**: Market trend identification
- **Competitive Analysis**: Channel comparison
- **Workflow Templates**: Complete analysis pipelines

## Why Only API Key?

The YouTube Data API v3 provides access to:
- ✅ **Public video data** (titles, descriptions, statistics)
- ✅ **Public comments** (top-level and replies)
- ✅ **Video transcripts** (when available)
- ✅ **Channel information** (public data)
- ✅ **Search results** (public videos)

**No OAuth/Service Account needed** because we're only accessing **public data**.

## Usage Examples

Once connected to Claude Desktop:

1. **Search for videos**: "Find top 10 Python tutorial videos"
2. **Analyze performance**: "Get detailed stats for video dQw4w9WgXcQ"
3. **Get comments**: "Fetch top 50 comments for this video"
4. **Create analysis**: "Start a new analysis session for tech tutorials"

## Environment Variables Required

Only **ONE** environment variable is required:

```bash
GOOGLE_API_KEY=your_youtube_api_key_here
```

Optional variables:
```bash
# Optional - for advanced features
OPENAI_API_KEY=your_openai_key  # For AI-powered analysis
PROJECT_ID=your_gcp_project     # For Google Cloud features
```

## Troubleshooting

### Connection Issues
1. Check that virtual environment is activated
2. Verify Python path in configuration
3. Ensure GOOGLE_API_KEY is valid

### Missing Dependencies
```bash
cd /home/dell/coding/mcp/youtube-mcp
source venv/bin/activate
pip install -r requirements.txt
```

### Test the Server
```bash
cd /home/dell/coding/mcp/youtube-mcp
source venv/bin/activate
python test_mcp_client.py
```

## API Quota Management

- **Daily limit**: 10,000 units
- **Search cost**: 100 units per query
- **Video details**: 1 unit per video
- **Comments**: 1 unit per request (100 comments max)

The MCP includes built-in caching to minimize API usage!