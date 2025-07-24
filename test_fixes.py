#!/usr/bin/env python3
"""
Test script to verify that the VideoFrameExtractor bug fixes and dependency handling work correctly.
This script tests the core functionality without requiring all advanced dependencies.
"""

import sys
import logging
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dependency_checking():
    """Test that dependency checking functions work correctly."""
    print("\n🔍 Testing dependency checking...")
    
    try:
        from youtube_mcp_server.tools.advanced_trimming import check_dependencies, get_missing_dependencies
        
        deps = check_dependencies()
        missing = get_missing_dependencies()
        
        print(f"✅ Dependency check successful!")
        print(f"   Available: {[k for k, v in deps.items() if v]}")
        print(f"   Missing: {missing}")
        
        return True
    except Exception as e:
        print(f"❌ Dependency check failed: {e}")
        return False

def test_video_frame_extractor():
    """Test that VideoFrameExtractor output_dir bug is fixed."""
    print("\n🎬 Testing VideoFrameExtractor output_dir fix...")
    
    try:
        from youtube_mcp_server.tools.frame_extractor import VideoFrameExtractor
        from youtube_mcp_server.core.config import YouTubeConfig
        
        config = YouTubeConfig()
        extractor = VideoFrameExtractor(config)
        
        # Test both attributes exist
        frames_dir_exists = hasattr(extractor, 'frames_dir')
        output_dir_exists = hasattr(extractor, 'output_dir')
        
        if frames_dir_exists and output_dir_exists:
            print("✅ VideoFrameExtractor attributes fixed!")
            print(f"   frames_dir: {extractor.frames_dir}")
            print(f"   output_dir: {extractor.output_dir}")
            print(f"   Both point to same location: {extractor.frames_dir == extractor.output_dir}")
            return True
        else:
            print(f"❌ Missing attributes - frames_dir: {frames_dir_exists}, output_dir: {output_dir_exists}")
            return False
            
    except Exception as e:
        print(f"❌ VideoFrameExtractor test failed: {e}")
        return False

def test_models_graceful_degradation():
    """Test that models handle missing dependencies gracefully."""
    print("\n🧠 Testing model graceful degradation...")
    
    tests_passed = 0
    total_tests = 0
    
    # Test video models
    try:
        from youtube_mcp_server.models.video_models import VideoAnalyzer, SceneDetector
        
        analyzer = VideoAnalyzer()
        detector = SceneDetector(analyzer)
        
        print("✅ Video models instantiated successfully")
        print(f"   Models loaded: {analyzer.models_loaded}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Video models failed: {e}")
    total_tests += 1
    
    # Test audio models
    try:
        from youtube_mcp_server.models.audio_models import AudioAnalyzer, WhisperTranscriber, SoundClassifier
        
        audio_analyzer = AudioAnalyzer()
        transcriber = WhisperTranscriber()
        classifier = SoundClassifier()
        
        print("✅ Audio models instantiated successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Audio models failed: {e}")
    total_tests += 1
    
    return tests_passed == total_tests

def test_processors_dependency_handling():
    """Test that processors handle missing dependencies correctly."""
    print("\n⚙️ Testing processor dependency handling...")
    
    tests_passed = 0
    total_tests = 0
    
    # Test video processor
    try:
        from youtube_mcp_server.processors.video_processor import VideoProcessor, MOVIEPY_AVAILABLE
        
        processor = VideoProcessor()
        print(f"✅ VideoProcessor instantiated (MoviePy available: {MOVIEPY_AVAILABLE})")
        
        # Test smart_trim with missing dependency
        if not MOVIEPY_AVAILABLE:
            fake_result = processor.smart_trim("fake.mp4", [], "output.mp4")
            if not fake_result.get('success') and 'MoviePy not available' in fake_result.get('error', ''):
                print("✅ VideoProcessor gracefully handles missing MoviePy")
                tests_passed += 1
            else:
                print("❌ VideoProcessor doesn't handle missing MoviePy correctly")
        else:
            print("ℹ️ MoviePy available - skipping graceful degradation test")
            tests_passed += 1
            
    except Exception as e:
        print(f"❌ VideoProcessor test failed: {e}")
    total_tests += 1
    
    # Test audio processor
    try:
        from youtube_mcp_server.processors.audio_processor import AudioProcessor
        
        audio_processor = AudioProcessor()
        print("✅ AudioProcessor instantiated successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ AudioProcessor test failed: {e}")
    total_tests += 1
    
    return tests_passed == total_tests

def test_advanced_trimming_orchestrator():
    """Test that the advanced trimming orchestrator can be instantiated."""
    print("\n🎭 Testing AdvancedTrimmingOrchestrator...")
    
    try:
        from youtube_mcp_server.tools.advanced_trimming import AdvancedTrimmingOrchestrator
        from youtube_mcp_server.infrastructure.cache_manager import CacheManager
        from youtube_mcp_server.infrastructure.error_handler import ErrorHandler
        
        cache_manager = CacheManager(cache_dir=Path("test_cache"), max_size_mb=100)
        error_handler = ErrorHandler()
        
        orchestrator = AdvancedTrimmingOrchestrator(
            cache_manager=cache_manager,
            error_handler=error_handler,
            use_gpu=False  # Don't require GPU for testing
        )
        
        print("✅ AdvancedTrimmingOrchestrator instantiated successfully")
        return True
        
    except Exception as e:
        print(f"❌ AdvancedTrimmingOrchestrator test failed: {e}")
        return False

def test_core_tools_integration():
    """Test that core tools can access the frame extractor without errors."""
    print("\n🔧 Testing core tools integration...")
    
    try:
        from youtube_mcp_server.tools.core_tools import YouTubeAnalyticsTools
        from youtube_mcp_server.core.config import YouTubeConfig
        
        config = YouTubeConfig()
        tools = YouTubeAnalyticsTools(config)
        
        # Check that frame_extractor has the required attributes
        if hasattr(tools.frame_extractor, 'frames_dir') and hasattr(tools.frame_extractor, 'output_dir'):
            print("✅ Core tools can access frame extractor attributes")
            return True
        else:
            print("❌ Core tools missing frame extractor attributes")
            return False
            
    except Exception as e:
        print(f"❌ Core tools integration test failed: {e}")
        return False

def main():
    """Run all tests and report results."""
    print("🧪 Running YouTube MCP Server Fix Verification Tests")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    test_results.append(("Dependency Checking", test_dependency_checking()))
    test_results.append(("VideoFrameExtractor Fix", test_video_frame_extractor()))
    test_results.append(("Model Graceful Degradation", test_models_graceful_degradation()))
    test_results.append(("Processor Dependency Handling", test_processors_dependency_handling()))
    test_results.append(("Advanced Trimming Orchestrator", test_advanced_trimming_orchestrator()))
    test_results.append(("Core Tools Integration", test_core_tools_integration()))
    
    # Report results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! The fixes are working correctly.")
        print("\n📋 Next steps:")
        print("   1. Install missing dependencies: pip install -r requirements.txt")
        print("   2. Test with real video URLs using the MCP server")
        print("   3. Verify advanced trimming features work end-to-end")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please review the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())