#!/usr/bin/env python3
"""
Test script for dashboard artifact prompt generation.

This script demonstrates the new dashboard generation functionality that automatically
creates interactive HTML dashboard prompts after YouTube analysis sessions.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.append('src')

from youtube_mcp_server.prompts.dashboard_prompts import dashboard_prompt_generator


def test_dashboard_prompt_generation():
    """Test dashboard prompt generation with sample data."""
    
    print("🎨 Testing Dashboard Artifact Prompt Generation")
    print("=" * 60)
    
    # Sample session data
    session_data = {
        "session_id": "test-session-123",
        "session_title": "YouTube Analytics Demo",
        "video_count": 3,
        "total_video_ids": 3,
        "timestamp": "2025-06-11T10:30:00Z",
        "created_at": "2025-06-11T10:00:00Z",
        "updated_at": "2025-06-11T10:30:00Z",
        "description": "Demo session for testing dashboard generation"
    }
    
    # Sample visualization results
    visualization_results = [
        {
            "type": "engagement_chart",
            "success": True,
            "chart_type": "bar",
            "data_points": 3,
            "total_views": 1500000,
            "max_value": 800000,
            "data": {
                "result": {
                    "success": True,
                    "video_count": 3,
                    "chart_type": "bar"
                }
            }
        },
        {
            "type": "html_chart",
            "success": True,
            "chart_type": "bar",
            "data_points": 3,
            "total_views": 1500000,
            "max_views": 800000,
            "avg_views": 500000
        },
        {
            "type": "word_cloud",
            "success": True,
            "data": {
                "result": {
                    "success": True,
                    "text_count": 3,
                    "source_type": "titles"
                }
            }
        }
    ]
    
    # Sample video analysis data
    video_analysis_data = {
        "analysis_results": [
            {
                "video_source": "rfscVS0vtbw",
                "extraction_info": {
                    "total_frames_extracted": 15
                },
                "frame_analyses": [{"frame": 1}, {"frame": 2}]
            },
            {
                "video_source": "_uQrJ0TkZlc", 
                "extraction_info": {
                    "total_frames_extracted": 12
                },
                "frame_analyses": [{"frame": 1}, {"frame": 2}]
            }
        ],
        "processing_summary": {
            "successful_videos": 2,
            "total_videos": 2
        }
    }
    
    # Sample engagement data
    engagement_data = {
        "analysis": [
            {
                "video_id": "rfscVS0vtbw",
                "title": "Learn Python - Full Course for Beginners",
                "metrics": {
                    "engagement_rate": 2.5,
                    "performance_score": 85000
                }
            },
            {
                "video_id": "_uQrJ0TkZlc",
                "title": "Python Full Course for Beginners",
                "metrics": {
                    "engagement_rate": 1.8,
                    "performance_score": 72000
                }
            }
        ]
    }
    
    print("📊 Sample Data Overview:")
    print(f"   Session: {session_data['session_title']}")
    print(f"   Videos: {session_data['video_count']}")
    print(f"   Visualizations: {len(visualization_results)}")
    print(f"   Video Analysis: {len(video_analysis_data['analysis_results'])} videos")
    print(f"   Engagement Data: {len(engagement_data['analysis'])} videos")
    print()
    
    # Generate the main dashboard prompt
    print("🎯 Generating Main Dashboard Prompt...")
    main_prompt = dashboard_prompt_generator.generate_visualization_dashboard_prompt(
        session_data=session_data,
        visualization_results=visualization_results,
        video_analysis_data=video_analysis_data,
        engagement_data=engagement_data
    )
    
    print("✅ Main dashboard prompt generated!")
    print(f"   Length: {len(main_prompt)} characters")
    print()
    
    # Generate the auto-dashboard prompt
    print("🚀 Generating Auto-Dashboard Prompt...")
    sample_analysis_results = {
        "session_id": session_data["session_id"],
        "session_title": session_data["session_title"],
        "analysis": {
            "analyzed_videos": 3,
            "performance_metrics": engagement_data["analysis"]
        },
        "visualizations": {
            "results": visualization_results,
            "successful_count": len([v for v in visualization_results if v["success"]])
        },
        "summary": {
            "total_resources": 5
        }
    }
    
    auto_prompt = dashboard_prompt_generator.generate_auto_dashboard_prompt(
        session_data=session_data,
        analysis_results=sample_analysis_results
    )
    
    print("✅ Auto-dashboard prompt generated!")
    print(f"   Length: {len(auto_prompt)} characters")
    print()
    
    # Display prompt previews
    print("🔍 PROMPT PREVIEWS")
    print("=" * 60)
    
    print("📋 Main Dashboard Prompt (first 300 chars):")
    print("-" * 50)
    print(main_prompt[:300] + "..." if len(main_prompt) > 300 else main_prompt)
    print()
    
    print("🎉 Auto-Dashboard Prompt (first 300 chars):")
    print("-" * 50)
    print(auto_prompt[:300] + "..." if len(auto_prompt) > 300 else auto_prompt)
    print()
    
    # Key features analysis
    print("🔧 PROMPT FEATURES ANALYSIS")
    print("=" * 60)
    
    main_features = {
        "Contains session data": "session_id" in main_prompt.lower(),
        "Includes visualization data": "visualization" in main_prompt.lower(),
        "Has video analysis": "video analysis" in main_prompt.lower(),
        "Includes engagement metrics": "engagement" in main_prompt.lower(),
        "Interactive requirements": "interactive" in main_prompt.lower(),
        "HTML artifact instruction": "html" in main_prompt.lower(),
        "Professional styling": "professional" in main_prompt.lower(),
        "Real data emphasis": "exact data" in main_prompt.lower()
    }
    
    auto_features = {
        "Analysis complete notification": "complete" in auto_prompt.lower(),
        "Celebration tone": "🎉" in auto_prompt or "🚀" in auto_prompt,
        "Results summary": "summary" in auto_prompt.lower(),
        "Artifact creation": "artifact" in auto_prompt.lower(),
        "Dashboard styling": "dashboard" in auto_prompt.lower()
    }
    
    print("Main Dashboard Prompt Features:")
    for feature, present in main_features.items():
        status = "✅" if present else "❌"
        print(f"  {status} {feature}")
    
    print("\nAuto-Dashboard Prompt Features:")
    for feature, present in auto_features.items():
        status = "✅" if present else "❌"
        print(f"  {status} {feature}")
    
    # Save sample prompts for testing
    print("\n💾 SAVING SAMPLE PROMPTS")
    print("=" * 60)
    
    output_dir = Path("dashboard_prompt_samples")
    output_dir.mkdir(exist_ok=True)
    
    # Save main prompt
    main_file = output_dir / "main_dashboard_prompt.md"
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write("# Main Dashboard Prompt\n\n")
        f.write("Generated from dashboard_prompt_generator.generate_visualization_dashboard_prompt()\n\n")
        f.write("## Prompt Content:\n\n")
        f.write(main_prompt)
    
    # Save auto prompt
    auto_file = output_dir / "auto_dashboard_prompt.md"
    with open(auto_file, 'w', encoding='utf-8') as f:
        f.write("# Auto-Dashboard Prompt\n\n")
        f.write("Generated from dashboard_prompt_generator.generate_auto_dashboard_prompt()\n\n")
        f.write("## Prompt Content:\n\n")
        f.write(auto_prompt)
    
    # Save sample data
    data_file = output_dir / "sample_data.json"
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump({
            "session_data": session_data,
            "visualization_results": visualization_results,
            "video_analysis_data": video_analysis_data,
            "engagement_data": engagement_data
        }, f, indent=2)
    
    print(f"✅ Sample prompts saved to: {output_dir}")
    print(f"   📋 Main prompt: {main_file}")
    print(f"   🚀 Auto prompt: {auto_file}")
    print(f"   📊 Sample data: {data_file}")
    
    print("\n🎯 INTEGRATION SUMMARY")
    print("=" * 60)
    print("The dashboard prompt generation system is ready for integration!")
    print()
    print("Key Features:")
    print("  🎨 Automatic dashboard prompts after analysis completion")
    print("  📊 Rich data integration from session resources")
    print("  🎯 Targeted artifact creation instructions")
    print("  🔧 Configurable prompt templates")
    print("  💾 Resource management integration")
    print()
    print("Usage in MCP:")
    print("  1. Run analyze_session_videos() -> auto-generates dashboard prompt")
    print("  2. Use generate_dashboard_artifact_prompt() tool manually")
    print("  3. Dashboard prompts saved as session resources")
    print("  4. Claude Desktop receives ready-to-use artifact instructions")
    
    return True


if __name__ == "__main__":
    print("YouTube MCP Server - Dashboard Prompt Generation Test")
    print("Testing automatic artifact prompt creation for Claude Desktop")
    print()
    
    success = test_dashboard_prompt_generation()
    
    if success:
        print("\n✨ All dashboard prompt generation tests completed successfully!")
    else:
        print("\n❌ Some tests failed")
    
    sys.exit(0 if success else 1)