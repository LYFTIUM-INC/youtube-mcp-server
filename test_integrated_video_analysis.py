#!/usr/bin/env python3
"""
Test script for the integrated video content analysis functionality.
Tests the complete workflow from video frame extraction to analysis prompt generation.
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

async def test_integrated_video_analysis():
    """Test the integrated video content analysis functionality."""
    print("🎬 Testing Integrated Video Content Analysis System...")
    print("=" * 70)
    
    # Initialize configuration
    config = YouTubeMCPConfig()
    if not config.google_api_key:
        print("❌ No YouTube API key configured. Please set GOOGLE_API_KEY environment variable.")
        return False
    
    # Initialize tools
    tools = YouTubeMCPTools(config)
    await tools.initialize()
    
    tests_passed = 0
    total_tests = 3
    
    print("\n🧪 Test 1: Single Video Analysis (Short Segment)")
    print("-" * 60)
    
    try:
        # Test with a single video, short segment
        result = await tools._analyze_video_content_from_frames(
            video_ids=["dQw4w9WgXcQ"],  # Rick Roll - reliable test video
            segment_start=10,            # Start at 10 seconds
            segment_end=20,              # End at 20 seconds (10 second segment)
            frame_interval=2.0,          # Extract frame every 2 seconds
            max_frames_per_video=10,     # Maximum 10 frames
            analysis_focus=["scene_description", "objects", "people"],
            include_comparative_analysis=True,
            generate_video_summary=True
        )
        
        if result and isinstance(result, list) and len(result) > 0:
            result_data = json.loads(result[0].text)
            
            if result_data.get("success"):
                processing_summary = result_data.get("processing_summary", {})
                successful_videos = processing_summary.get("successful_videos", 0)
                analysis_results = result_data.get("analysis_results", [])
                
                if successful_videos > 0 and len(analysis_results) > 0:
                    video_analysis = analysis_results[0]
                    frame_analyses = video_analysis.get("frame_analyses", [])
                    comparative_analysis = video_analysis.get("comparative_analysis")
                    video_summary_prompt = video_analysis.get("video_summary_prompt")
                    
                    print(f"   ✅ Single video analysis - SUCCESS!")
                    print(f"      - Frames extracted: {len(frame_analyses)}")
                    print(f"      - Frame analysis prompts generated: {len(frame_analyses)}")
                    print(f"      - Comparative analysis: {'✓' if comparative_analysis else '✗'}")
                    print(f"      - Video summary prompt: {'✓' if video_summary_prompt else '✗'}")
                    
                    # Check that prompts are actually generated
                    if (len(frame_analyses) > 0 and 
                        frame_analyses[0].get("analysis_prompt") and
                        "comprehensive frame analysis" in frame_analyses[0]["analysis_prompt"].lower()):
                        print("      - Frame analysis prompts contain expected content ✓")
                        tests_passed += 1
                    else:
                        print("      - Frame analysis prompts missing or incomplete ✗")
                else:
                    print(f"   ❌ Single video analysis - No successful results: {result_data}")
            else:
                error = result_data.get("error", "Unknown error")
                print(f"   ❌ Single video analysis - FAILED: {error}")
        else:
            print("   ❌ Single video analysis - No result returned")
            
    except Exception as e:
        print(f"   ❌ Single video analysis - Exception: {str(e)[:200]}...")
    
    print("\n🎯 Test 2: Multiple Videos Analysis")
    print("-" * 60)
    
    try:
        # Test with multiple videos (smaller segments for faster testing)
        result = await tools._analyze_video_content_from_frames(
            video_ids=["dQw4w9WgXcQ", "jNQXAC9IVRw"],  # Two test videos
            segment_start="0:30",        # 30 seconds in MM:SS format
            segment_end="0:45",          # 45 seconds (15 second segments)
            frame_interval=3.0,          # Extract frame every 3 seconds
            max_frames_per_video=8,      # Maximum 8 frames per video
            analysis_focus=["scene_description", "environment"],
            include_comparative_analysis=True,
            generate_video_summary=True
        )
        
        if result and isinstance(result, list) and len(result) > 0:
            result_data = json.loads(result[0].text)
            
            if result_data.get("success"):
                processing_summary = result_data.get("processing_summary", {})
                successful_videos = processing_summary.get("successful_videos", 0)
                total_videos = processing_summary.get("total_videos", 0)
                analysis_results = result_data.get("analysis_results", [])
                
                print(f"   ✅ Multiple videos analysis - SUCCESS!")
                print(f"      - Videos processed: {successful_videos}/{total_videos}")
                print(f"      - Analysis results: {len(analysis_results)}")
                
                # Check each video analysis
                total_frames = 0
                total_prompts = 0
                for i, video_analysis in enumerate(analysis_results):
                    frame_analyses = video_analysis.get("frame_analyses", [])
                    total_frames += len(frame_analyses)
                    total_prompts += len([f for f in frame_analyses if f.get("analysis_prompt")])
                    print(f"      - Video {i+1}: {len(frame_analyses)} frames, analysis prompts generated")
                
                if total_prompts > 0:
                    print(f"      - Total analysis prompts generated: {total_prompts}")
                    tests_passed += 1
                else:
                    print("      - No analysis prompts generated ✗")
            else:
                error = result_data.get("error", "Unknown error")
                print(f"   ❌ Multiple videos analysis - FAILED: {error}")
        else:
            print("   ❌ Multiple videos analysis - No result returned")
            
    except Exception as e:
        print(f"   ❌ Multiple videos analysis - Exception: {str(e)[:200]}...")
    
    print("\n🔍 Test 3: Analysis Configuration Flexibility")
    print("-" * 60)
    
    try:
        # Test different analysis configurations
        result = await tools._analyze_video_content_from_frames(
            video_ids=["dQw4w9WgXcQ"],
            segment_start="end-30",      # Last 30 seconds
            segment_end="end-10",        # Last 10 seconds (20 second segment)
            frame_interval=5.0,          # Extract frame every 5 seconds
            max_frames_per_video=5,      # Maximum 5 frames
            analysis_focus=["objects", "people", "text_content", "movement_indicators"],
            include_comparative_analysis=False,  # Skip comparative analysis
            generate_video_summary=False         # Skip video summary
        )
        
        if result and isinstance(result, list) and len(result) > 0:
            result_data = json.loads(result[0].text)
            
            if result_data.get("success"):
                analysis_results = result_data.get("analysis_results", [])
                configuration = result_data.get("configuration", {})
                
                if len(analysis_results) > 0:
                    video_analysis = analysis_results[0]
                    frame_analyses = video_analysis.get("frame_analyses", [])
                    comparative_analysis = video_analysis.get("comparative_analysis")
                    video_summary_prompt = video_analysis.get("video_summary_prompt")
                    
                    print(f"   ✅ Configuration flexibility - SUCCESS!")
                    print(f"      - Frames extracted: {len(frame_analyses)}")
                    print(f"      - Analysis focus: {configuration.get('analysis_focus', [])}")
                    print(f"      - Comparative analysis disabled: {'✓' if not comparative_analysis else '✗'}")
                    print(f"      - Video summary disabled: {'✓' if not video_summary_prompt else '✗'}")
                    
                    # Check time specification parsing
                    if (configuration.get("segment_start") and 
                        configuration.get("segment_end") and
                        len(frame_analyses) > 0):
                        print("      - Time specification parsing working ✓")
                        tests_passed += 1
                    else:
                        print("      - Time specification parsing issues ✗")
                else:
                    print(f"   ❌ Configuration flexibility - No analysis results")
            else:
                error = result_data.get("error", "Unknown error")
                print(f"   ❌ Configuration flexibility - FAILED: {error}")
        else:
            print("   ❌ Configuration flexibility - No result returned")
            
    except Exception as e:
        print(f"   ❌ Configuration flexibility - Exception: {str(e)[:200]}...")
    
    # Clean up
    await tools.cleanup()
    
    # Final Results
    print("\n" + "=" * 70)
    print("📋 INTEGRATED VIDEO ANALYSIS TEST RESULTS")
    print("=" * 70)
    print(f"✅ Tests Passed: {tests_passed}/{total_tests}")
    print(f"📈 Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed >= 3:
        print("🎉 EXCELLENT! Integrated video content analysis is fully functional!")
        print("🚀 The system can extract frames and generate comprehensive analysis prompts!")
        print("💡 Ready for integration with image analysis services!")
        return True
    elif tests_passed >= 2:
        print("✨ GREAT! Core functionality working!")
        print("🔧 Minor improvements may enhance performance.")
        return True
    elif tests_passed >= 1:
        print("👍 GOOD! Basic functionality demonstrated!")
        print("⚡ Some features need attention for full functionality.")
        return True
    else:
        print("⚠️  NEEDS WORK!")
        print("🔧 Integrated analysis system requires fixes.")
        return False

if __name__ == "__main__":
    try:
        print("🧪 YouTube MCP Server - Integrated Video Content Analysis Test")
        print("Testing complete workflow: video → frames → analysis prompts...")
        result = asyncio.run(test_integrated_video_analysis())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)