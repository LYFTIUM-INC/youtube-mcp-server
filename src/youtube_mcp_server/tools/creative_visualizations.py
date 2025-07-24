"""
Creative Visualization Tools for YouTube MCP Server.
Dependency-free visualization solutions using multiple approaches.
"""

import os
import json
import base64
import html
import math
import colorsys
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime


class CreativeVisualizationTools:
    """Creative visualization tools that work without heavy dependencies."""
    
    def __init__(self, output_dir: str):
        """Initialize with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def create_ascii_chart(self, data: List[Dict[str, Any]], title: str = "Chart") -> Dict[str, Any]:
        """Create ASCII art chart visualization."""
        try:
            if not data:
                return {"success": False, "error": "No data provided"}
            
            # Extract numeric data for charting
            values = []
            labels = []
            
            for item in data:
                # Try to extract view counts or other numeric metrics
                if "statistics" in item:
                    stats = item["statistics"]
                    view_count = int(stats.get("viewCount", 0))
                    values.append(view_count)
                    title_text = item.get("snippet", {}).get("title", "Unknown")
                    labels.append(title_text[:20] + "..." if len(title_text) > 20 else title_text)
                elif "view_count" in item:
                    values.append(int(item["view_count"]))
                    labels.append(item.get("title", "Unknown")[:20])
            
            if not values:
                return {"success": False, "error": "No numeric data found"}
            
            # Create ASCII bar chart
            max_val = max(values)
            max_width = 50
            
            chart_lines = [f"📊 {title}", "=" * (len(title) + 4), ""]
            
            for i, (label, value) in enumerate(zip(labels, values)):
                if max_val > 0:
                    bar_width = int((value / max_val) * max_width)
                    bar = "█" * bar_width + "░" * (max_width - bar_width)
                else:
                    bar = "░" * max_width
                
                # Format value with appropriate units
                if value >= 1_000_000:
                    value_str = f"{value/1_000_000:.1f}M"
                elif value >= 1_000:
                    value_str = f"{value/1_000:.1f}K"
                else:
                    value_str = str(value)
                
                chart_lines.append(f"{label:<25} |{bar}| {value_str}")
            
            chart_text = "\n".join(chart_lines)
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ascii_chart_{timestamp}.txt"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(chart_text)
            
            return {
                "success": True,
                "type": "ascii_chart",
                "file_path": str(filepath),
                "chart_text": chart_text,
                "data_points": len(values),
                "max_value": max_val
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_html_chart(self, data: List[Dict[str, Any]], chart_type: str = "bar") -> Dict[str, Any]:
        """Create interactive HTML chart using Chart.js."""
        try:
            if not data:
                return {"success": False, "error": "No data provided"}
            
            # Extract data
            values = []
            labels = []
            colors = []
            
            for i, item in enumerate(data):
                # Extract metrics
                if "statistics" in item:
                    stats = item["statistics"]
                    view_count = int(stats.get("viewCount", 0))
                    values.append(view_count)
                    title_text = item.get("snippet", {}).get("title", "Unknown")
                    labels.append(title_text[:30])
                elif "view_count" in item:
                    values.append(int(item["view_count"]))
                    labels.append(item.get("title", "Unknown")[:30])
                
                # Generate colors
                hue = (i * 137.5) % 360  # Golden angle for nice color distribution
                rgb = colorsys.hsv_to_rgb(hue/360, 0.7, 0.9)
                color = f"rgb({int(rgb[0]*255)}, {int(rgb[1]*255)}, {int(rgb[2]*255)})"
                colors.append(color)
            
            # Create HTML with Chart.js
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Analytics Chart</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .chart-container {{ position: relative; height: 500px; margin: 20px 0; }}
        h1 {{ color: #333; text-align: center; }}
        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .stat {{ text-align: center; padding: 10px; background: #f0f0f0; border-radius: 5px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #e74c3c; }}
        .stat-label {{ font-size: 14px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 YouTube Video Analytics</h1>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{len(values)}</div>
                <div class="stat-label">Videos</div>
            </div>
            <div class="stat">
                <div class="stat-value">{sum(values):,}</div>
                <div class="stat-label">Total Views</div>
            </div>
            <div class="stat">
                <div class="stat-value">{max(values) if values else 0:,}</div>
                <div class="stat-label">Max Views</div>
            </div>
            <div class="stat">
                <div class="stat-value">{int(sum(values)/len(values)) if values else 0:,}</div>
                <div class="stat-label">Avg Views</div>
            </div>
        </div>
        
        <div class="chart-container">
            <canvas id="myChart"></canvas>
        </div>
        
        <p style="text-align: center; color: #666; font-size: 12px;">
            Generated by YouTube MCP Server • {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </p>
    </div>

    <script>
        const ctx = document.getElementById('myChart').getContext('2d');
        const myChart = new Chart(ctx, {{
            type: '{chart_type}',
            data: {{
                labels: {json.dumps(labels)},
                datasets: [{{
                    label: 'Views',
                    data: {json.dumps(values)},
                    backgroundColor: {json.dumps(colors)},
                    borderColor: {json.dumps(colors)},
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Video Performance Analysis'
                    }},
                    legend: {{
                        display: {chart_type != 'pie'}
                    }}
                }},
                scales: {chart_type != 'pie' and '''{{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            callback: function(value) {{
                                if (value >= 1000000) return (value/1000000).toFixed(1) + 'M';
                                if (value >= 1000) return (value/1000).toFixed(1) + 'K';
                                return value;
                            }}
                        }}
                    }}
                }}''' or '{}'}
            }}
        }});
    </script>
</body>
</html>
"""
            
            # Save HTML file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chart_{chart_type}_{timestamp}.html"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {
                "success": True,
                "type": "html_chart",
                "chart_type": chart_type,
                "file_path": str(filepath),
                "data_points": len(values),
                "total_views": sum(values),
                "max_views": max(values) if values else 0,
                "avg_views": int(sum(values)/len(values)) if values else 0
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_svg_chart(self, data: List[Dict[str, Any]], chart_type: str = "bar") -> Dict[str, Any]:
        """Create SVG chart visualization."""
        try:
            if not data:
                return {"success": False, "error": "No data provided"}
            
            # Extract data
            values = []
            labels = []
            
            for item in data:
                if "statistics" in item:
                    stats = item["statistics"]
                    view_count = int(stats.get("viewCount", 0))
                    values.append(view_count)
                    title_text = item.get("snippet", {}).get("title", "Unknown")
                    labels.append(title_text[:20])
                elif "view_count" in item:
                    values.append(int(item["view_count"]))
                    labels.append(item.get("title", "Unknown")[:20])
            
            if not values:
                return {"success": False, "error": "No numeric data found"}
            
            # SVG dimensions
            width = 800
            height = 600
            margin = 60
            chart_width = width - 2 * margin
            chart_height = height - 2 * margin
            
            max_val = max(values)
            
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="barGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style="stop-color:#e74c3c;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#c0392b;stop-opacity:1" />
        </linearGradient>
    </defs>
    
    <!-- Background -->
    <rect width="{width}" height="{height}" fill="#f8f9fa"/>
    
    <!-- Title -->
    <text x="{width//2}" y="30" text-anchor="middle" font-family="Arial" font-size="20" font-weight="bold" fill="#2c3e50">
        📊 YouTube Video Performance
    </text>
    
    <!-- Chart area border -->
    <rect x="{margin}" y="{margin}" width="{chart_width}" height="{chart_height}" 
          fill="none" stroke="#ddd" stroke-width="1"/>
'''
            
            if chart_type == "bar":
                # Bar chart
                bar_width = chart_width / len(values) * 0.8
                bar_spacing = chart_width / len(values)
                
                for i, (value, label) in enumerate(zip(values, labels)):
                    if max_val > 0:
                        bar_height = (value / max_val) * chart_height
                    else:
                        bar_height = 0
                    
                    x = margin + i * bar_spacing + bar_spacing * 0.1
                    y = margin + chart_height - bar_height
                    
                    # Bar
                    svg_content += f'''
    <rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" 
          fill="url(#barGradient)" stroke="#c0392b" stroke-width="1"/>
    
    <!-- Value label -->
    <text x="{x + bar_width/2}" y="{y - 5}" text-anchor="middle" font-family="Arial" font-size="10" fill="#2c3e50">
        {value if value < 1000 else f"{value//1000}K" if value < 1000000 else f"{value//1000000:.1f}M"}
    </text>
    
    <!-- X-axis label -->
    <text x="{x + bar_width/2}" y="{margin + chart_height + 20}" text-anchor="middle" 
          font-family="Arial" font-size="8" fill="#7f8c8d" transform="rotate(-45 {x + bar_width/2} {margin + chart_height + 20})">
        {html.escape(label)}
    </text>
'''
            
            # Y-axis labels
            for i in range(6):
                y_val = (max_val / 5) * i
                y_pos = margin + chart_height - (i * chart_height / 5)
                
                svg_content += f'''
    <line x1="{margin-5}" y1="{y_pos}" x2="{margin}" y2="{y_pos}" stroke="#ddd" stroke-width="1"/>
    <text x="{margin-10}" y="{y_pos+3}" text-anchor="end" font-family="Arial" font-size="10" fill="#7f8c8d">
        {int(y_val) if y_val < 1000 else f"{int(y_val//1000)}K" if y_val < 1000000 else f"{y_val//1000000:.1f}M"}
    </text>
'''
            
            svg_content += f'''
    <!-- Footer -->
    <text x="{width//2}" y="{height-10}" text-anchor="middle" font-family="Arial" font-size="10" fill="#95a5a6">
        Generated by YouTube MCP Server • {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    </text>
</svg>'''
            
            # Save SVG file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chart_svg_{timestamp}.svg"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            return {
                "success": True,
                "type": "svg_chart",
                "file_path": str(filepath),
                "data_points": len(values),
                "max_value": max_val,
                "chart_type": chart_type
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_word_cloud_html(self, text_data: List[str], source_type: str = "titles") -> Dict[str, Any]:
        """Create HTML word cloud visualization."""
        try:
            if not text_data:
                return {"success": False, "error": "No text data provided"}
            
            # Combine all text and count words
            all_text = " ".join(text_data).lower()
            
            # Simple word frequency counting
            import re
            words = re.findall(r'\b\w+\b', all_text)
            
            # Filter common words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
            }
            
            filtered_words = [word for word in words if len(word) > 2 and word not in stop_words]
            
            # Count word frequencies
            word_freq = {}
            for word in filtered_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top words
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:50]
            
            if not top_words:
                return {"success": False, "error": "No significant words found"}
            
            max_freq = top_words[0][1]
            
            # Generate HTML word cloud
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube {source_type.title()} Word Cloud</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
        h1 {{ color: #333; text-align: center; margin-bottom: 30px; }}
        .word-cloud {{ 
            text-align: center; 
            padding: 40px; 
            background: linear-gradient(45deg, #f8f9fa, #e9ecef);
            border-radius: 10px;
            margin: 20px 0;
            min-height: 400px;
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            align-items: center;
            gap: 10px;
        }}
        .word {{ 
            display: inline-block; 
            margin: 2px 5px; 
            padding: 5px 10px;
            border-radius: 20px;
            transition: all 0.3s ease;
            cursor: pointer;
            text-decoration: none;
            border: 2px solid transparent;
        }}
        .word:hover {{ 
            transform: scale(1.1); 
            border-color: #e74c3c;
            box-shadow: 0 5px 15px rgba(231, 76, 60, 0.3);
        }}
        .stats {{ 
            display: flex; 
            justify-content: space-around; 
            margin: 20px 0; 
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }}
        .stat {{ text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #e74c3c; }}
        .stat-label {{ font-size: 14px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>☁️ {source_type.title()} Word Cloud</h1>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{len(text_data)}</div>
                <div class="stat-label">Sources</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(filtered_words)}</div>
                <div class="stat-label">Total Words</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(word_freq)}</div>
                <div class="stat-label">Unique Words</div>
            </div>
            <div class="stat">
                <div class="stat-value">{max_freq}</div>
                <div class="stat-label">Max Frequency</div>
            </div>
        </div>
        
        <div class="word-cloud">
"""
            
            # Add words with varying sizes and colors
            for i, (word, freq) in enumerate(top_words):
                # Calculate font size (12-48px based on frequency)
                font_size = 12 + int((freq / max_freq) * 36)
                
                # Generate color
                hue = (i * 137.5) % 360
                saturation = 60 + (freq / max_freq) * 40
                lightness = 40 + (freq / max_freq) * 20
                
                color = f"hsl({hue}, {saturation}%, {lightness}%)"
                bg_color = f"hsla({hue}, {saturation-20}%, {lightness+30}%, 0.2)"
                
                html_content += f'''
            <span class="word" style="font-size: {font_size}px; color: {color}; background-color: {bg_color};" 
                  title="Frequency: {freq}">
                {html.escape(word)}
            </span>'''
            
            html_content += f"""
        </div>
        
        <p style="text-align: center; color: #666; font-size: 12px; margin-top: 30px;">
            Generated by YouTube MCP Server • {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </p>
    </div>
</body>
</html>
"""
            
            # Save HTML file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"wordcloud_{source_type}_{timestamp}.html"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {
                "success": True,
                "type": "html_word_cloud",
                "file_path": str(filepath),
                "source_type": source_type,
                "total_words": len(filtered_words),
                "unique_words": len(word_freq),
                "top_words": top_words[:10]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_multi_format_visualization(self, data: List[Dict[str, Any]], title: str = "Analysis") -> Dict[str, Any]:
        """Create visualization in multiple formats for maximum compatibility."""
        try:
            results = {
                "success": True,
                "title": title,
                "formats": {},
                "summary": {
                    "data_points": len(data),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # ASCII format (always works)
            ascii_result = self.create_ascii_chart(data, title)
            if ascii_result["success"]:
                results["formats"]["ascii"] = ascii_result
            
            # HTML format (interactive)
            html_result = self.create_html_chart(data, "bar")
            if html_result["success"]:
                results["formats"]["html"] = html_result
            
            # SVG format (scalable)
            svg_result = self.create_svg_chart(data, "bar")
            if svg_result["success"]:
                results["formats"]["svg"] = svg_result
            
            # Add summary stats
            if data:
                values = []
                for item in data:
                    if "statistics" in item:
                        view_count = int(item["statistics"].get("viewCount", 0))
                        values.append(view_count)
                    elif "view_count" in item:
                        values.append(int(item["view_count"]))
                
                if values:
                    results["summary"].update({
                        "total_views": sum(values),
                        "max_views": max(values),
                        "min_views": min(values),
                        "avg_views": int(sum(values) / len(values))
                    })
            
            return results
            
        except Exception as e:
            return {"success": False, "error": str(e)}