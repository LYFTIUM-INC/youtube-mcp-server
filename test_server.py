#!/usr/bin/env python3
"""
Simple test to verify the MCP server can initialize properly.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from youtube_mcp_server.core.config import YouTubeMCPConfig
from youtube_mcp_server.tools.core_tools import YouTubeMCPTools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_server_initialization():
    """Test that the server can initialize without errors."""
    try:
        logger.info("Testing YouTube MCP Server initialization...")
        
        # Test configuration loading
        config = YouTubeMCPConfig()
        logger.info(f"✓ Configuration loaded successfully")
        logger.info(f"  - Cache directory: {config.cache_directory}")
        logger.info(f"  - Download directory: {config.download_directory}")
        logger.info(f"  - Google API key configured: {'Yes' if config.google_api_key else 'No'}")
        
        # Test tools initialization
        youtube_tools = YouTubeMCPTools(config)
        await youtube_tools.initialize()
        logger.info("✓ YouTube tools initialized successfully")
        
        # Test tool registration
        tools = youtube_tools.get_tools()
        logger.info(f"✓ {len(tools)} tools registered:")
        for tool in tools:
            logger.info(f"  - {tool.name}: {tool.description}")
        
        # Cleanup
        await youtube_tools.cleanup()
        logger.info("✓ Cleanup completed successfully")
        
        logger.info("\n🎉 Server initialization test PASSED!")
        logger.info("The MCP server is ready to run.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Server initialization test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test runner."""
    success = await test_server_initialization()
    
    if success:
        logger.info("\nNext steps:")
        logger.info("1. Copy .env.example to .env and configure your API keys")
        logger.info("2. Run: python scripts/run_server.py")
        logger.info("3. Test with MCP inspector or Claude Desktop")
        sys.exit(0)
    else:
        logger.error("\nPlease fix the errors above before proceeding.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())