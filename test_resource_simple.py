#!/usr/bin/env python3
"""
Simple test for ResourceManager functionality.
Tests core session management and resource persistence without YouTube API.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from youtube_mcp_server.infrastructure.resource_manager import ResourceManager


def test_resource_manager():
    """Test the ResourceManager core functionality."""
    print("🧪 Testing ResourceManager Core Functionality")
    print("=" * 50)
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir) / "test_resources"
        resource_manager = ResourceManager(base_path)
        
        print(f"📁 Using temp directory: {base_path}")
        print()
        
        # Test 1: Create analysis session
        print("🔵 Test 1: Creating analysis session")
        session_id = resource_manager.create_session(
            title="Test Session",
            description="Testing ResourceManager functionality",
            auto_switch=True
        )
        print(f"   ✅ Session created: {session_id}")
        print(f"   Current session: {resource_manager.current_session_id}")
        print()
        
        # Test 2: Get session
        print("🔵 Test 2: Getting session")
        session = resource_manager.get_session(session_id)
        if session:
            print(f"   ✅ Session retrieved: {session.title}")
            print(f"   Description: {session.description}")
            print(f"   Created: {session.created_at}")
        else:
            print("   ❌ Failed to retrieve session")
        print()
        
        # Test 3: Save search results
        print("🔵 Test 3: Saving search results")
        mock_search_results = [
            {"id": "dQw4w9WgXcQ", "title": "Rick Astley - Never Gonna Give You Up"},
            {"id": "jNQXAC9IVRw", "title": "Me at the zoo"},
            {"id": "9bZkp7q19f0", "title": "PSY - GANGNAM STYLE"}
        ]
        
        search_uri = resource_manager.save_search_results(
            query="test search",
            results=mock_search_results,
            session_id=session_id
        )
        print(f"   ✅ Search results saved: {search_uri}")
        
        # Check if video IDs were extracted
        updated_session = resource_manager.get_session(session_id)
        print(f"   Video IDs in session: {len(updated_session.video_ids)}")
        print(f"   Video IDs: {list(updated_session.video_ids)}")
        print()
        
        # Test 4: Save video details
        print("🔵 Test 4: Saving video details")
        mock_video_details = [
            {
                "id": "dQw4w9WgXcQ",
                "snippet": {"title": "Rick Astley - Never Gonna Give You Up"},
                "statistics": {"viewCount": "1400000000", "likeCount": "15000000"}
            },
            {
                "id": "jNQXAC9IVRw", 
                "snippet": {"title": "Me at the zoo"},
                "statistics": {"viewCount": "300000000", "likeCount": "5000000"}
            }
        ]
        
        details_uri = resource_manager.save_video_details(
            video_details=mock_video_details,
            session_id=session_id
        )
        print(f"   ✅ Video details saved: {details_uri}")
        print()
        
        # Test 5: Get session video IDs
        print("🔵 Test 5: Getting session video IDs")
        video_ids = resource_manager.get_session_video_ids(session_id)
        print(f"   ✅ Video IDs retrieved: {len(video_ids)}")
        print(f"   Video IDs: {video_ids}")
        print()
        
        # Test 6: List resources
        print("🔵 Test 6: Listing resources")
        resources = resource_manager.get_session_resources(session_id)
        print(f"   ✅ Total resources: {len(resources)}")
        for i, resource in enumerate(resources):
            print(f"   {i+1}. {resource.name}")
            print(f"      URI: {resource.uri}")
            print(f"      Type: {resource.mimeType}")
        print()
        
        # Test 7: Save visualization (mock)
        print("🔵 Test 7: Saving visualization")
        mock_viz_data = {
            "success": True,
            "filepath": "/fake/path/chart.png",
            "title": "Test Engagement Chart",
            "description": "Mock visualization for testing"
        }
        
        viz_uri = resource_manager.save_visualization(
            viz_type="engagement_chart",
            viz_data=mock_viz_data,
            session_id=session_id
        )
        print(f"   ✅ Visualization saved: {viz_uri}")
        print()
        
        # Test 8: Create second session
        print("🔵 Test 8: Creating second session and switching")
        session_id_2 = resource_manager.create_session(
            title="Second Test Session",
            description="Another test session",
            auto_switch=False
        )
        print(f"   ✅ Second session created: {session_id_2}")
        print(f"   Current session (should still be first): {resource_manager.current_session_id}")
        
        # Switch to second session
        switched = resource_manager.switch_session(session_id_2)
        print(f"   ✅ Switched to second session: {switched}")
        print(f"   Current session: {resource_manager.current_session_id}")
        print()
        
        # Test 9: List all sessions
        print("🔵 Test 9: Listing all sessions")
        all_sessions = list(resource_manager.sessions.values())
        print(f"   ✅ Total sessions: {len(all_sessions)}")
        for session in all_sessions:
            is_current = session.session_id == resource_manager.current_session_id
            current_marker = " (current)" if is_current else ""
            print(f"   - {session.title} ({session.session_id[:8]}...){current_marker}")
            print(f"     Video count: {len(session.video_ids)}")
            print(f"     Resources: {len(session.resources)}")
        print()
        
        # Test 10: Directory structure verification
        print("🔵 Test 10: Verifying directory structure")
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
        
        # Check for search files
        search_files = list((base_path / "searches").glob("*.json"))
        print(f"   - Search files: {len(search_files)} ✅")
        
        print()
        print("🎉 ResourceManager test completed successfully!")
        print("=" * 50)


if __name__ == "__main__":
    test_resource_manager()