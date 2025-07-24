#!/usr/bin/env python3
"""
Debug script to test imports in different environments.
"""

import os
import sys

# Suppress warnings and set minimal environment like MCP Inspector might
os.environ['MPLBACKEND'] = 'Agg'
os.environ['DISPLAY'] = ''

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("🔍 Testing imports in MCP-like environment...")
print(f"Python path: {sys.path[0]}")
print(f"Working directory: {os.getcwd()}")
print()

# Test matplotlib first
print("📊 Testing matplotlib import...")
try:
    import matplotlib
    print(f"   ✅ matplotlib version: {matplotlib.__version__}")
    matplotlib.use('Agg', force=True)
    print("   ✅ Backend set to Agg")
    
    import matplotlib.pyplot as plt
    print("   ✅ pyplot imported")
    
    # Test basic functionality
    fig = plt.figure()
    plt.close()
    print("   ✅ Basic matplotlib functionality works")
    
except Exception as e:
    print(f"   ❌ matplotlib error: {e}")
    print(f"   Error type: {type(e).__name__}")

print()

# Test visualization tools import
print("🎨 Testing visualization tools import...")
try:
    from youtube_mcp_server.tools.visualization_tools import YouTubeVisualizationTools
    print("   ✅ YouTubeVisualizationTools imported successfully")
    
    # Test initialization
    viz_tools = YouTubeVisualizationTools("/tmp/test_viz")
    print("   ✅ YouTubeVisualizationTools initialized")
    
except Exception as e:
    print(f"   ❌ Visualization tools error: {e}")
    print(f"   Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

print()

# Test core tools import
print("🔧 Testing core tools import...")
try:
    from youtube_mcp_server.tools.core_tools import YouTubeMCPTools
    print("   ✅ YouTubeMCPTools imported successfully")
    
except Exception as e:
    print(f"   ❌ Core tools error: {e}")
    print(f"   Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

print()

# Test MCP server import  
print("🖥️  Testing MCP server import...")
try:
    from youtube_mcp_server.core.config import YouTubeMCPConfig
    print("   ✅ YouTubeMCPConfig imported successfully")
    
except Exception as e:
    print(f"   ❌ MCP server error: {e}")
    print(f"   Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

print()
print("🎉 Import debugging completed!")