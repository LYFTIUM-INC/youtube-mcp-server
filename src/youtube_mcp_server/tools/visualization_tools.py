"""
Visualization tools for YouTube MCP Server.
Provides chart creation and data visualization capabilities with creative fallbacks.
"""

import os
import sys
import base64
import io
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

# Import creative visualization fallback
from .creative_visualizations import CreativeVisualizationTools

# Set up logger first
logger = logging.getLogger(__name__)

def _check_visualization_dependencies():
    """Check if visualization dependencies are available."""
    # Due to NumPy 2.x compatibility issues, disable visualization by default
    # Users can enable by setting ENABLE_VISUALIZATION=true in environment
    import os
    if not os.getenv('ENABLE_VISUALIZATION', '').lower() in ('true', '1', 'yes'):
        return False, "Visualization disabled by default due to dependency conflicts. Set ENABLE_VISUALIZATION=true to enable."
    
    try:
        # Try importing in subprocess to avoid polluting main process
        import subprocess
        import sys
        
        # Test imports in isolated process
        test_code = '''
import matplotlib
matplotlib.use('Agg', force=True)
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from wordcloud import WordCloud
print("SUCCESS")
'''
        
        result = subprocess.run(
            [sys.executable, '-c', test_code],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and 'SUCCESS' in result.stdout:
            logger.info("Visualization dependencies verified in subprocess")
            return True, None
        else:
            error_msg = result.stderr or "Unknown subprocess error"
            logger.warning(f"Visualization dependencies failed subprocess test: {error_msg}")
            return False, error_msg
            
    except Exception as e:
        logger.warning(f"Visualization dependency check failed: {e}")
        return False, str(e)


class YouTubeVisualizationTools:
    """Visualization tools for YouTube analytics data with creative fallbacks."""
    
    def __init__(self, output_dir: str, auto_create_artifacts: bool = True):
        """Initialize visualization tools.
        
        Args:
            output_dir: Directory to save visualization files
            auto_create_artifacts: Whether to automatically create HTML artifacts for all visualizations
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize creative visualization tools as fallback
        self.creative_viz = CreativeVisualizationTools(str(self.output_dir))
        
        # Artifact generation settings
        self.auto_create_artifacts = auto_create_artifacts
        
        # Check dependencies when first used
        self._deps_checked = False
        self._deps_available = False
        self._deps_error = None
        
    def _ensure_dependencies(self) -> bool:
        """Ensure visualization dependencies are available."""
        if not self._deps_checked:
            self._deps_available, self._deps_error = _check_visualization_dependencies()
            self._deps_checked = True
            
            if self._deps_available:
                # Import and setup visualization libraries
                import matplotlib.pyplot as plt
                import seaborn as sns
                
                # Configure matplotlib for MCP use
                try:
                    plt.style.use('seaborn-v0_8')
                except:
                    # Fallback if seaborn style not available
                    pass
                plt.rcParams['figure.figsize'] = (12, 8)
                plt.rcParams['figure.dpi'] = 100
                plt.rcParams['savefig.dpi'] = 300
                plt.rcParams['font.size'] = 10
                plt.rcParams['savefig.bbox'] = 'tight'
                
                # Store color schemes
                self.color_palette = sns.color_palette("husl", 10)
                self.engagement_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
            else:
                # Fallback color schemes
                self.color_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
                self.engagement_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        return self._deps_available
    
    def _get_error_response(self, operation: str) -> Dict[str, Any]:
        """Get error response for missing dependencies."""
        return {
            "success": False,
            "error": f"Visualization dependencies not available for {operation}",
            "details": self._deps_error,
            "message": "Please install matplotlib, seaborn, plotly, and wordcloud packages",
            "file_path": None
        }
    
    def create_engagement_chart(self, video_data: List[Dict[str, Any]], chart_type: str = "bar") -> Dict[str, Any]:
        """Create engagement chart visualization."""
        if not self._ensure_dependencies():
            # Fallback to creative visualization
            logger.info("Using creative visualization fallback for engagement chart")
            return self.creative_viz.create_multi_format_visualization(
                data=video_data,
                title=f"Video Engagement Analysis ({chart_type.title()} Chart)"
            )
        
        try:
            import matplotlib.pyplot as plt
            import pandas as pd
            import numpy as np
            
            # Process video data for visualization
            processed_data = []
            for video in video_data:
                stats = video.get('statistics', {})
                snippet = video.get('snippet', {})
                
                # Calculate engagement metrics
                view_count = int(stats.get('viewCount', 0))
                like_count = int(stats.get('likeCount', 0))
                comment_count = int(stats.get('commentCount', 0))
                
                engagement_rate = ((like_count + comment_count) / view_count * 100) if view_count > 0 else 0
                
                processed_data.append({
                    'title': snippet.get('title', 'Unknown')[:50] + '...',
                    'views': view_count,
                    'likes': like_count,
                    'comments': comment_count,
                    'engagement_rate': engagement_rate
                })
            
            df = pd.DataFrame(processed_data)
            
            # Create the chart
            fig, ax = plt.subplots(figsize=(12, 8))
            
            if chart_type == "bar":
                x_pos = np.arange(len(df))
                ax.bar(x_pos, df['engagement_rate'], color=self.engagement_colors[0])
                ax.set_xlabel('Videos')
                ax.set_ylabel('Engagement Rate (%)')
                ax.set_title('Video Engagement Rates')
                ax.set_xticks(x_pos)
                ax.set_xticklabels(df['title'], rotation=45, ha='right')
            
            elif chart_type == "scatter":
                ax.scatter(df['views'], df['engagement_rate'], 
                          color=self.engagement_colors[1], alpha=0.7)
                ax.set_xlabel('View Count')
                ax.set_ylabel('Engagement Rate (%)')
                ax.set_title('Views vs Engagement Rate')
                ax.set_xscale('log')
            
            elif chart_type == "multi":
                # Multi-metric chart
                x_pos = np.arange(len(df))
                width = 0.25
                
                ax.bar(x_pos - width, np.log10(df['views'] + 1), width, 
                       label='Views (log)', color=self.engagement_colors[0])
                ax.bar(x_pos, np.log10(df['likes'] + 1), width, 
                       label='Likes (log)', color=self.engagement_colors[1])
                ax.bar(x_pos + width, np.log10(df['comments'] + 1), width, 
                       label='Comments (log)', color=self.engagement_colors[2])
                
                ax.set_xlabel('Videos')
                ax.set_ylabel('Count (log scale)')
                ax.set_title('Video Engagement Metrics Comparison')
                ax.set_xticks(x_pos)
                ax.set_xticklabels(df['title'], rotation=45, ha='right')
                ax.legend()
            
            # Save chart
            filename = f"engagement_chart_{chart_type}_{len(video_data)}_videos.png"
            file_path = self.output_dir / filename
            plt.tight_layout()
            plt.savefig(file_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            result = {
                "success": True,
                "file_path": str(file_path),
                "chart_type": chart_type,
                "video_count": len(video_data),
                "message": f"Engagement chart created successfully with {len(video_data)} videos"
            }
            
            # Auto-create artifact if enabled
            if self.auto_create_artifacts:
                artifact_result = self._create_engagement_artifact(video_data, chart_type)
                if artifact_result.get('success'):
                    result['artifact'] = artifact_result
                    result['artifact_instruction'] = "📊 Engagement chart artifact ready! You can view it as an interactive HTML visualization."
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create engagement chart: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": None
            }
    
    def create_word_cloud(self, text_data: List[str], source_type: str = "titles") -> Dict[str, Any]:
        """Create word cloud visualization."""
        if not self._ensure_dependencies():
            # Fallback to creative visualization
            logger.info("Using creative visualization fallback for word cloud")
            return self.creative_viz.create_word_cloud_html(
                text_data=text_data,
                source_type=source_type
            )
        
        try:
            from wordcloud import WordCloud
            import matplotlib.pyplot as plt
            
            # Combine all text
            text = " ".join(text_data)
            
            if not text.strip():
                return {
                    "success": False,
                    "error": "No text data provided for word cloud",
                    "file_path": None
                }
            
            # Create word cloud
            wordcloud = WordCloud(
                width=1200,
                height=600,
                background_color='white',
                max_words=100,
                colormap='viridis'
            ).generate(text)
            
            # Plot word cloud
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            ax.set_title(f'Word Cloud from {source_type.title()}', fontsize=16)
            
            # Save word cloud
            filename = f"word_cloud_{source_type}_{len(text_data)}_items.png"
            file_path = self.output_dir / filename
            plt.tight_layout()
            plt.savefig(file_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            result = {
                "success": True,
                "file_path": str(file_path),
                "source_type": source_type,
                "text_count": len(text_data),
                "message": f"Word cloud created successfully from {len(text_data)} {source_type}"
            }
            
            # Auto-create artifact if enabled
            if self.auto_create_artifacts:
                artifact_result = self._create_word_cloud_artifact(text_data, source_type)
                if artifact_result.get('success'):
                    result['artifact'] = artifact_result
                    result['artifact_instruction'] = "☁️ Word cloud artifact ready! You can view it as an interactive HTML visualization."
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create word cloud: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": None
            }
    
    def create_performance_radar(self, video_data: List[Dict[str, Any]], max_videos: int = 5) -> Dict[str, Any]:
        """Create radar chart for video performance comparison."""
        if not self._ensure_dependencies():
            # Fallback to creative visualization
            logger.info("Using creative visualization fallback for performance radar")
            limited_data = video_data[:max_videos] if len(video_data) > max_videos else video_data
            result = self.creative_viz.create_html_chart(
                data=limited_data,
                chart_type="bar"
            )
            
            # Auto-create artifact if enabled
            if self.auto_create_artifacts and result.get('success'):
                artifact_result = self._create_performance_artifact(limited_data, "radar")
                if artifact_result.get('success'):
                    result['artifact'] = artifact_result
                    result['artifact_instruction'] = "🎯 Performance radar artifact ready! You can view it as an interactive HTML visualization."
            
            return result
        
        return {
            "success": False,
            "error": "Radar chart not implemented yet",
            "file_path": None
        }
    
    def create_views_timeline(self, video_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create timeline visualization of video performance."""
        if not self._ensure_dependencies():
            # Fallback to creative visualization
            logger.info("Using creative visualization fallback for views timeline")
            result = self.creative_viz.create_html_chart(
                data=video_data,
                chart_type="line"
            )
            
            # Auto-create artifact if enabled
            if self.auto_create_artifacts and result.get('success'):
                artifact_result = self._create_timeline_artifact(video_data)
                if artifact_result.get('success'):
                    result['artifact'] = artifact_result
                    result['artifact_instruction'] = "📈 Timeline artifact ready! You can view it as an interactive HTML visualization."
            
            return result
        
        return {
            "success": False,
            "error": "Views timeline not implemented yet",
            "file_path": None
        }
    
    def create_comparison_heatmap(self, video_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create heatmap comparing multiple metrics across videos."""
        if not self._ensure_dependencies():
            # Fallback to creative visualization
            logger.info("Using creative visualization fallback for comparison heatmap")
            result = self.creative_viz.create_svg_chart(
                data=video_data,
                chart_type="bar"
            )
            
            # Auto-create artifact if enabled
            if self.auto_create_artifacts and result.get('success'):
                artifact_result = self._create_heatmap_artifact(video_data)
                if artifact_result.get('success'):
                    result['artifact'] = artifact_result
                    result['artifact_instruction'] = "🔥 Heatmap artifact ready! You can view it as an interactive HTML visualization."
            
            return result
        
        return {
            "success": False,
            "error": "Comparison heatmap not implemented yet",
            "file_path": None
        }
    
    def _create_engagement_artifact(self, video_data: List[Dict[str, Any]], chart_type: str) -> Dict[str, Any]:
        """Create HTML artifact for engagement chart visualization."""
        try:
            # Process video data for the artifact
            processed_data = []
            for video in video_data:
                stats = video.get('statistics', {})
                snippet = video.get('snippet', {})
                
                view_count = int(stats.get('viewCount', 0))
                like_count = int(stats.get('likeCount', 0))
                comment_count = int(stats.get('commentCount', 0))
                
                engagement_rate = ((like_count + comment_count) / view_count * 100) if view_count > 0 else 0
                
                processed_data.append({
                    'title': snippet.get('title', 'Unknown'),
                    'views': view_count,
                    'likes': like_count,
                    'comments': comment_count,
                    'engagement_rate': round(engagement_rate, 2)
                })
            
            # Create HTML content
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Video Engagement Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a1a1a; margin-bottom: 30px; text-align: center; }}
        .chart-container {{ position: relative; height: 400px; margin: 30px 0; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }}
        .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .video-list {{ margin-top: 30px; }}
        .video-item {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #28a745; }}
        .video-title {{ font-weight: bold; color: #1a1a1a; margin-bottom: 8px; }}
        .video-stats {{ display: flex; gap: 20px; color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 YouTube Video Engagement Analysis</h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(video_data)}</div>
                <div class="stat-label">Videos Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(d['views'] for d in processed_data):,}</div>
                <div class="stat-label">Total Views</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(d['likes'] for d in processed_data):,}</div>
                <div class="stat-label">Total Likes</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{round(sum(d['engagement_rate'] for d in processed_data) / len(processed_data), 2)}%</div>
                <div class="stat-label">Average Engagement Rate</div>
            </div>
        </div>
        
        <div class="chart-container">
            <canvas id="engagementChart"></canvas>
        </div>
        
        <div class="video-list">
            <h3>📹 Video Details</h3>
            {''.join(f'''
            <div class="video-item">
                <div class="video-title">{video['title']}</div>
                <div class="video-stats">
                    <span>👁️ {video['views']:,} views</span>
                    <span>👍 {video['likes']:,} likes</span>
                    <span>💬 {video['comments']:,} comments</span>
                    <span>📈 {video['engagement_rate']}% engagement</span>
                </div>
            </div>
            ''' for video in processed_data)}
        </div>
    </div>
    
    <script>
        const ctx = document.getElementById('engagementChart').getContext('2d');
        const videoData = {json.dumps(processed_data)};
        
        new Chart(ctx, {{
            type: '{chart_type}',
            data: {{
                labels: videoData.map(v => v.title.length > 30 ? v.title.substring(0, 30) + '...' : v.title),
                datasets: [{{
                    label: 'Engagement Rate (%)',
                    data: videoData.map(v => v.engagement_rate),
                    backgroundColor: '#007bff',
                    borderColor: '#0056b3',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Video Engagement Rates'
                    }},
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Engagement Rate (%)'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Videos'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
            
            # Save artifact
            filename = f"engagement_artifact_{chart_type}_{len(video_data)}_videos.html"
            file_path = self.output_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {
                "success": True,
                "file_path": str(file_path),
                "artifact_type": "engagement_chart",
                "chart_type": chart_type,
                "video_count": len(video_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to create engagement artifact: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_word_cloud_artifact(self, text_data: List[str], source_type: str) -> Dict[str, Any]:
        """Create HTML artifact for word cloud visualization."""
        try:
            # Process text data
            all_text = " ".join(text_data)
            words = all_text.lower().split()
            
            # Count word frequency
            word_freq = {}
            for word in words:
                # Simple cleanup
                word = ''.join(c for c in word if c.isalnum())
                if len(word) > 3:  # Skip short words
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top words
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:50]
            
            # Create HTML content
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Content Word Cloud</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a1a1a; margin-bottom: 30px; text-align: center; }}
        .word-cloud {{ display: flex; flex-wrap: wrap; justify-content: center; align-items: center; gap: 10px; margin: 30px 0; padding: 30px; background: #f8f9fa; border-radius: 12px; min-height: 300px; }}
        .word {{ display: inline-block; margin: 5px; padding: 8px 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 20px; font-weight: bold; transition: transform 0.2s; cursor: default; }}
        .word:hover {{ transform: scale(1.1); }}
        .word-size-1 {{ font-size: 32px; }}
        .word-size-2 {{ font-size: 28px; }}
        .word-size-3 {{ font-size: 24px; }}
        .word-size-4 {{ font-size: 20px; }}
        .word-size-5 {{ font-size: 16px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #667eea; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .word-list {{ margin-top: 30px; }}
        .word-list h3 {{ color: #1a1a1a; }}
        .word-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; }}
        .word-item {{ background: #f8f9fa; padding: 10px; border-radius: 6px; display: flex; justify-content: space-between; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>☁️ Word Cloud from {source_type.title()}</h1>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{len(text_data)}</div>
                <div class="stat-label">Total {source_type.title()}</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(words):,}</div>
                <div class="stat-label">Total Words</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(word_freq)}</div>
                <div class="stat-label">Unique Words</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(top_words)}</div>
                <div class="stat-label">Top Words Shown</div>
            </div>
        </div>
        
        <div class="word-cloud">
            {''.join(f'<span class="word word-size-{min(5, max(1, int(freq/max(word_freq.values(), default=1)*5) + 1))}">{word}</span>' for word, freq in top_words)}
        </div>
        
        <div class="word-list">
            <h3>📊 Top Words by Frequency</h3>
            <div class="word-grid">
                {''.join(f'<div class="word-item"><span>{word}</span><span>{freq}</span></div>' for word, freq in top_words[:20])}
            </div>
        </div>
    </div>
</body>
</html>
"""
            
            # Save artifact
            filename = f"word_cloud_artifact_{source_type}_{len(text_data)}_items.html"
            file_path = self.output_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {
                "success": True,
                "file_path": str(file_path),
                "artifact_type": "word_cloud",
                "source_type": source_type,
                "text_count": len(text_data),
                "unique_words": len(word_freq)
            }
            
        except Exception as e:
            logger.error(f"Failed to create word cloud artifact: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_performance_artifact(self, video_data: List[Dict[str, Any]], chart_type: str) -> Dict[str, Any]:
        """Create HTML artifact for performance comparison visualization."""
        try:
            # Process video data for the artifact
            processed_data = []
            for video in video_data:
                stats = video.get('statistics', {})
                snippet = video.get('snippet', {})
                
                view_count = int(stats.get('viewCount', 0))
                like_count = int(stats.get('likeCount', 0))
                comment_count = int(stats.get('commentCount', 0))
                
                # Calculate normalized scores (0-100)
                max_views = max(int(v.get('statistics', {}).get('viewCount', 0)) for v in video_data)
                max_likes = max(int(v.get('statistics', {}).get('likeCount', 0)) for v in video_data)
                max_comments = max(int(v.get('statistics', {}).get('commentCount', 0)) for v in video_data)
                
                view_score = (view_count / max_views * 100) if max_views > 0 else 0
                like_score = (like_count / max_likes * 100) if max_likes > 0 else 0
                comment_score = (comment_count / max_comments * 100) if max_comments > 0 else 0
                engagement_rate = ((like_count + comment_count) / view_count * 100) if view_count > 0 else 0
                
                processed_data.append({
                    'title': snippet.get('title', 'Unknown'),
                    'views': view_count,
                    'likes': like_count,
                    'comments': comment_count,
                    'view_score': round(view_score, 1),
                    'like_score': round(like_score, 1),
                    'comment_score': round(comment_score, 1),
                    'engagement_rate': round(engagement_rate, 2)
                })
            
            # Create HTML content
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Video Performance Comparison</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a1a1a; margin-bottom: 30px; text-align: center; }}
        .chart-container {{ position: relative; height: 400px; margin: 30px 0; }}
        .performance-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 30px 0; }}
        .performance-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #17a2b8; }}
        .performance-title {{ font-weight: bold; color: #1a1a1a; margin-bottom: 15px; }}
        .metric-bar {{ margin: 10px 0; }}
        .metric-label {{ font-size: 12px; color: #666; margin-bottom: 5px; }}
        .metric-progress {{ background: #e9ecef; border-radius: 10px; height: 8px; }}
        .metric-fill {{ height: 100%; border-radius: 10px; transition: width 0.3s ease; }}
        .metric-views {{ background: linear-gradient(90deg, #007bff, #0056b3); }}
        .metric-likes {{ background: linear-gradient(90deg, #28a745, #1e7e34); }}
        .metric-comments {{ background: linear-gradient(90deg, #ffc107, #e0a800); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Video Performance Comparison</h1>
        
        <div class="chart-container">
            <canvas id="performanceChart"></canvas>
        </div>
        
        <div class="performance-grid">
            {''.join(f'''
            <div class="performance-card">
                <div class="performance-title">{video['title'][:60]}{'...' if len(video['title']) > 60 else ''}</div>
                <div class="metric-bar">
                    <div class="metric-label">Views: {video['views']:,} ({video['view_score']}%)</div>
                    <div class="metric-progress">
                        <div class="metric-fill metric-views" style="width: {video['view_score']}%"></div>
                    </div>
                </div>
                <div class="metric-bar">
                    <div class="metric-label">Likes: {video['likes']:,} ({video['like_score']}%)</div>
                    <div class="metric-progress">
                        <div class="metric-fill metric-likes" style="width: {video['like_score']}%"></div>
                    </div>
                </div>
                <div class="metric-bar">
                    <div class="metric-label">Comments: {video['comments']:,} ({video['comment_score']}%)</div>
                    <div class="metric-progress">
                        <div class="metric-fill metric-comments" style="width: {video['comment_score']}%"></div>
                    </div>
                </div>
                <div style="margin-top: 15px; font-weight: bold; color: #17a2b8;">
                    Engagement Rate: {video['engagement_rate']}%
                </div>
            </div>
            ''' for video in processed_data)}
        </div>
    </div>
    
    <script>
        const ctx = document.getElementById('performanceChart').getContext('2d');
        const videoData = {json.dumps(processed_data)};
        
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: videoData.map(v => v.title.length > 20 ? v.title.substring(0, 20) + '...' : v.title),
                datasets: [
                    {{
                        label: 'Views Score',
                        data: videoData.map(v => v.view_score),
                        backgroundColor: '#007bff'
                    }},
                    {{
                        label: 'Likes Score',
                        data: videoData.map(v => v.like_score),
                        backgroundColor: '#28a745'
                    }},
                    {{
                        label: 'Comments Score',
                        data: videoData.map(v => v.comment_score),
                        backgroundColor: '#ffc107'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Performance Comparison (Normalized Scores)'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        title: {{
                            display: true,
                            text: 'Normalized Score (%)'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
            
            # Save artifact
            filename = f"performance_artifact_{chart_type}_{len(video_data)}_videos.html"
            file_path = self.output_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {
                "success": True,
                "file_path": str(file_path),
                "artifact_type": "performance_comparison",
                "chart_type": chart_type,
                "video_count": len(video_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to create performance artifact: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_timeline_artifact(self, video_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create HTML artifact for timeline visualization."""
        try:
            # Process video data for timeline
            processed_data = []
            for video in video_data:
                stats = video.get('statistics', {})
                snippet = video.get('snippet', {})
                
                # Parse publish date
                published_at = snippet.get('publishedAt', '')
                if published_at:
                    from datetime import datetime
                    try:
                        publish_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                        date_str = publish_date.strftime('%Y-%m-%d')
                    except:
                        date_str = published_at[:10]  # Fallback to first 10 chars
                else:
                    date_str = 'Unknown'
                
                view_count = int(stats.get('viewCount', 0))
                like_count = int(stats.get('likeCount', 0))
                comment_count = int(stats.get('commentCount', 0))
                
                processed_data.append({
                    'title': snippet.get('title', 'Unknown'),
                    'date': date_str,
                    'views': view_count,
                    'likes': like_count,
                    'comments': comment_count
                })
            
            # Sort by date
            processed_data.sort(key=lambda x: x['date'])
            
            # Create HTML content
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Video Timeline</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/date-fns@2.29.3/index.min.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a1a1a; margin-bottom: 30px; text-align: center; }}
        .chart-container {{ position: relative; height: 400px; margin: 30px 0; }}
        .timeline-list {{ margin-top: 30px; }}
        .timeline-item {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #6f42c1; }}
        .timeline-date {{ font-weight: bold; color: #6f42c1; margin-bottom: 8px; }}
        .timeline-title {{ color: #1a1a1a; margin-bottom: 8px; }}
        .timeline-stats {{ display: flex; gap: 20px; color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 Video Timeline Analysis</h1>
        
        <div class="chart-container">
            <canvas id="timelineChart"></canvas>
        </div>
        
        <div class="timeline-list">
            <h3>📅 Chronological Video List</h3>
            {''.join(f'''
            <div class="timeline-item">
                <div class="timeline-date">{video['date']}</div>
                <div class="timeline-title">{video['title']}</div>
                <div class="timeline-stats">
                    <span>👁️ {video['views']:,} views</span>
                    <span>👍 {video['likes']:,} likes</span>
                    <span>💬 {video['comments']:,} comments</span>
                </div>
            </div>
            ''' for video in processed_data)}
        </div>
    </div>
    
    <script>
        const ctx = document.getElementById('timelineChart').getContext('2d');
        const videoData = {json.dumps(processed_data)};
        
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: videoData.map(v => v.date),
                datasets: [{{
                    label: 'Views',
                    data: videoData.map(v => v.views),
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Video Views Over Time'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Views'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Publish Date'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
            
            # Save artifact
            filename = f"timeline_artifact_{len(video_data)}_videos.html"
            file_path = self.output_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {
                "success": True,
                "file_path": str(file_path),
                "artifact_type": "timeline",
                "video_count": len(video_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to create timeline artifact: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_heatmap_artifact(self, video_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create HTML artifact for heatmap visualization."""
        try:
            # Process video data for heatmap
            processed_data = []
            for video in video_data:
                stats = video.get('statistics', {})
                snippet = video.get('snippet', {})
                
                view_count = int(stats.get('viewCount', 0))
                like_count = int(stats.get('likeCount', 0))
                comment_count = int(stats.get('commentCount', 0))
                
                # Calculate engagement metrics
                engagement_rate = ((like_count + comment_count) / view_count * 100) if view_count > 0 else 0
                like_ratio = (like_count / view_count * 100) if view_count > 0 else 0
                comment_ratio = (comment_count / view_count * 100) if view_count > 0 else 0
                
                processed_data.append({
                    'title': snippet.get('title', 'Unknown')[:30] + ('...' if len(snippet.get('title', '')) > 30 else ''),
                    'views': view_count,
                    'likes': like_count,
                    'comments': comment_count,
                    'engagement_rate': round(engagement_rate, 2),
                    'like_ratio': round(like_ratio, 2),
                    'comment_ratio': round(comment_ratio, 2)
                })
            
            # Create HTML content with CSS grid heatmap
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Video Metrics Heatmap</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a1a1a; margin-bottom: 30px; text-align: center; }}
        .heatmap {{ display: grid; grid-template-columns: 200px repeat(4, 1fr); gap: 2px; margin: 30px 0; background: #e9ecef; padding: 10px; border-radius: 8px; }}
        .heatmap-header {{ background: #495057; color: white; padding: 10px; text-align: center; font-weight: bold; }}
        .heatmap-row-header {{ background: #6c757d; color: white; padding: 10px; font-size: 12px; display: flex; align-items: center; }}
        .heatmap-cell {{ padding: 10px; text-align: center; font-size: 12px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; }}
        .legend {{ display: flex; justify-content: center; gap: 20px; margin: 20px 0; }}
        .legend-item {{ display: flex; align-items: center; gap: 5px; }}
        .legend-color {{ width: 20px; height: 20px; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔥 Video Metrics Heatmap</h1>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #d73027;"></div>
                <span>High (75-100%)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #fc8d59;"></div>
                <span>Medium-High (50-75%)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #fee08b;"></div>
                <span>Medium (25-50%)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #e0f3f8;"></div>
                <span>Low (0-25%)</span>
            </div>
        </div>
        
        <div class="heatmap">
            <div class="heatmap-header">Video</div>
            <div class="heatmap-header">Views</div>
            <div class="heatmap-header">Likes %</div>
            <div class="heatmap-header">Comments %</div>
            <div class="heatmap-header">Engagement %</div>
            
            {''.join(f'''
            <div class="heatmap-row-header">{video['title']}</div>
            <div class="heatmap-cell" style="background: {'#d73027' if video['views'] >= max(v['views'] for v in processed_data) * 0.75 else '#fc8d59' if video['views'] >= max(v['views'] for v in processed_data) * 0.5 else '#fee08b' if video['views'] >= max(v['views'] for v in processed_data) * 0.25 else '#e0f3f8'};">{video['views']:,}</div>
            <div class="heatmap-cell" style="background: {'#d73027' if video['like_ratio'] >= 5 else '#fc8d59' if video['like_ratio'] >= 3 else '#fee08b' if video['like_ratio'] >= 1 else '#e0f3f8'};">{video['like_ratio']}%</div>
            <div class="heatmap-cell" style="background: {'#d73027' if video['comment_ratio'] >= 2 else '#fc8d59' if video['comment_ratio'] >= 1 else '#fee08b' if video['comment_ratio'] >= 0.5 else '#e0f3f8'};">{video['comment_ratio']}%</div>
            <div class="heatmap-cell" style="background: {'#d73027' if video['engagement_rate'] >= 7 else '#fc8d59' if video['engagement_rate'] >= 4 else '#fee08b' if video['engagement_rate'] >= 2 else '#e0f3f8'};">{video['engagement_rate']}%</div>
            ''' for video in processed_data)}
        </div>
        
        <div style="margin-top: 30px;">
            <h3>📊 Summary Statistics</h3>
            <p><strong>Total Videos:</strong> {len(processed_data)}</p>
            <p><strong>Average Engagement Rate:</strong> {round(sum(v['engagement_rate'] for v in processed_data) / len(processed_data), 2)}%</p>
            <p><strong>Top Performer:</strong> {max(processed_data, key=lambda x: x['engagement_rate'])['title']} ({max(v['engagement_rate'] for v in processed_data)}%)</p>
            <p><strong>Most Viewed:</strong> {max(processed_data, key=lambda x: x['views'])['title']} ({max(v['views'] for v in processed_data):,} views)</p>
        </div>
    </div>
</body>
</html>
"""
            
            # Save artifact
            filename = f"heatmap_artifact_{len(video_data)}_videos.html"
            file_path = self.output_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {
                "success": True,
                "file_path": str(file_path),
                "artifact_type": "heatmap",
                "video_count": len(video_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to create heatmap artifact: {e}")
            return {
                "success": False,
                "error": str(e)
            }