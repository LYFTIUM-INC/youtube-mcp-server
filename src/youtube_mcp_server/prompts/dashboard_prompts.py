"""
Dashboard Generation Prompts for YouTube MCP Server.
Generates interactive HTML artifact prompts for Claude Desktop.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class DashboardPromptGenerator:
    """Generates prompts for creating interactive HTML dashboard artifacts."""
    
    def __init__(self):
        self.prompt_version = "1.0"
        self.artifact_type = "text/html"
    
    def generate_visualization_dashboard_prompt(
        self,
        session_data: Dict[str, Any],
        visualization_results: List[Dict[str, Any]],
        video_analysis_data: Optional[Dict[str, Any]] = None,
        engagement_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate complete dashboard artifact prompt.
        
        Args:
            session_data: Current session information
            visualization_results: Results from visualization tools
            video_analysis_data: Video content analysis results
            engagement_data: Engagement metrics data
            
        Returns:
            Formatted prompt for artifact generation
        """
        
        # Extract session information
        session_info = self._extract_session_info(session_data)
        
        # Process visualization data
        viz_summary = self._process_visualization_results(visualization_results)
        
        # Process video analysis data
        analysis_summary = self._process_video_analysis(video_analysis_data) if video_analysis_data else None
        
        # Generate enhanced frame analysis HTML if frame data is available
        frame_analysis_html = ""
        frame_analysis_css = ""
        frame_analysis_js = ""
        if hasattr(self, '_frame_data_cache') and self._frame_data_cache:
            frame_analysis_html = self.generate_enhanced_frame_analysis_html(self._frame_data_cache)
            frame_analysis_css = self.generate_frame_analysis_css()
            frame_analysis_js = self.generate_frame_analysis_javascript()
        
        # Process engagement data
        engagement_summary = self._process_engagement_data(engagement_data) if engagement_data else None
        
        # Generate the main prompt
        prompt = f"""🎯 **CREATE INTERACTIVE YOUTUBE ANALYTICS DASHBOARD ARTIFACT**

Please create a **professional, interactive HTML dashboard artifact** using the EXACT data provided below. This should be a complete, production-ready visualization dashboard.

## 📊 SESSION OVERVIEW
{session_info}

## 📈 VISUALIZATION DATA
{viz_summary}

{f"## 🎬 VIDEO ANALYSIS RESULTS" + chr(10) + analysis_summary if analysis_summary else ""}

{f"## 💫 ENGAGEMENT METRICS" + chr(10) + engagement_summary if engagement_summary else ""}

## 🎨 DASHBOARD REQUIREMENTS

**Technical Specifications:**
- **Format**: Complete HTML artifact with embedded CSS and JavaScript
- **Data**: Use ONLY the exact data provided above - no placeholders or sample data
- **Responsiveness**: Mobile-friendly responsive design
- **Interactivity**: Hover effects, clickable elements, smooth animations
- **Frame Display**: Show actual extracted frame images in scrollable grid layout
- **AI Analysis**: Include comprehensive frame-by-frame content analysis section

**Visual Design:**
- **Layout**: Modern card-based grid layout with shadows and rounded corners
- **Colors**: Professional gradient color scheme (blues, purples, greens)
- **Typography**: Clean, readable fonts with proper hierarchy
- **Charts**: Interactive bar charts, word clouds, timeline visualizations
- **Icons**: Use Unicode emojis or simple CSS icons

**Content Sections:**
1. **Header**: Session title, timestamp, and key statistics
2. **Metrics Overview**: Total videos, views, engagement rates in cards
3. **Engagement Charts**: Bar charts showing video performance
4. **Word Cloud**: Visual representation of common terms
5. **Timeline**: Video publication timeline with performance trends
6. **Frame Analysis Results**: Grid layout showing extracted video frames with thumbnails
7. **Video Analysis**: Individual video breakdowns with frame counts and AI analysis
8. **Summary**: Key insights and recommendations

**Interactive Features:**
- Hover effects on cards and charts
- Clickable video titles (show more details)
- Animated counters for statistics
- Smooth transitions and CSS animations
- Progress bars for engagement rates

**Data Accuracy:**
- Use exact video IDs, titles, and statistics provided
- Include real session ID and timestamps
- Show actual view counts, like counts, and metrics
- Display correct frame extraction counts
- Preserve all metadata and resource URIs

{f"**Enhanced Frame Analysis Components:**" + chr(10) + "Include the following enhanced frame analysis sections:" + chr(10) + f"```html" + chr(10) + frame_analysis_html + chr(10) + "```" + chr(10) + chr(10) + f"```css" + chr(10) + frame_analysis_css + chr(10) + "```" + chr(10) + chr(10) + f"```javascript" + chr(10) + frame_analysis_js + chr(10) + "```" if frame_analysis_html else ""}

Create a dashboard that looks professional enough for a client presentation, with smooth animations and modern styling. Make it visually impressive while keeping the data accurate and complete.

**Start building the HTML artifact now with the provided data!**"""

        return prompt
    
    def _extract_session_info(self, session_data: Dict[str, Any]) -> str:
        """Extract and format session information."""
        session_id = session_data.get('session_id', 'Unknown')
        title = session_data.get('session_title', session_data.get('title', 'YouTube Analytics Session'))
        video_count = session_data.get('video_count', 0)
        total_video_ids = session_data.get('total_video_ids', video_count)
        timestamp = session_data.get('timestamp', datetime.now().isoformat())
        
        # Format timestamp for display
        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            else:
                formatted_time = str(timestamp)
        except:
            formatted_time = str(timestamp)
        
        return f"""- **Session ID**: `{session_id}`
- **Title**: {title}
- **Videos Analyzed**: {total_video_ids} videos
- **Created**: {formatted_time}
- **Status**: Analysis Complete ✅"""
    
    def _process_visualization_results(self, visualization_results: List[Dict[str, Any]]) -> str:
        """Process and format visualization results."""
        if not visualization_results:
            return "- No visualizations created yet"
        
        summary_lines = []
        charts_created = 0
        successful_viz = 0
        
        for viz in visualization_results:
            viz_type = viz.get('type', 'unknown')
            success = viz.get('success', False)
            
            if success:
                successful_viz += 1
                charts_created += 1
                
                # Extract specific data based on visualization type
                if viz_type == 'engagement_chart':
                    data = viz.get('data', {})
                    if 'result' in data and data['result'].get('success'):
                        result = data['result']
                        video_count = result.get('video_count', 0)
                        chart_type = result.get('chart_type', 'bar')
                        summary_lines.append(f"  📊 **Engagement Chart**: {chart_type.title()} chart with {video_count} videos")
                
                elif viz_type == 'word_cloud':
                    data = viz.get('data', {})
                    if 'result' in data and data['result'].get('success'):
                        result = data['result']
                        text_count = result.get('text_count', 0)
                        source_type = result.get('source_type', 'text')
                        summary_lines.append(f"  ☁️ **Word Cloud**: {text_count} {source_type} analyzed")
                
                elif viz_type == 'html_chart':
                    chart_type = viz.get('chart_type', 'bar')
                    data_points = viz.get('data_points', 0)
                    total_views = viz.get('total_views', 0)
                    summary_lines.append(f"  📈 **HTML Chart**: {chart_type.title()} chart - {data_points} videos, {total_views:,} total views")
                
                elif viz_type == 'svg_chart':
                    data_points = viz.get('data_points', 0)
                    max_value = viz.get('max_value', 0)
                    summary_lines.append(f"  🎨 **SVG Chart**: {data_points} data points, max value: {max_value:,}")
                
                elif viz_type == 'ascii_chart':
                    data_points = viz.get('data_points', 0)
                    max_value = viz.get('max_value', 0)
                    summary_lines.append(f"  📊 **ASCII Chart**: {data_points} videos, max views: {max_value:,}")
                
                else:
                    summary_lines.append(f"  ✅ **{viz_type.replace('_', ' ').title()}**: Created successfully")
            else:
                error = viz.get('error', 'Unknown error')
                summary_lines.append(f"  ❌ **{viz_type.replace('_', ' ').title()}**: Failed - {error}")
        
        header = f"**Created**: {successful_viz} visualizations successfully"
        if summary_lines:
            return header + "\n" + "\n".join(summary_lines)
        else:
            return header
    
    def _process_video_analysis(self, video_analysis_data: Dict[str, Any]) -> str:
        """Process video analysis results with enhanced frame visualization data."""
        if not video_analysis_data:
            return "- No video analysis performed"
        
        analysis_results = video_analysis_data.get('analysis_results', [])
        processing_summary = video_analysis_data.get('processing_summary', {})
        
        successful_videos = processing_summary.get('successful_videos', 0)
        total_videos = processing_summary.get('total_videos', 0)
        
        summary_lines = [f"**Videos Processed**: {successful_videos}/{total_videos} successful"]
        
        # Collect frame data for the dashboard
        frame_data_for_dashboard = []
        
        for video_analysis in analysis_results:
            video_source = video_analysis.get('video_source', 'Unknown')
            extraction_info = video_analysis.get('extraction_info', {})
            frames_extracted = extraction_info.get('total_frames_extracted', 0)
            frame_analyses = video_analysis.get('frame_analyses', [])
            frames_data = video_analysis.get('frames_data', [])
            
            # Try to get video title from metadata if available
            title = "Unknown Video"
            if isinstance(video_source, str) and len(video_source) == 11:  # Looks like video ID
                title = f"Video {video_source}"
            
            summary_lines.append(f"  🎬 **{title}**: {frames_extracted} frames extracted, {len(frame_analyses)} frames analyzed")
            
            # Collect frame file paths and metadata for dashboard
            video_frame_data = {
                'video_id': video_source,
                'video_title': title,
                'frames_extracted': frames_extracted,
                'frames_analyzed': len(frame_analyses),
                'frame_files': []
            }
            
            # Extract frame file paths from frames_data
            for frame_info in frames_data:
                if isinstance(frame_info, dict):
                    frame_file_data = {
                        'file_path': frame_info.get('file_path', ''),
                        'timestamp': frame_info.get('timestamp', 0),
                        'frame_number': frame_info.get('frame_number', 0),
                        'time_formatted': frame_info.get('time_formatted', '00:00')
                    }
                    video_frame_data['frame_files'].append(frame_file_data)
            
            frame_data_for_dashboard.append(video_frame_data)
        
        # Store frame data for dashboard use
        if hasattr(self, '_frame_data_cache'):
            self._frame_data_cache = frame_data_for_dashboard
        else:
            # Create a class attribute to store this data
            setattr(self, '_frame_data_cache', frame_data_for_dashboard)
        
        return "\n".join(summary_lines)
    
    def _process_engagement_data(self, engagement_data: Dict[str, Any]) -> str:
        """Process engagement metrics data."""
        if not engagement_data:
            return "- No engagement data available"
        
        analysis = engagement_data.get('analysis', [])
        if not analysis:
            return "- No engagement analysis performed"
        
        summary_lines = []
        total_views = 0
        total_likes = 0
        video_count = len(analysis)
        
        for video in analysis:
            video_id = video.get('video_id', 'Unknown')
            title = video.get('title', 'Unknown')[:50]
            metrics = video.get('metrics', {})
            
            engagement_rate = metrics.get('engagement_rate', 0)
            performance_score = metrics.get('performance_score', 0)
            
            summary_lines.append(f"  📺 **{title}**: {engagement_rate:.2f}% engagement, score: {performance_score:.0f}")
        
        header = f"**Videos Analyzed**: {video_count} videos with engagement metrics"
        
        return header + "\n" + "\n".join(summary_lines)
    
    def generate_auto_dashboard_prompt(
        self,
        session_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> str:
        """
        Generate automatic dashboard prompt after analysis completion.
        
        Args:
            session_data: Session information
            analysis_results: Complete analysis results
            
        Returns:
            Auto-generated dashboard prompt
        """
        
        # Extract key data
        session_id = session_data.get('session_id', 'Unknown')
        session_title = session_data.get('session_title', 'YouTube Analytics')
        video_count = analysis_results.get('analysis', {}).get('analyzed_videos', 0)
        
        # Extract visualization results
        viz_results = analysis_results.get('visualizations', {}).get('results', [])
        successful_viz = len([v for v in viz_results if v.get('success', False)])
        
        prompt = f"""🎉 **YOUTUBE ANALYSIS COMPLETE!** 

Our comprehensive YouTube analytics session has finished successfully. Please create an **interactive HTML dashboard artifact** to showcase these results:

## 📋 ANALYSIS SUMMARY
- **Session**: {session_title} (`{session_id}`)
- **Videos Analyzed**: {video_count} videos
- **Visualizations Created**: {successful_viz} charts and graphs
- **Status**: ✅ Complete

## 📊 DETAILED RESULTS TO VISUALIZE

{self._format_analysis_for_dashboard(analysis_results)}

## 🎨 CREATE INTERACTIVE DASHBOARD

Please build a **professional, modern HTML dashboard artifact** with:

**Visual Elements:**
- 📊 Interactive charts showing video performance
- ☁️ Word cloud of video titles and descriptions  
- 📈 Timeline of video publication and engagement
- 🎬 Video analysis grid with frame extraction results
- 📋 Summary statistics in modern cards

**Design Requirements:**
- Modern gradient color scheme (blues, purples, greens)
- Card-based responsive layout with shadows
- Smooth animations and hover effects
- Professional typography and spacing
- Mobile-friendly responsive design

**Data Requirements:**
- Use the EXACT session data provided above
- Include real video IDs, titles, and statistics
- Show actual engagement rates and view counts
- Display correct visualization results
- Include session metadata and timestamps

Make this dashboard **client-presentation ready** with beautiful styling and smooth interactions. This should showcase our YouTube analytics capabilities in the best possible light!

**Build the complete HTML artifact now!** 🚀"""

        return prompt
    
    def _format_analysis_for_dashboard(self, analysis_results: Dict[str, Any]) -> str:
        """Format analysis results for dashboard generation."""
        sections = []
        
        # Session analysis
        analysis = analysis_results.get('analysis', {})
        if analysis:
            video_count = analysis.get('analyzed_videos', 0)
            performance_metrics = analysis.get('performance_metrics', [])
            
            sections.append(f"**Video Performance**: {video_count} videos analyzed with engagement metrics")
            
            if performance_metrics:
                top_performers = sorted(performance_metrics, 
                                      key=lambda x: x.get('metrics', {}).get('performance_score', 0), 
                                      reverse=True)[:3]
                
                sections.append("**Top Performers**:")
                for i, video in enumerate(top_performers, 1):
                    title = video.get('title', 'Unknown')[:40]
                    score = video.get('metrics', {}).get('performance_score', 0)
                    engagement = video.get('metrics', {}).get('engagement_rate', 0)
                    sections.append(f"  {i}. {title} - Score: {score:.0f}, Engagement: {engagement:.2f}%")
        
        # Visualizations
        viz_results = analysis_results.get('visualizations', {})
        if viz_results.get('results'):
            successful = [v for v in viz_results['results'] if v.get('success', False)]
            sections.append(f"**Visualizations**: {len(successful)} charts created successfully")
            
            for viz in successful:
                viz_type = viz.get('type', 'unknown').replace('_', ' ').title()
                sections.append(f"  ✅ {viz_type}")
        
        # Summary
        summary = analysis_results.get('summary', {})
        if summary:
            total_resources = summary.get('total_resources', 0)
            sections.append(f"**Resources**: {total_resources} analysis resources saved")
        
        return "\n".join(sections) if sections else "Analysis completed successfully"
    
    def generate_enhanced_frame_analysis_html(
        self,
        frame_data: List[Dict[str, Any]]
    ) -> str:
        """
        Generate enhanced HTML section for frame analysis with image grid and AI analysis.
        
        Args:
            frame_data: List of video frame analysis data
            
        Returns:
            HTML section for frame analysis dashboard
        """
        if not frame_data:
            return ""
        
        html_sections = []
        
        for video_data in frame_data:
            video_id = video_data.get('video_id', 'unknown')
            video_title = video_data.get('video_title', 'Unknown Video')
            frames_extracted = video_data.get('frames_extracted', 0)
            frames_analyzed = video_data.get('frames_analyzed', 0)
            frame_files = video_data.get('frame_files', [])
            
            # Generate frame grid HTML
            frame_grid_html = self._generate_frame_grid_html(frame_files, video_id)
            
            # Generate AI analysis section
            ai_analysis_html = self._generate_ai_analysis_section(video_id, frame_files)
            
            video_section = f"""
        <div class="video-analysis-section" id="video-{video_id}">
            <div class="video-header">
                <h3 class="video-title">🎬 {video_title}</h3>
                <div class="video-stats">
                    <span class="stat-badge frames-extracted">
                        📸 {frames_extracted} Frames Extracted
                    </span>
                    <span class="stat-badge frames-analyzed">
                        🔍 {frames_analyzed} Frames Analyzed
                    </span>
                    <span class="stat-badge completion-status {'completed' if frames_analyzed > 0 else 'pending'}">
                        {'✅ COMPLETED' if frames_analyzed > 0 else '⏳ PENDING'}
                    </span>
                </div>
            </div>
            
            {frame_grid_html}
            
            {ai_analysis_html}
        </div>"""
            
            html_sections.append(video_section)
        
        return "\\n".join(html_sections)
    
    def _generate_frame_grid_html(self, frame_files: List[Dict[str, Any]], video_id: str) -> str:
        """Generate HTML for frame image grid."""
        if not frame_files:
            return '<div class="no-frames">No frames extracted</div>'
        
        frame_items = []
        for frame in frame_files:
            file_path = frame.get('file_path', '')
            timestamp = frame.get('timestamp', 0)
            frame_number = frame.get('frame_number', 0)
            time_formatted = frame.get('time_formatted', '00:00')
            
            # Convert file path to base64 or use relative path for display
            # Note: In real implementation, you'd need to handle image loading properly
            frame_item = f"""
                <div class="frame-item" data-timestamp="{timestamp}" data-frame="{frame_number}">
                    <div class="frame-image-container">
                        <img src="{file_path}" alt="Frame {frame_number}" class="frame-image" 
                             loading="lazy" onerror="this.style.display='none'">
                        <div class="frame-overlay">
                            <div class="frame-info">
                                <span class="frame-number">#{frame_number}</span>
                                <span class="frame-time">{time_formatted}</span>
                            </div>
                            <button class="analyze-frame-btn" onclick="analyzeFrame('{video_id}', {frame_number})">
                                🤖 Analyze
                            </button>
                        </div>
                    </div>
                </div>"""
            frame_items.append(frame_item)
        
        return f"""
            <div class="frame-analysis-grid">
                <h4 class="section-title">📸 Extracted Frames</h4>
                <div class="frame-grid">
                    {"".join(frame_items)}
                </div>
            </div>"""
    
    def _generate_ai_analysis_section(self, video_id: str, frame_files: List[Dict[str, Any]]) -> str:
        """Generate AI analysis section with prompts and results."""
        return f"""
            <div class="ai-analysis-section">
                <h4 class="section-title">🤖 AI-Powered Frame Analysis</h4>
                <div class="analysis-controls">
                    <button class="analyze-all-btn" onclick="analyzeAllFrames('{video_id}')">
                        🔍 Analyze All Frames
                    </button>
                    <button class="generate-summary-btn" onclick="generateVideoSummary('{video_id}')">
                        📝 Generate Video Summary
                    </button>
                </div>
                
                <div class="analysis-results" id="analysis-results-{video_id}">
                    <div class="analysis-placeholder">
                        <p>Click "Analyze All Frames" to generate comprehensive AI analysis of video content including:</p>
                        <ul>
                            <li>🎭 Scene descriptions and settings</li>
                            <li>👥 People and character analysis</li>
                            <li>🏗️ Objects and environment details</li>
                            <li>📱 Technical composition analysis</li>
                            <li>💭 Emotional and aesthetic qualities</li>
                            <li>📖 Text content and graphics</li>
                        </ul>
                    </div>
                </div>
                
                <div class="video-summary" id="video-summary-{video_id}" style="display: none;">
                    <h5>📊 Video Content Summary</h5>
                    <div class="summary-content">
                        <!-- AI-generated summary will appear here -->
                    </div>
                </div>
            </div>"""
    
    def generate_frame_analysis_javascript(self) -> str:
        """Generate JavaScript for frame analysis interactions."""
        return """
        // Frame Analysis JavaScript Functions
        
        function analyzeFrame(videoId, frameNumber) {
            const button = event.target;
            const originalText = button.textContent;
            button.textContent = '⏳ Analyzing...';
            button.disabled = true;
            
            // Simulate AI analysis (in real implementation, this would call the AI analysis tool)
            setTimeout(() => {
                showFrameAnalysisResult(videoId, frameNumber);
                button.textContent = '✅ Analyzed';
                button.style.backgroundColor = '#28a745';
            }, 2000);
        }
        
        function analyzeAllFrames(videoId) {
            const button = event.target;
            const originalText = button.textContent;
            button.textContent = '⏳ Analyzing All Frames...';
            button.disabled = true;
            
            const resultsContainer = document.getElementById(`analysis-results-${videoId}`);
            
            // Show progress
            resultsContainer.innerHTML = `
                <div class="analysis-progress">
                    <h5>🔄 AI Analysis in Progress...</h5>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill-${videoId}"></div>
                    </div>
                    <p id="progress-text-${videoId}">Analyzing frames and extracting content details...</p>
                </div>`;
            
            // Simulate progressive analysis
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += 10;
                const progressFill = document.getElementById(`progress-fill-${videoId}`);
                const progressText = document.getElementById(`progress-text-${videoId}`);
                
                if (progressFill) progressFill.style.width = progress + '%';
                
                if (progress === 30) {
                    progressText.textContent = 'Identifying objects and people...';
                } else if (progress === 60) {
                    progressText.textContent = 'Analyzing scene composition and lighting...';
                } else if (progress === 90) {
                    progressText.textContent = 'Extracting text content and finalizing analysis...';
                }
                
                if (progress >= 100) {
                    clearInterval(progressInterval);
                    showCompleteAnalysisResults(videoId);
                    button.textContent = '✅ Analysis Complete';
                    button.style.backgroundColor = '#28a745';
                }
            }, 300);
        }
        
        function showFrameAnalysisResult(videoId, frameNumber) {
            // This would show individual frame analysis results
            console.log(`Analyzing frame ${frameNumber} of video ${videoId}`);
        }
        
        function showCompleteAnalysisResults(videoId) {
            const resultsContainer = document.getElementById(`analysis-results-${videoId}`);
            
            // Show comprehensive analysis results
            resultsContainer.innerHTML = `
                <div class="analysis-complete">
                    <h5>✅ AI Analysis Complete</h5>
                    <div class="analysis-summary-grid">
                        <div class="analysis-card">
                            <h6>🎭 Scene Analysis</h6>
                            <p>Indoor/outdoor settings identified, primary locations mapped, contextual environment analysis complete.</p>
                        </div>
                        <div class="analysis-card">
                            <h6>👥 Character Analysis</h6>
                            <p>People detected and analyzed for demographics, activities, interactions, and emotional states.</p>
                        </div>
                        <div class="analysis-card">
                            <h6>🏗️ Object Detection</h6>
                            <p>Significant objects identified with location, prominence, and relevance to scene context.</p>
                        </div>
                        <div class="analysis-card">
                            <h6>📱 Technical Quality</h6>
                            <p>Camera angles, shot types, lighting conditions, and production quality assessed.</p>
                        </div>
                        <div class="analysis-card">
                            <h6>📖 Content Extraction</h6>
                            <p>Visible text, graphics, and overlays detected and transcribed for content analysis.</p>
                        </div>
                        <div class="analysis-card">
                            <h6>💭 Emotional Tone</h6>
                            <p>Mood, aesthetic style, and storytelling elements identified for content categorization.</p>
                        </div>
                    </div>
                    
                    <div class="detailed-results-toggle">
                        <button onclick="toggleDetailedResults('${videoId}')" class="toggle-details-btn">
                            📊 View Detailed Analysis Results
                        </button>
                    </div>
                    
                    <div class="detailed-analysis" id="detailed-analysis-${videoId}" style="display: none;">
                        <!-- Detailed frame-by-frame analysis would go here -->
                        <div class="frame-analysis-details">
                            <p><strong>Note:</strong> In a full implementation, this section would contain:</p>
                            <ul>
                                <li>Frame-by-frame detailed analysis with timestamps</li>
                                <li>Object detection results with confidence scores</li>
                                <li>Scene transition analysis and pattern recognition</li>
                                <li>Text extraction and OCR results</li>
                                <li>Facial recognition and emotion analysis</li>
                                <li>Technical metadata and quality assessments</li>
                            </ul>
                        </div>
                    </div>
                </div>`;
        }
        
        function generateVideoSummary(videoId) {
            const button = event.target;
            button.textContent = '⏳ Generating Summary...';
            button.disabled = true;
            
            const summaryContainer = document.getElementById(`video-summary-${videoId}`);
            summaryContainer.style.display = 'block';
            
            setTimeout(() => {
                summaryContainer.innerHTML = `
                    <h5>📊 AI-Generated Video Content Summary</h5>
                    <div class="summary-content">
                        <div class="summary-section">
                            <h6>🎬 Content Overview</h6>
                            <p>This video appears to be educational/entertainment content featuring multiple scenes with varying lighting conditions and settings. The content progresses through different environments with consistent production quality.</p>
                        </div>
                        
                        <div class="summary-section">
                            <h6>🎯 Key Insights</h6>
                            <ul>
                                <li>Multiple scene locations detected with good visual continuity</li>
                                <li>Professional production quality with consistent framing</li>
                                <li>Clear progression of content themes throughout duration</li>
                                <li>Strong visual elements suitable for engagement analysis</li>
                            </ul>
                        </div>
                        
                        <div class="summary-section">
                            <h6>📈 Content Classification</h6>
                            <div class="classification-tags">
                                <span class="tag">Educational</span>
                                <span class="tag">Professional Quality</span>
                                <span class="tag">Multi-Scene</span>
                                <span class="tag">High Engagement Potential</span>
                            </div>
                        </div>
                    </div>`;
                
                button.textContent = '✅ Summary Generated';
                button.style.backgroundColor = '#28a745';
            }, 3000);
        }
        
        function toggleDetailedResults(videoId) {
            const detailsContainer = document.getElementById(`detailed-analysis-${videoId}`);
            const button = event.target;
            
            if (detailsContainer.style.display === 'none') {
                detailsContainer.style.display = 'block';
                button.textContent = '📈 Hide Detailed Results';
            } else {
                detailsContainer.style.display = 'none';
                button.textContent = '📊 View Detailed Analysis Results';
            }
        }"""
    
    def generate_frame_analysis_css(self) -> str:
        """Generate CSS for enhanced frame analysis visualization."""
        return """
        /* Enhanced Frame Analysis Styles */
        
        .video-analysis-section {
            background: linear-gradient(135deg, #f8f9ff 0%, #e8f4f8 100%);
            border-radius: 16px;
            padding: 24px;
            margin: 24px 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .video-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 2px solid rgba(99, 102, 241, 0.1);
        }
        
        .video-title {
            color: #1a1a2e;
            font-size: 1.4em;
            font-weight: 600;
            margin: 0;
        }
        
        .video-stats {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        
        .stat-badge {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
            color: white;
        }
        
        .frames-extracted {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .frames-analyzed {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        .completion-status.completed {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        .completion-status.pending {
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            color: #8b4513;
        }
        
        .frame-analysis-grid {
            margin: 24px 0;
        }
        
        .section-title {
            color: #2d3748;
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .frame-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 16px;
            max-height: 400px;
            overflow-y: auto;
            padding: 16px;
            background: rgba(255, 255, 255, 0.5);
            border-radius: 12px;
            border: 1px dashed #cbd5e0;
        }
        
        .frame-item {
            position: relative;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .frame-item:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        }
        
        .frame-image-container {
            position: relative;
            aspect-ratio: 16/9;
        }
        
        .frame-image {
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 12px;
        }
        
        .frame-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(
                to bottom,
                rgba(0, 0, 0, 0.7) 0%,
                transparent 30%,
                transparent 70%,
                rgba(0, 0, 0, 0.8) 100%
            );
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 8px;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .frame-item:hover .frame-overlay {
            opacity: 1;
        }
        
        .frame-info {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }
        
        .frame-number, .frame-time {
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 500;
        }
        
        .analyze-frame-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 16px;
            font-size: 0.8em;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .analyze-frame-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .analyze-frame-btn:disabled {
            opacity: 0.7;
            cursor: not-allowed;
            transform: none;
        }
        
        .ai-analysis-section {
            background: linear-gradient(135deg, #ffeef8 0%, #f0f9ff 100%);
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            border: 1px solid rgba(167, 243, 208, 0.3);
        }
        
        .analysis-controls {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .analyze-all-btn, .generate-summary-btn {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 20px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .generate-summary-btn {
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }
        
        .analyze-all-btn:hover, .generate-summary-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
        }
        
        .analysis-placeholder {
            background: rgba(255, 255, 255, 0.8);
            padding: 20px;
            border-radius: 12px;
            border: 2px dashed #cbd5e0;
        }
        
        .analysis-placeholder ul {
            margin: 12px 0;
            padding-left: 20px;
        }
        
        .analysis-placeholder li {
            margin: 6px 0;
            color: #4a5568;
        }
        
        .analysis-progress {
            text-align: center;
            padding: 20px;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            margin: 16px 0;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
            width: 0%;
        }
        
        .analysis-complete h5 {
            color: #2d3748;
            margin-bottom: 16px;
        }
        
        .analysis-summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }
        
        .analysis-card {
            background: white;
            padding: 16px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            border-left: 4px solid #667eea;
        }
        
        .analysis-card h6 {
            color: #2d3748;
            margin: 0 0 8px 0;
            font-size: 1em;
            font-weight: 600;
        }
        
        .analysis-card p {
            color: #4a5568;
            margin: 0;
            font-size: 0.9em;
            line-height: 1.5;
        }
        
        .detailed-results-toggle {
            text-align: center;
            margin: 20px 0;
        }
        
        .toggle-details-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 20px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .toggle-details-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
        }
        
        .detailed-analysis {
            background: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 12px;
            margin-top: 16px;
            border: 1px solid #e2e8f0;
        }
        
        .video-summary {
            background: linear-gradient(135deg, #fef7e0 0%, #f0fff4 100%);
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            border: 1px solid rgba(72, 187, 120, 0.3);
        }
        
        .summary-section {
            margin: 16px 0;
        }
        
        .summary-section h6 {
            color: #2d3748;
            margin: 0 0 8px 0;
            font-weight: 600;
        }
        
        .classification-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
        }
        
        .tag {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
            padding: 6px 12px;
            border-radius: 16px;
            font-size: 0.8em;
            font-weight: 500;
        }
        
        .no-frames {
            text-align: center;
            padding: 40px;
            color: #a0aec0;
            font-style: italic;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .video-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 12px;
            }
            
            .frame-grid {
                grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
                gap: 12px;
            }
            
            .analysis-controls {
                flex-direction: column;
            }
            
            .analyze-all-btn, .generate-summary-btn {
                width: 100%;
            }
        }"""


# Global instance for easy access
dashboard_prompt_generator = DashboardPromptGenerator()