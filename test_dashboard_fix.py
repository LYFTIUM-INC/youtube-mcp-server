#!/usr/bin/env python3
"""
Test script to verify the dashboard generation fix.
Tests the generate_dashboard_artifact_prompt function with actual session data.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.append('src')

from youtube_mcp_server.core.config import YouTubeMCPConfig
from youtube_mcp_server.tools.core_tools import YouTubeMCPTools


async def test_dashboard_generation_fix():
    """Test the fixed dashboard generation function."""
    
    print("🔧 Testing Dashboard Generation Bug Fix")
    print("=" * 60)
    
    try:
        # Initialize the MCP tools
        config = YouTubeMCPConfig()
        tools = YouTubeMCPTools(config)
        await tools.initialize()
        
        print("✅ MCP Tools initialized successfully")
        
        # List available sessions
        sessions_result = await tools._list_analysis_sessions()
        sessions_data = json.loads(sessions_result[0].text)
        
        if not sessions_data.get('success', False):
            print("❌ No sessions available for testing")
            return False
        
        sessions = sessions_data.get('sessions', [])
        if not sessions:
            print("❌ No sessions found")
            return False
        
        print(f"📋 Found {len(sessions)} available sessions")
        
        # Use the first session for testing
        test_session = sessions[0]
        session_id = test_session['session_id']
        session_title = test_session['title']
        video_count = test_session['video_count']
        
        print(f"🎯 Testing with session: {session_title}")
        print(f"   Session ID: {session_id}")
        print(f"   Video Count: {video_count}")
        print()
        
        # Test the dashboard generation function
        print("🎨 Testing generate_dashboard_artifact_prompt...")
        
        try:
            dashboard_result = await tools._generate_dashboard_artifact_prompt(
                session_id=session_id,
                include_video_analysis=True,
                include_engagement_metrics=True,
                dashboard_title="Test Dashboard",
                auto_generate=True
            )
            
            # Parse the result
            dashboard_data = json.loads(dashboard_result[0].text)
            
            if dashboard_data.get('success', False):
                print("✅ Dashboard generation succeeded!")
                print(f"   Dashboard Title: {dashboard_data.get('dashboard_title')}")
                print(f"   Visualization Count: {dashboard_data.get('visualization_count')}")
                print(f"   Has Video Analysis: {dashboard_data.get('has_video_analysis')}")
                print(f"   Has Engagement Data: {dashboard_data.get('has_engagement_data')}")
                
                # Check if prompt was generated
                dashboard_prompt = dashboard_data.get('dashboard_prompt')
                if dashboard_prompt:
                    print(f"   Prompt Length: {len(dashboard_prompt)} characters")
                    print("   ✅ Dashboard prompt generated successfully")
                    
                    # Show preview of prompt
                    print(f"   📋 Prompt Preview (first 200 chars):")
                    print(f"      {dashboard_prompt[:200]}...")
                    
                    # Check for auto-generation instruction
                    if dashboard_data.get('instruction'):
                        print(f"   📌 Instruction: {dashboard_data.get('instruction')}")
                    
                    return True
                else:
                    print("   ❌ No dashboard prompt was generated")
                    return False
            else:
                error = dashboard_data.get('error', 'Unknown error')
                print(f"❌ Dashboard generation failed: {error}")
                return False
                
        except Exception as e:
            print(f"❌ Exception during dashboard generation: {e}")
            print(f"   Error type: {type(e).__name__}")
            return False
        
    except Exception as e:
        print(f"💥 Setup error: {e}")
        return False
    
    finally:
        try:
            await tools.cleanup()
        except:
            pass


async def test_prompt_components():
    """Test individual components of the prompt generation system."""
    
    print("\n" + "=" * 60)
    print("🧪 Testing Prompt Generation Components")
    print("=" * 60)
    
    # Test the dashboard prompt generator directly
    from youtube_mcp_server.prompts.dashboard_prompts import dashboard_prompt_generator
    
    # Sample data for testing
    sample_session_data = {
        "session_id": "test-session",
        "session_title": "Test Session",
        "video_count": 3,
        "timestamp": "2025-06-11T10:30:00Z"
    }
    
    sample_viz_results = [
        {
            "type": "engagement_chart",
            "success": True,
            "data": {"chart_type": "bar", "data_points": 3}
        }
    ]
    
    try:
        # Test main prompt generation
        print("🔍 Testing main prompt generation...")
        main_prompt = dashboard_prompt_generator.generate_visualization_dashboard_prompt(
            session_data=sample_session_data,
            visualization_results=sample_viz_results
        )
        
        if main_prompt and len(main_prompt) > 100:
            print("✅ Main prompt generation works")
            print(f"   Length: {len(main_prompt)} characters")
        else:
            print("❌ Main prompt generation failed")
            return False
        
        # Test auto prompt generation
        print("🚀 Testing auto prompt generation...")
        sample_analysis_results = {
            "analysis": {"analyzed_videos": 3},
            "visualizations": {"results": sample_viz_results}
        }
        
        auto_prompt = dashboard_prompt_generator.generate_auto_dashboard_prompt(
            session_data=sample_session_data,
            analysis_results=sample_analysis_results
        )
        
        if auto_prompt and len(auto_prompt) > 100:
            print("✅ Auto prompt generation works")
            print(f"   Length: {len(auto_prompt)} characters")
        else:
            print("❌ Auto prompt generation failed")
            return False
        
        print("✅ All prompt generation components working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        return False


async def main():
    """Run all tests."""
    
    print("YouTube MCP Server - Dashboard Generation Fix Test")
    print("Testing fix for 'str' object has no attribute 'get' error")
    print()
    
    # Test the main dashboard generation
    main_success = await test_dashboard_generation_fix()
    
    # Test individual components
    component_success = await test_prompt_components()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    overall_success = main_success and component_success
    
    if overall_success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Dashboard generation bug has been fixed")
        print("✅ Prompt generation components work correctly") 
        print("✅ Function can access session resources properly")
        print("✅ No more 'str' object attribute errors")
    else:
        print("❌ SOME TESTS FAILED")
        if not main_success:
            print("❌ Main dashboard generation still has issues")
        if not component_success:
            print("❌ Prompt generation components have problems")
    
    print(f"\nOverall Result: {'SUCCESS' if overall_success else 'FAILURE'}")
    
    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)