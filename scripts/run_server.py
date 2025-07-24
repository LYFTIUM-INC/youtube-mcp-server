#!/usr/bin/env python3
"""
CLI script to run the YouTube MCP Server.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from youtube_mcp_server import __main__


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="YouTube MCP Server - Model Context Protocol server for YouTube analytics"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--config-file",
        type=Path,
        help="Path to configuration file (.env format)"
    )
    
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to bind the server to (default: localhost)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="YouTube MCP Server 1.0.0"
    )
    
    return parser.parse_args()


def main():
    """Main CLI entry point."""
    args = parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting YouTube MCP Server CLI...")
    
    try:
        # Set environment variables from args if needed
        import os
        if args.config_file and args.config_file.exists():
            logger.info(f"Loading config from: {args.config_file}")
            from dotenv import load_dotenv
            load_dotenv(args.config_file)
        
        # Override host/port if specified
        if args.host != "localhost":
            os.environ["SERVER_HOST"] = args.host
        if args.port != 8000:
            os.environ["SERVER_PORT"] = str(args.port)
        
        # Run the server
        asyncio.run(__main__.main())
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()