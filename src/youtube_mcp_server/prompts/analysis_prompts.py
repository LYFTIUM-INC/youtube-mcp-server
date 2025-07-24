"""
High-level analysis prompts for LLM-powered YouTube content analysis.

This module provides structured prompts that leverage LLM vision and text analysis 
capabilities to extract insights from YouTube video data, thumbnails, and metadata.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class AnalysisPrompt:
    """Structure for analysis prompts with context and instructions."""
    name: str
    description: str
    prompt_template: str
    required_data: List[str]
    optional_data: List[str]
    output_format: str


class YouTubeAnalysisPrompts:
    """Collection of high-level analysis prompts for YouTube content analysis."""
    
    @staticmethod
    def get_thumbnail_effectiveness_prompt() -> AnalysisPrompt:
        """
        Analyze thumbnail effectiveness using vision capabilities.
        
        Returns:
            AnalysisPrompt: Prompt for thumbnail analysis
        """
        return AnalysisPrompt(
            name="thumbnail_effectiveness",
            description="Analyze thumbnail design effectiveness and click-through potential",
            prompt_template="""
Analyze this YouTube thumbnail image and provide insights on its effectiveness:

**Thumbnail Analysis Request:**
- Video Title: {title}
- Channel: {channel_name}
- View Count: {view_count:,}
- Upload Date: {upload_date}
- Video Duration: {duration}

**Analysis Focus Areas:**
1. **Visual Design Quality**: Assess composition, color scheme, text readability, and overall aesthetic appeal
2. **Click-Through Potential**: Evaluate how likely this thumbnail is to generate clicks based on visual appeal and curiosity
3. **Target Audience Alignment**: Determine if the thumbnail matches the expected audience for this content type
4. **Competitive Analysis**: Compare against typical thumbnails in this niche/category
5. **Emotional Impact**: Identify the emotional response the thumbnail is designed to evoke

**Please provide:**
- Effectiveness Score (1-10) with justification
- 3 specific strengths of the thumbnail design
- 3 specific areas for improvement
- Predicted click-through rate category (Low/Medium/High)
- Recommended design changes to increase engagement

**Output Format:** Structured analysis with clear ratings and actionable recommendations.
""",
            required_data=["thumbnail_url", "title", "channel_name", "view_count"],
            optional_data=["upload_date", "duration", "category"],
            output_format="structured_analysis"
        )
    
    @staticmethod
    def get_content_performance_prediction_prompt() -> AnalysisPrompt:
        """
        Predict content performance based on multiple data points.
        
        Returns:
            AnalysisPrompt: Prompt for performance prediction
        """
        return AnalysisPrompt(
            name="content_performance_prediction",
            description="Predict video performance potential using title, description, and metadata",
            prompt_template="""
Analyze this YouTube video's potential for success based on its metadata and content strategy:

**Video Details:**
- Title: {title}
- Description: {description}
- Tags: {tags}
- Category: {category}
- Upload Time: {upload_date}
- Duration: {duration}
- Channel Subscribers: {subscriber_count:,}
- Channel Upload Frequency: {upload_frequency}

**Historical Channel Performance:**
- Average Views: {avg_views:,}
- Average Engagement Rate: {avg_engagement_rate:.2%}
- Top Performing Video Views: {top_video_views:,}

**Analysis Dimensions:**
1. **Title Optimization**: SEO effectiveness, keyword usage, emotional triggers, length optimization
2. **Content Timing**: Upload timing strategy, seasonal relevance, trending topic alignment
3. **Audience Fit**: Alignment with channel's existing audience and content themes
4. **Discoverability**: Search optimization, suggested video potential, algorithm favorability
5. **Engagement Potential**: Likelihood to generate comments, likes, shares, and watch time

**Prediction Output:**
- Performance Prediction: Views range estimate for first 30 days
- Engagement Rate Prediction: Expected like/comment/share rates
- Growth Trajectory: Short-term (1 week) vs long-term (3 months) performance
- Risk Factors: Elements that could limit performance
- Optimization Recommendations: 5 specific actions to improve performance potential

**Confidence Level:** Rate prediction confidence (Low/Medium/High) with reasoning.
""",
            required_data=["title", "description", "category", "upload_date"],
            optional_data=["tags", "subscriber_count", "avg_views", "avg_engagement_rate"],
            output_format="performance_prediction"
        )
    
    @staticmethod
    def get_audience_sentiment_analysis_prompt() -> AnalysisPrompt:
        """
        Analyze audience sentiment from comments and engagement patterns.
        
        Returns:
            AnalysisPrompt: Prompt for sentiment analysis
        """
        return AnalysisPrompt(
            name="audience_sentiment_analysis",
            description="Analyze audience sentiment and engagement patterns from comments",
            prompt_template="""
Analyze the audience sentiment and engagement patterns for this YouTube video:

**Video Context:**
- Title: {title}
- Channel: {channel_name}
- Views: {view_count:,}
- Likes: {like_count:,}
- Comments: {comment_count:,}
- Upload Date: {upload_date}

**Top Comments Sample:**
{top_comments}

**Engagement Metrics:**
- Like-to-View Ratio: {like_ratio:.3%}
- Comment-to-View Ratio: {comment_ratio:.3%}
- Subscriber Conversion: {subscriber_growth} new subscribers

**Analysis Framework:**
1. **Overall Sentiment**: Positive, negative, or mixed audience reception
2. **Emotional Themes**: Primary emotions expressed (excitement, frustration, curiosity, etc.)
3. **Content Reception**: How well the content met audience expectations
4. **Community Dynamics**: Level of discussion, debate, and community interaction
5. **Creator-Audience Relationship**: Evidence of loyal fanbase vs casual viewers

**Key Insights:**
- Sentiment Distribution: % breakdown of positive/neutral/negative responses
- Recurring Themes: Common topics, requests, or concerns in comments
- Audience Engagement Quality: Depth and thoughtfulness of interactions
- Content Impact: Evidence of content influencing viewers (learning, entertainment, inspiration)
- Community Health: Signs of healthy vs toxic community dynamics

**Actionable Recommendations:**
- Content Strategy: How to build on positive reception or address concerns
- Community Management: Strategies for improving audience relationships
- Future Content: Topics or approaches suggested by audience feedback

Provide specific examples from comments to support each analysis point.
""",
            required_data=["title", "channel_name", "view_count", "like_count", "comment_count", "top_comments"],
            optional_data=["upload_date", "subscriber_growth", "dislike_count"],
            output_format="sentiment_analysis"
        )
    
    @staticmethod
    def get_competitive_landscape_analysis_prompt() -> AnalysisPrompt:
        """
        Analyze competitive positioning and market opportunities.
        
        Returns:
            AnalysisPrompt: Prompt for competitive analysis
        """
        return AnalysisPrompt(
            name="competitive_landscape_analysis",
            description="Analyze competitive positioning and identify market opportunities",
            prompt_template="""
Analyze the competitive landscape and positioning for this YouTube content:

**Primary Video/Channel:**
- Channel: {channel_name}
- Video Title: {title}
- Category: {category}
- Subscribers: {subscriber_count:,}
- Recent Performance: {recent_avg_views:,} avg views

**Competitive Context:**
{competitor_data}

**Market Analysis Focus:**
1. **Content Differentiation**: How does this content stand out from competitors?
2. **Quality Positioning**: Production value, expertise level, entertainment factor
3. **Audience Overlap**: Shared vs unique audience segments
4. **Content Gaps**: Underserved topics or approaches in the niche
5. **Growth Opportunities**: Areas where this creator could expand influence

**Strategic Assessment:**
- **Competitive Advantages**: Unique strengths vs competitors
- **Market Position**: Leader, challenger, niche player, or newcomer status
- **Threat Analysis**: Competitive pressures and market risks
- **Blue Ocean Opportunities**: Uncontested market spaces to explore
- **Collaboration Potential**: Creators who might be partners rather than competitors

**Growth Strategy Recommendations:**
1. Content Innovation: New formats or topics to explore
2. Audience Expansion: Demographic or geographic growth opportunities
3. Platform Strategy: Cross-platform opportunities and priorities
4. Partnership Opportunities: Strategic collaborations to consider
5. Differentiation Strategy: How to strengthen unique market position

**Market Trend Analysis:**
- Emerging trends this creator is well-positioned to capitalize on
- Declining trends to avoid or pivot away from
- Seasonal or cyclical opportunities in the niche

Provide specific examples and data-driven insights for each recommendation.
""",
            required_data=["channel_name", "title", "category", "subscriber_count"],
            optional_data=["competitor_data", "recent_avg_views", "market_trends"],
            output_format="competitive_analysis"
        )
    
    @staticmethod
    def get_content_optimization_strategy_prompt() -> AnalysisPrompt:
        """
        Generate comprehensive content optimization strategies.
        
        Returns:
            AnalysisPrompt: Prompt for optimization strategy
        """
        return AnalysisPrompt(
            name="content_optimization_strategy",
            description="Generate data-driven content optimization strategies",
            prompt_template="""
Develop a comprehensive content optimization strategy based on performance data and analytics:

**Channel Overview:**
- Channel: {channel_name}
- Total Subscribers: {subscriber_count:,}
- Total Videos: {video_count}
- Channel Age: {channel_age} months
- Average Views: {avg_views:,}

**Performance Analysis:**
- Top Performing Videos: {top_videos}
- Underperforming Content: {low_performing_videos}
- Engagement Trends: {engagement_trends}
- Upload Consistency: {upload_schedule}

**Audience Insights:**
- Demographics: {audience_demographics}
- Watch Time Patterns: {watch_time_data}
- Traffic Sources: {traffic_sources}
- Device Usage: {device_breakdown}

**Optimization Strategy Development:**

1. **Content Theme Optimization**:
   - Identify highest-performing content themes and formats
   - Recommend content mix ratios for optimal channel growth
   - Suggest new themes based on audience interest and market gaps

2. **Production Quality Enhancement**:
   - Video length optimization based on audience retention data
   - Thumbnail and title optimization strategies
   - Audio/visual quality improvements with highest ROI

3. **Publishing Strategy**:
   - Optimal upload schedule based on audience activity patterns
   - Seasonal content planning and trending topic integration
   - Cross-platform content distribution strategy

4. **Audience Engagement Optimization**:
   - Comment engagement strategies to increase community interaction
   - Call-to-action optimization for subscribers and engagement
   - Community tab and live streaming integration opportunities

5. **Algorithm Optimization**:
   - SEO improvements for search and suggested video placement
   - Click-through rate optimization techniques
   - Watch time and retention improvement strategies

**90-Day Implementation Plan:**
- Week 1-2: Immediate optimizations (titles, thumbnails, descriptions)
- Month 1: Content theme adjustments and upload schedule optimization
- Month 2: Production quality improvements and new format testing
- Month 3: Advanced engagement strategies and community building

**Success Metrics & KPIs:**
- Primary: Subscriber growth rate, average view count, watch time
- Secondary: Engagement rate, click-through rate, revenue (if applicable)
- Long-term: Brand recognition, audience loyalty, market position

Provide specific, actionable recommendations with expected impact timelines.
""",
            required_data=["channel_name", "subscriber_count", "video_count", "avg_views"],
            optional_data=["top_videos", "engagement_trends", "audience_demographics", "upload_schedule"],
            output_format="optimization_strategy"
        )
    
    @staticmethod
    def get_all_prompts() -> Dict[str, AnalysisPrompt]:
        """
        Get all available analysis prompts.
        
        Returns:
            Dict[str, AnalysisPrompt]: Dictionary of all prompts keyed by name
        """
        prompts = {}
        prompt_methods = [
            'get_thumbnail_effectiveness_prompt',
            'get_content_performance_prediction_prompt',
            'get_audience_sentiment_analysis_prompt',
            'get_competitive_landscape_analysis_prompt',
            'get_content_optimization_strategy_prompt'
        ]
        
        for method_name in prompt_methods:
            method = getattr(YouTubeAnalysisPrompts, method_name)
            prompt = method()
            prompts[prompt.name] = prompt
        
        return prompts
    
    @staticmethod
    def format_prompt(prompt_name: str, data: Dict[str, Any]) -> str:
        """
        Format a specific prompt with provided data.
        
        Args:
            prompt_name: Name of the prompt to format
            data: Dictionary of data to populate in the prompt
            
        Returns:
            str: Formatted prompt ready for LLM consumption
            
        Raises:
            ValueError: If prompt_name is not found or required data is missing
        """
        prompts = YouTubeAnalysisPrompts.get_all_prompts()
        
        if prompt_name not in prompts:
            available = ", ".join(prompts.keys())
            raise ValueError(f"Prompt '{prompt_name}' not found. Available: {available}")
        
        prompt = prompts[prompt_name]
        
        # Check for required data
        missing_required = [field for field in prompt.required_data if field not in data]
        if missing_required:
            raise ValueError(f"Missing required data fields: {missing_required}")
        
        # Add default values for missing optional data
        formatted_data = data.copy()
        for field in prompt.optional_data:
            if field not in formatted_data:
                formatted_data[field] = "Not available"
        
        try:
            return prompt.prompt_template.format(**formatted_data)
        except KeyError as e:
            raise ValueError(f"Missing data field in prompt template: {e}")


def get_prompt_summary() -> Dict[str, str]:
    """
    Get a summary of all available analysis prompts.
    
    Returns:
        Dict[str, str]: Dictionary mapping prompt names to descriptions
    """
    prompts = YouTubeAnalysisPrompts.get_all_prompts()
    return {name: prompt.description for name, prompt in prompts.items()}


# Example usage patterns for LLM integration
USAGE_EXAMPLES = {
    "thumbnail_analysis": {
        "description": "Analyze thumbnail effectiveness with vision AI",
        "sample_data": {
            "thumbnail_url": "https://i.ytimg.com/vi/VIDEO_ID/maxresdefault.jpg",
            "title": "How to Build Amazing YouTube Thumbnails",
            "channel_name": "Creator Academy",
            "view_count": 150000,
            "upload_date": "2024-01-15",
            "duration": "10:34"
        }
    },
    "performance_prediction": {
        "description": "Predict video performance based on metadata",
        "sample_data": {
            "title": "Ultimate Guide to YouTube Growth in 2024",
            "description": "Complete tutorial covering...",
            "category": "Education",
            "upload_date": "2024-01-20T10:00:00Z",
            "subscriber_count": 50000,
            "avg_views": 25000
        }
    }
}