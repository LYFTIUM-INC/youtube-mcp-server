"""
Workflow prompts for YouTube MCP Server.
Provides structured prompts for common tool sequence workflows.
"""

from typing import List, Dict, Any

def get_workflow_prompts() -> List[Dict[str, Any]]:
    """Get list of available workflow prompts for MCP.
    
    Returns:
        List of workflow prompt definitions
    """
    return [
        {
            "name": "video_performance_analysis",
            "description": "Complete video performance analysis workflow using search, analysis, and visualization tools",
            "arguments": [
                {
                    "name": "search_query",
                    "description": "Search query to find videos for analysis",
                    "required": True
                },
                {
                    "name": "max_videos", 
                    "description": "Maximum number of videos to analyze (default: 10)",
                    "required": False
                }
            ],
            "workflow": """
**🔍 Video Performance Analysis Workflow**

This workflow combines multiple tools to provide comprehensive video performance insights:

**Step 1: Search for Videos**
- Use `search_youtube_videos` with query='{search_query}', max_results={max_videos}, order='viewCount'
- This finds the most viewed videos matching your search criteria

**Step 2: Get Detailed Video Information** 
- Use `get_video_details` to fetch complete statistics, content details, and snippets
- Include view counts, like counts, comment counts, and publication dates

**Step 3: Analyze Performance Metrics**
- Use `analyze_video_performance` to calculate engagement rates and performance scores
- This provides quantitative metrics for comparison

**Step 4: Create Visualizations**
- `create_engagement_chart` with chart_type='multi' to show like/comment ratios
- `create_word_cloud` from video titles to identify trending topics
- `create_performance_radar` for top 5 videos to compare metrics
- `create_views_timeline` to show performance over time

**Expected Outputs:**
- Performance analysis JSON with engagement metrics
- 4 visualization files (PNG format with base64 encoding)
- Actionable insights on what drives high performance

**Key Insights You'll Get:**
- Which videos have the best engagement rates
- Common keywords in high-performing titles
- Performance patterns over time
- Multi-metric comparison of top videos
            """
        },
        {
            "name": "channel_content_strategy",
            "description": "Analyze channel content strategy and performance patterns using channel-specific tools",
            "arguments": [
                {
                    "name": "channel_id",
                    "description": "YouTube channel ID to analyze",
                    "required": True
                },
                {
                    "name": "analysis_period",
                    "description": "Time period for analysis in days (default: 30)",
                    "required": False
                }
            ],
            "workflow": """
**📊 Channel Content Strategy Analysis**

This workflow analyzes a specific channel's content strategy and performance:

**Step 1: Channel Overview**
- Use `get_channel_info` to fetch channel statistics and basic information
- Provides subscriber count, total videos, and channel metadata

**Step 2: Recent Content Analysis**
- Use `get_channel_videos` to get recent videos from the channel
- Filter by publication date to focus on recent {analysis_period} days
- Sort by date to understand content posting patterns

**Step 3: Performance Deep Dive** 
- Use `analyze_video_performance` on the channel's recent videos
- Calculate engagement rates, performance scores, and trends
- Identify best and worst performing content

**Step 4: Content Pattern Visualization**
- `create_views_timeline` to show performance trends over time
- `create_comparison_heatmap` to compare metrics across videos
- `create_word_cloud` from video titles to identify content themes
- `create_engagement_chart` with chart_type='bar' for performance comparison

**Step 5: Strategic Insights**
Based on the analysis, you'll understand:
- Optimal posting frequency and timing patterns
- Most successful content themes and formats
- Engagement optimization opportunities
- Performance trends and growth patterns

**Expected Outputs:**
- Channel strategy report with comprehensive metrics
- Performance trend visualizations showing growth patterns
- Content theme analysis and recommendations
- Engagement optimization insights
            """
        },
        {
            "name": "trending_content_insights",
            "description": "Analyze trending content to identify patterns, themes, and opportunities",
            "arguments": [
                {
                    "name": "region_code",
                    "description": "Country code for trending analysis (default: US)",
                    "required": False
                },
                {
                    "name": "category_id",
                    "description": "YouTube category ID to focus analysis (optional)",
                    "required": False
                }
            ],
            "workflow": """
**📈 Trending Content Insights Analysis**

This workflow analyzes trending content to identify viral patterns and opportunities:

**Step 1: Fetch Trending Videos**
- Use `get_trending_videos` for region '{region_code}'
- Get top 25 trending videos (filter by category if specified)
- Captures what's currently popular and gaining momentum

**Step 2: Content Characteristics Analysis**
- Use `get_video_details` to analyze trending video patterns
- Examine title structures, video lengths, and upload timing
- Identify common characteristics of viral content

**Step 3: Comments and Engagement Analysis**
- Use `get_video_comments` on top trending videos (sample of 5-10)
- Analyze comment sentiment and engagement patterns
- Understand what resonates with audiences

**Step 4: Viral Pattern Visualization**
- `create_word_cloud` from trending video titles to identify hot topics
- `create_performance_radar` comparing top 5 trending videos
- `create_engagement_chart` with chart_type='scatter' to show viral patterns
- `create_comparison_heatmap` to compare engagement metrics

**Step 5: Market Opportunity Analysis**
Identify opportunities by analyzing:
- Content gaps in trending topics
- Optimal video characteristics for virality
- Regional content preferences and cultural trends
- Timing patterns for maximum reach

**Expected Outputs:**
- Trending content analysis with viral characteristics
- Topic and keyword trend visualizations
- Viral content pattern insights and success factors
- Market opportunity recommendations for content creators

**Key Value:**
- Understand what makes content go viral right now
- Identify trending topics before they peak
- Learn optimal content formats and timing
- Discover underserved niches with viral potential
            """
        }
    ]

def format_workflow_prompt(workflow_name: str, **kwargs) -> str:
    """Format a workflow prompt with provided arguments.
    
    Args:
        workflow_name: Name of the workflow prompt
        **kwargs: Arguments to substitute in the prompt
        
    Returns:
        Formatted workflow prompt text
    """
    workflows = {w["name"]: w for w in get_workflow_prompts()}
    
    if workflow_name not in workflows:
        available = ", ".join(workflows.keys())
        raise ValueError(f"Workflow '{workflow_name}' not found. Available: {available}")
    
    workflow = workflows[workflow_name]
    
    # Substitute arguments in the workflow description
    try:
        formatted_workflow = workflow["workflow"].format(**kwargs)
        return formatted_workflow
    except KeyError as e:
        # If formatting fails, return the original workflow with available substitutions
        return workflow["workflow"]

def get_all_workflows_summary() -> str:
    """Get a summary of all available workflow prompts.
    
    Returns:
        Formatted string with all workflow descriptions
    """
    workflows = get_workflow_prompts()
    
    summary_parts = [
        "# Available YouTube Analysis Workflows",
        "",
        "The YouTube MCP server provides three powerful workflow prompts that combine multiple tools for comprehensive analysis:",
        ""
    ]
    
    for i, workflow in enumerate(workflows, 1):
        summary_parts.extend([
            f"## {i}. {workflow['name'].replace('_', ' ').title()}",
            f"**Description:** {workflow['description']}",
            "",
            "**Required Arguments:**"
        ])
        
        required_args = [arg for arg in workflow["arguments"] if arg["required"]]
        optional_args = [arg for arg in workflow["arguments"] if not arg["required"]]
        
        if required_args:
            for arg in required_args:
                summary_parts.append(f"- `{arg['name']}`: {arg['description']}")
        else:
            summary_parts.append("- None")
            
        if optional_args:
            summary_parts.extend(["", "**Optional Arguments:**"])
            for arg in optional_args:
                summary_parts.append(f"- `{arg['name']}`: {arg['description']}")
        
        summary_parts.extend(["", "---", ""])
    
    summary_parts.extend([
        "## How to Use These Workflows",
        "",
        "1. **Choose a workflow** based on your analysis goal",
        "2. **Provide the required arguments** (search query, channel ID, or region)",
        "3. **Follow the step-by-step workflow** using the specified MCP tools",
        "4. **Analyze the combined results** for comprehensive insights",
        "",
        "Each workflow is designed to provide end-to-end analysis using multiple complementary tools, giving you both quantitative metrics and visual insights for data-driven decision making."
    ])
    
    return "\n".join(summary_parts)