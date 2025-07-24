"""
Main YouTube MCP Server implementation.

This module contains the core MCP server that orchestrates all YouTube analytics
tools, manages resources, handles authentication, and provides the main API interface.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
import mcp.types as types

from .config import YouTubeMCPConfig
from .exceptions import YouTubeMCPError, ConfigurationError
from ..tools import YouTubeMCPTools


logger = logging.getLogger(__name__)


class YouTubeMCPServer:
    """
    Main YouTube Analytics MCP Server.
    
    Provides comprehensive YouTube analytics capabilities through a Model Context
    Protocol interface, including data collection, analysis, visualization, and
    AI-powered insights.
    """
    
    def __init__(self, config: Optional[YouTubeMCPConfig] = None):
        """
        Initialize the YouTube MCP Server.
        
        Args:
            config: Server configuration. If None, loads from environment.
        """
        self.config = config or YouTubeMCPConfig.from_env()
        self.mcp = FastMCP("YouTube Analytics Server")
        
        # Core YouTube MCP Tools
        self.youtube_tools: Optional[YouTubeMCPTools] = None
        
        # Server state
        self._initialized = False
        self._running = False
        self._startup_time: Optional[datetime] = None
        
        logger.info("YouTube MCP Server initialized")
    
    async def initialize(self) -> None:
        """Initialize all server components."""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing YouTube MCP Server components...")
            
            # Initialize YouTube MCP Tools
            self.youtube_tools = YouTubeMCPTools(self.config)
            await self.youtube_tools.initialize()
            
            # Register tools with FastMCP
            await self._register_tools()
            
            self._initialized = True
            self._startup_time = datetime.now()
            
            logger.info("YouTube MCP Server successfully initialized")
            
        except Exception as e:
            logger.error("Failed to initialize YouTube MCP Server: %s", e)
            raise ConfigurationError(f"Server initialization failed: {e}") from e
    
    async def _register_tools(self) -> None:
        """Register all MCP tools."""
        logger.debug("Registering MCP tools...")
        
        if not self.youtube_tools:
            raise ConfigurationError("YouTube tools not initialized")
        
        # Get all tools from YouTube MCP Tools
        tools = self.youtube_tools.get_tools()
        
        # Register each tool with the FastMCP server
        for tool in tools:
            @self.mcp.tool(tool.name, description=tool.description, inputSchema=tool.inputSchema)
            async def tool_handler(name: str = tool.name, **kwargs):
                return await self.youtube_tools.execute_tool(name, kwargs)
        
        logger.info("Registered %d tools", len(tools))
    
    async def start(self) -> None:
        """Start the MCP server."""
        if self._running:
            logger.warning("Server is already running")
            return
        
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info("Starting YouTube MCP Server")
            
            self._running = True
            
            # Start the FastMCP server
            await self.mcp.run()
            
        except Exception as e:
            logger.error("Failed to start server: %s", e)
            self._running = False
            raise
    
    async def stop(self) -> None:
        """Stop the MCP server and cleanup resources."""
        if not self._running:
            return
        
        logger.info("Stopping YouTube MCP Server...")
        
        try:
            # Cleanup YouTube tools
            if self.youtube_tools:
                await self.youtube_tools.cleanup()
            
            self._running = False
            logger.info("YouTube MCP Server stopped successfully")
            
        except Exception as e:
            logger.error("Error during server shutdown: %s", e)
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of all server components.
        
        Returns:
            Health status information.
        """
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (
                (datetime.now() - self._startup_time).total_seconds()
                if self._startup_time else 0
            ),
            "components": {},
        }
        
        try:
            # Check YouTube tools
            if self.youtube_tools:
                health_data["components"]["youtube_tools"] = {
                    "status": "healthy",
                    "initialized": True
                }
            
            # Check if server is initialized and running
            health_data["components"]["server"] = {
                "status": "healthy" if self._initialized and self._running else "unhealthy",
                "initialized": self._initialized,
                "running": self._running
            }
            
            # Check overall health
            unhealthy_components = [
                name for name, status in health_data["components"].items()
                if status.get("status") != "healthy"
            ]
            
            if unhealthy_components:
                health_data["status"] = "degraded"
                health_data["unhealthy_components"] = unhealthy_components
            
        except Exception as e:
            logger.error("Health check failed: %s", e)
            health_data["status"] = "unhealthy"
            health_data["error"] = str(e)
        
        return health_data
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get server metrics and statistics.
        
        Returns:
            Server metrics data.
        """
        tools_count = len(self.youtube_tools.get_tools()) if self.youtube_tools else 0
        
        metrics = {
            "server": {
                "uptime_seconds": (
                    (datetime.now() - self._startup_time).total_seconds()
                    if self._startup_time else 0
                ),
                "initialized": self._initialized,
                "running": self._running,
            },
            "tools": {
                "total_registered": tools_count,
                "categories": {
                    "data_collection": tools_count,  # All our current tools are data collection
                    "analytics": 0,
                    "visualization": 0,
                    "export": 0,
                }
            },
        }
        
        return metrics
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific tool.
        
        Args:
            tool_name: Name of the tool.
            
        Returns:
            Tool information or None if not found.
        """
        if not self.youtube_tools:
            return None
        
        tools = self.youtube_tools.get_tools()
        for tool in tools:
            if tool.name == tool_name:
                return {
                    "name": tool.name,
                    "description": tool.description,
                    "schema": tool.inputSchema,
                    "category": self._categorize_tool(tool.name),
                }
        
        return None
    
    def list_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all available tools, optionally filtered by category.
        
        Args:
            category: Optional category filter.
            
        Returns:
            List of tool information.
        """
        if not self.youtube_tools:
            return []
        
        tools = []
        for tool in self.youtube_tools.get_tools():
            tool_info = {
                "name": tool.name,
                "description": tool.description,
                "schema": tool.inputSchema,
                "category": self._categorize_tool(tool.name),
            }
            
            if not category or tool_info["category"] == category:
                tools.append(tool_info)
        
        return sorted(tools, key=lambda x: x["name"])
    
    def _categorize_tool(self, tool_name: str) -> str:
        """Categorize a tool based on its name."""
        if any(tool_name.startswith(prefix) for prefix in ["search_", "get_", "collect_", "extract_"]):
            return "data_collection"
        elif any(tool_name.startswith(prefix) for prefix in ["analyze_", "detect_", "predict_", "perform_"]):
            return "analytics"
        elif any(word in tool_name for word in ["dashboard", "chart", "plot", "visualiz", "wordcloud"]):
            return "visualization"
        elif any(word in tool_name for word in ["export", "report", "generate_comprehensive"]):
            return "export"
        elif any(word in tool_name for word in ["thumbnail", "competitor", "ai_"]):
            return "ai_analysis"
        else:
            return "other"
    
    @property
    def is_initialized(self) -> bool:
        """Check if the server is initialized."""
        return self._initialized
    
    @property
    def is_running(self) -> bool:
        """Check if the server is running."""
        return self._running
    
    @property
    def uptime(self) -> float:
        """Get server uptime in seconds."""
        if not self._startup_time:
            return 0.0
        return (datetime.now() - self._startup_time).total_seconds()


# Context manager support
class YouTubeMCPServerContext:
    """Context manager for YouTube MCP Server."""
    
    def __init__(self, config: Optional[YouTubeMCPConfig] = None):
        self.server = YouTubeMCPServer(config)
    
    async def __aenter__(self) -> YouTubeMCPServer:
        await self.server.initialize()
        return self.server
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.server.stop()


# Convenience function
async def create_and_run_server(config: Optional[YouTubeMCPConfig] = None) -> None:
    """
    Create and run a YouTube MCP Server.
    
    Args:
        config: Server configuration.
    """
    server = YouTubeMCPServer(config)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    finally:
        await server.stop()


if __name__ == "__main__":
    # Run server directly
    asyncio.run(create_and_run_server())