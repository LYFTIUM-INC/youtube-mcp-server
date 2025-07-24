#!/usr/bin/env python3
"""
Test script for ResourceManager integration with MCP Server.
Verifies that session management and resource persistence work correctly.
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from youtube_mcp_server.core.config import YouTubeMCPConfig
from youtube_mcp_server.tools.core_tools import YouTubeMCPTools


async def test_resource_manager_integration():
    """Test the ResourceManager integration with YouTube MCP Tools."""
    print("🧪 Testing ResourceManager Integration with YouTube MCP Tools")
    print("=" * 60)
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        config = YouTubeMCPConfig()
        config.output_directory = Path(temp_dir)
        
        # Initialize YouTube tools
        youtube_tools = YouTubeMCPTools(config)
        await youtube_tools.initialize()
        
        print(f"✅ YouTube tools initialized")
        print(f"📁 Using temp directory: {temp_dir}")
        print()
        
        # Test 1: Create analysis session
        print("🔵 Test 1: Creating analysis session")
        session_result = await youtube_tools.execute_tool(
            "create_analysis_session",
            {
                "title": "Test Integration Session",
                "description": "Testing ResourceManager integration",
                "auto_switch": True
            }
        )
        
        session_data = json.loads(session_result[0].text)
        print(f"   Session created: {session_data['session_id']}")
        print(f"   Title: {session_data['title']}")
        print()
        
        # Test 2: List sessions
        print("🔵 Test 2: Listing analysis sessions")
        list_result = await youtube_tools.execute_tool("list_analysis_sessions", {})
        list_data = json.loads(list_result[0].text)
        print(f"   Total sessions: {list_data['total_sessions']}")
        print(f"   Current session: {list_data['current_session_id']}")
        print()
        
        # Test 3: Simulate search (with mock data)
        print("🔵 Test 3: Testing search result persistence")
        mock_search_results = [
            {"id": "dQw4w9WgXcQ", "title": "Rick Astley - Never Gonna Give You Up"},
            {"id": "jNQXAC9IVRw", "title": "Me at the zoo"},
            {"id": "9bZkp7q19f0", "title": "PSY - GANGNAM STYLE"}
        ]
        
        # Manually save search results (simulating what would happen in real search)
        resource_uri = youtube_tools.resource_manager.save_search_results(
            query="test search",
            results=mock_search_results
        )
        print(f"   Search results saved to: {resource_uri}")
        
        # Test 4: Get session video IDs
        print("🔵 Test 4: Getting session video IDs")
        video_ids_result = await youtube_tools.execute_tool("get_session_video_ids", {})
        video_ids_data = json.loads(video_ids_result[0].text)
        print(f"   Video count: {video_ids_data['video_count']}")
        print(f"   Video IDs: {video_ids_data['video_ids']}")
        print()
        
        # Test 5: Test resource listing
        print("🔵 Test 5: Testing resource listing")
        resources = youtube_tools.resource_manager.list_all_resources()
        print(f"   Total resources: {len(resources)}")
        for resource in resources:
            print(f"   - {resource.name} ({resource.uri})")
        print()
        
        # Test 6: Test resource reading
        print("🔵 Test 6: Testing resource reading")
        if resources:
            test_resource = resources[0]
            content = await youtube_tools.resource_manager.read_resource(test_resource.uri)
            if content:
                print(f"   Successfully read resource: {test_resource.uri}")
                print(f"   Content type: {type(content).__name__}")
            else:
                print(f"   Failed to read resource: {test_resource.uri}")
        print()
        
        # Test 7: Directory structure verification
        print("🔵 Test 7: Verifying directory structure")
        base_path = youtube_tools.resource_manager.base_path
        print(f"   Base path: {base_path}")
        
        expected_dirs = ["sessions", "searches", "visualizations", "cache"]
        for dir_name in expected_dirs:
            dir_path = base_path / dir_name
            exists = dir_path.exists()
            print(f"   - {dir_name}/: {'✅' if exists else '❌'}")
        
        # Check for session files
        sessions_file = base_path / "sessions" / "sessions.json"
        if sessions_file.exists():
            print(f"   - sessions.json: ✅")
            with open(sessions_file, 'r') as f:
                sessions_content = json.load(f)
                print(f"     Sessions in file: {len(sessions_content.get('sessions', []))}")
        else:
            print(f"   - sessions.json: ❌")
        
        print()
        print("🎉 ResourceManager integration test completed!")
        print("=" * 60)
        
        await youtube_tools.cleanup()


if __name__ == "__main__":
    asyncio.run(test_resource_manager_integration())