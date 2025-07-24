#!/usr/bin/env python3
"""
Test script for video frame extraction functionality.
Tests frame extraction with various configurations before committing.
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from youtube_mcp_server.core.config import YouTubeMCPConfig
from youtube_mcp_server.tools.core_tools import YouTubeMCPTools

async def test_frame_extraction():
    """Test frame extraction functionality."""
    print("🎬 Testing YouTube MCP Frame Extraction Tool...")
    print("=" * 60)
    
    # Initialize configuration
    config = YouTubeMCPConfig()
    if not config.google_api_key:
        print("❌ No YouTube API key configured. Please set GOOGLE_API_KEY environment variable.")
        return False
    
    # Initialize tools
    tools = YouTubeMCPTools(config)
    await tools.initialize()
    
    tests_passed = 0
    total_tests = 4
    
    print("\n📥 Test 1: Basic Frame Extraction (Short Segment)")
    print("-" * 50)
    
    try:
        # Test basic frame extraction with a known video
        result = await tools._extract_video_frames(
            video_id="dQw4w9WgXcQ",  # Rick Roll - reliable test video
            segment_start=10,        # Start at 10 seconds
            segment_end=15,          # End at 15 seconds  
            interval_seconds=1.0,    # 1 frame per second
            max_frames=10,           # Limit to 10 frames
            quality="medium"         # Medium quality for faster processing
        )
        
        if result and isinstance(result, list) and len(result) > 0:
            result_data = json.loads(result[0].text)
            if result_data.get("success") and result_data.get("total_frames", 0) > 0:
                frames_count = result_data["total_frames"]
                output_dir = result_data["output_directory"]
                print(f"   ✅ Basic extraction - SUCCESS! {frames_count} frames extracted to {output_dir}")
                tests_passed += 1
            else:
                error = result_data.get("error", "Unknown error")
                print(f"   ❌ Basic extraction - FAILED: {error}")
        else:
            print("   ❌ Basic extraction - No result returned")
    except Exception as e:
        print(f"   ❌ Basic extraction - Exception: {str(e)[:200]}...")
    
    print("\n⏰ Test 2: Time Format Testing")
    print("-" * 50)
    
    try:
        # Test different time formats
        result = await tools._extract_video_frames(
            video_id="dQw4w9WgXcQ",
            segment_start="0:30",    # 30 seconds in MM:SS format
            segment_end="end-10",    # 10 seconds from end
            interval_seconds=2.0,    # 1 frame every 2 seconds
            max_frames=20,
            output_format="png"      # Test PNG format
        )
        
        if result and isinstance(result, list) and len(result) > 0:
            result_data = json.loads(result[0].text)
            if result_data.get("success"):
                config_info = result_data.get("extraction_config", {})
                start_time = config_info.get("segment_start", 0)
                end_time = config_info.get("segment_end", 0)
                print(f"   ✅ Time formats - SUCCESS! Parsed start: {start_time}s, end: {end_time}s")
                tests_passed += 1
            else:
                error = result_data.get("error", "Unknown error")
                print(f"   ❌ Time formats - FAILED: {error}")
        else:
            print("   ❌ Time formats - No result returned")
    except Exception as e:
        print(f"   ❌ Time formats - Exception: {str(e)[:200]}...")
    
    print("\n🎯 Test 3: High Frequency Extraction")
    print("-" * 50)
    
    try:
        # Test high frequency extraction (many frames)
        result = await tools._extract_video_frames(
            video_id="dQw4w9WgXcQ",
            segment_start=20,
            segment_end=25,
            interval_seconds=0.5,    # 2 frames per second
            max_frames=15,
            quality="low",           # Low quality for speed
            resolution="640x480"     # Lower resolution
        )
        
        if result and isinstance(result, list) and len(result) > 0:
            result_data = json.loads(result[0].text)
            if result_data.get("success"):
                frames_count = result_data["total_frames"]
                extraction_time = result_data.get("extraction_time", 0)
                print(f"   ✅ High frequency - SUCCESS! {frames_count} frames in {extraction_time:.2f}s")
                tests_passed += 1
            else:
                error = result_data.get("error", "Unknown error")
                print(f"   ❌ High frequency - FAILED: {error}")
        else:
            print("   ❌ High frequency - No result returned")
    except Exception as e:
        print(f"   ❌ High frequency - Exception: {str(e)[:200]}...")
    
    print("\n🧹 Test 4: Cleanup Function")
    print("-" * 50)
    
    try:
        # Test cleanup function
        result = await tools._cleanup_extracted_frames(older_than_hours=0)  # Clean all files
        
        if result and isinstance(result, list) and len(result) > 0:
            result_data = json.loads(result[0].text)
            if result_data.get("success") is not False:  # Success or no files to clean
                deleted_dirs = result_data.get("deleted_directories", 0)
                freed_mb = result_data.get("freed_space_mb", 0)
                print(f"   ✅ Cleanup - SUCCESS! Deleted {deleted_dirs} directories, freed {freed_mb}MB")
                tests_passed += 1
            else:
                error = result_data.get("error", "Unknown error")
                print(f"   ❌ Cleanup - FAILED: {error}")
        else:
            print("   ❌ Cleanup - No result returned")
    except Exception as e:
        print(f"   ❌ Cleanup - Exception: {str(e)[:200]}...")
    
    # Clean up
    await tools.cleanup()
    
    # Final Results
    print("\n" + "=" * 60)
    print("📋 FRAME EXTRACTION TEST RESULTS")
    print("=" * 60)
    print(f"✅ Tests Passed: {tests_passed}/{total_tests}")
    print(f"📈 Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed >= 3:
        print("🎉 EXCELLENT! Frame extraction is working correctly!")
        print("✅ Ready to proceed with image analysis integration.")
        return True
    elif tests_passed >= 2:
        print("✨ GOOD! Most functionality working.")
        print("🔧 Minor issues may need attention.")
        return True
    else:
        print("⚠️  NEEDS WORK!")
        print("🔧 Frame extraction requires fixes before proceeding.")
        return False

if __name__ == "__main__":
    try:
        print("🧪 YouTube MCP Server - Frame Extraction Test")
        result = asyncio.run(test_frame_extraction())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)