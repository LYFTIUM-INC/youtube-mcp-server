#!/usr/bin/env python3
"""
Test script for the improved YouTube video downloader.

This script tests the video downloader with the videos that were previously failing
and demonstrates the fixes applied.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.append('src')

from youtube_mcp_server.tools.video_downloader import VideoDownloader


async def test_video_downloads():
    """Test video downloads with previously failing videos."""
    
    print("🚀 Testing YouTube Video Downloader with Enhanced Fallbacks")
    print("=" * 60)
    
    # Initialize downloader
    downloader = VideoDownloader(download_dir='test_downloads')
    
    # Test videos that were previously failing
    test_videos = [
        {'id': 'rfscVS0vtbw', 'name': 'Learn Python - Full Course for Beginners'},
        {'id': '_uQrJ0TkZlc', 'name': 'Python Full Course for Beginners'},
        {'id': '3BaTzLk9rp0', 'name': 'I LEARNED CODING IN A DAY #shorts'}
    ]
    
    results = []
    
    for i, video in enumerate(test_videos, 1):
        print(f"\n📹 Test {i}/3: {video['name']}")
        print(f"   Video ID: {video['id']}")
        print("-" * 50)
        
        try:
            # Test with worst quality for faster downloads
            result = await downloader.download_video(
                video_id=video['id'],
                quality='worst',
                audio_only=False
            )
            
            if result['success']:
                file_size_mb = result['file_size'] / (1024 * 1024) if result['file_size'] else 0
                print(f"✅ SUCCESS")
                print(f"   Title: {result['title']}")
                print(f"   Format: {result['format']}")
                print(f"   File Size: {file_size_mb:.1f} MB")
                print(f"   Download Time: {result['download_time']:.1f}s")
                
                results.append({
                    'video_id': video['id'],
                    'status': 'success',
                    'title': result['title'],
                    'file_size_mb': round(file_size_mb, 1),
                    'download_time': round(result['download_time'], 1)
                })
            else:
                print(f"❌ FAILED")
                print(f"   Error: {result['error_message']}")
                
                results.append({
                    'video_id': video['id'],
                    'status': 'failed',
                    'error': result['error_message']
                })
                
        except Exception as e:
            print(f"💥 EXCEPTION: {str(e)}")
            results.append({
                'video_id': video['id'],
                'status': 'exception',
                'error': str(e)
            })
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 DOWNLOAD TEST SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for r in results if r['status'] == 'success')
    total = len(results)
    
    print(f"Success Rate: {successful}/{total} ({successful/total*100:.0f}%)")
    
    if successful > 0:
        total_size = sum(r.get('file_size_mb', 0) for r in results if r['status'] == 'success')
        avg_time = sum(r.get('download_time', 0) for r in results if r['status'] == 'success') / successful
        print(f"Total Downloaded: {total_size:.1f} MB")
        print(f"Average Time: {avg_time:.1f}s per video")
    
    print("\nDetailed Results:")
    for result in results:
        status_emoji = "✅" if result['status'] == 'success' else "❌"
        print(f"  {status_emoji} {result['video_id']}: {result['status'].upper()}")
        if result['status'] == 'success':
            print(f"     Size: {result['file_size_mb']}MB, Time: {result['download_time']}s")
    
    # Get downloader statistics
    stats = downloader.get_stats()
    print(f"\n📈 Downloader Statistics:")
    print(f"   Total Attempts: {stats['attempts']}")
    print(f"   Success Rate: {stats['success_rate']:.1%}")
    print(f"   Average Download Time: {stats['avg_download_time']:.1f}s")
    
    return results


async def test_format_detection():
    """Test format detection for videos."""
    
    print("\n" + "=" * 60)
    print("🔍 TESTING FORMAT DETECTION")
    print("=" * 60)
    
    downloader = VideoDownloader(download_dir='test_downloads')
    
    test_video = 'rfscVS0vtbw'  # A video we know works
    
    try:
        formats_result = await downloader.get_download_formats(test_video)
        
        if formats_result['success']:
            formats = formats_result['formats']
            print(f"✅ Found {len(formats)} available formats")
            
            # Show sample formats
            print("\nSample formats:")
            video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('resolution') != 'audio only'][:5]
            audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('resolution') == 'audio only'][:3]
            
            print("  Video formats:")
            for fmt in video_formats:
                print(f"    {fmt.get('format_id')}: {fmt.get('resolution')} - {fmt.get('ext')} ({fmt.get('vcodec')})")
            
            print("  Audio formats:")
            for fmt in audio_formats:
                print(f"    {fmt.get('format_id')}: {fmt.get('ext')} - {fmt.get('acodec')}")
        else:
            print(f"❌ Failed to get formats: {formats_result['error']}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")


async def main():
    """Run all tests."""
    
    print("YouTube MCP Server - Video Downloader Test Suite")
    print("Testing fixes for download failures")
    print()
    
    # Test downloads
    download_results = await test_video_downloads()
    
    # Test format detection
    await test_format_detection()
    
    # Cleanup
    print("\n🧹 Cleaning up test files...")
    import shutil
    test_dir = Path('test_downloads')
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print("   Test files cleaned up")
    
    print("\n✨ All tests completed!")
    
    # Return summary for integration testing
    successful_downloads = sum(1 for r in download_results if r['status'] == 'success')
    total_downloads = len(download_results)
    
    if successful_downloads == total_downloads:
        print(f"🎉 ALL TESTS PASSED! ({successful_downloads}/{total_downloads} videos downloaded successfully)")
        return True
    else:
        print(f"⚠️  PARTIAL SUCCESS: {successful_downloads}/{total_downloads} videos downloaded successfully")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)