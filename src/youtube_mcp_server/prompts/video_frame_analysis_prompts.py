"""
Video Frame Analysis Prompts for YouTube MCP Server.
Comprehensive prompts for analyzing extracted video frames.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class VideoFrameAnalysisPrompts:
    """Comprehensive prompts for video frame analysis."""
    
    @staticmethod
    def get_comprehensive_frame_analysis_prompt(
        frame_info: Dict[str, Any],
        analysis_focus: List[str] = None
    ) -> str:
        """
        Generate comprehensive frame analysis prompt.
        
        Args:
            frame_info: Information about the frame (timestamp, file path, etc.)
            analysis_focus: Specific aspects to focus on
            
        Returns:
            Detailed analysis prompt
        """
        if analysis_focus is None:
            analysis_focus = [
                "scene_description", "objects", "people", "environment", 
                "lighting", "composition", "movement_indicators", "text_content"
            ]
        
        prompt = f"""# Comprehensive Video Frame Analysis

## Frame Information
- **Timestamp**: {frame_info.get('timestamp', 'Unknown')} seconds
- **Time Position**: {frame_info.get('time_formatted', 'Unknown')}
- **Frame Number**: {frame_info.get('frame_number', 'Unknown')}

## Analysis Instructions
Please provide a detailed analysis of this video frame. Your analysis should be structured, comprehensive, and precise.

### 1. SCENE OVERVIEW
- **Overall Scene Type**: Describe the general type of scene (indoor/outdoor, public/private, natural/urban, etc.)
- **Primary Setting**: What is the main location or environment shown?
- **Scene Context**: What appears to be happening in this moment?

### 2. DETAILED OBJECT INVENTORY
For each significant object in the frame, provide:
- **Object Name**: What is it?
- **Location**: Where in the frame? (center, left, right, foreground, background)
- **Size/Prominence**: How much of the frame does it occupy?
- **Condition/State**: New, old, damaged, in use, etc.
- **Relevance**: How important is this object to the scene?

### 3. PEOPLE ANALYSIS
For each person visible:
- **Count**: How many people are visible?
- **Position in Frame**: Where are they located?
- **Distance from Camera**: Close-up, medium shot, long shot, background
- **Body Language**: Posture, gestures, apparent mood
- **Activity**: What are they doing?
- **Interaction**: Are they interacting with others or objects?
- **Demographics**: Approximate age group, gender (if discernible)
- **Clothing/Appearance**: Notable clothing, style, or appearance details

### 4. ENVIRONMENTAL DETAILS
- **Lighting**: Natural/artificial, bright/dim, direction of light sources
- **Weather**: If outdoor, what are the weather conditions?
- **Time of Day**: Can you estimate the time of day from lighting/shadows?
- **Season**: Any indicators of season (if applicable)?
- **Atmosphere**: Mood or feeling conveyed by the environment

### 5. TECHNICAL & VISUAL COMPOSITION
- **Camera Angle**: Eye-level, high angle, low angle, dutch angle
- **Shot Type**: Wide shot, medium shot, close-up, extreme close-up
- **Depth of Field**: What's in focus vs. blurred?
- **Color Palette**: Dominant colors and their emotional impact
- **Movement Indicators**: Any signs of motion (blur, positioning suggesting movement)
- **Visual Focus**: What draws the eye first?

### 6. TEXT AND GRAPHICS CONTENT
- **Visible Text**: Any readable text, signs, captions, or graphics
- **Language**: What language(s) are visible?
- **Text Context**: Purpose of the text (information, branding, subtitles, etc.)
- **Graphic Elements**: Logos, symbols, or graphic overlays

### 7. ACTIVITY AND ACTION INDICATORS
- **Primary Action**: What is the main action or activity occurring?
- **Secondary Actions**: Any background or peripheral activities?
- **Movement Direction**: Direction of any implied or actual movement
- **Energy Level**: High energy, calm, static, dynamic

### 8. CONTEXTUAL CLUES
- **Time Period**: Any indicators of historical period or era?
- **Cultural Context**: Any cultural or regional indicators?
- **Genre Indicators**: Does this suggest a particular type of content (documentary, entertainment, educational, etc.)?
- **Production Quality**: Professional, amateur, smartphone recording, etc.

### 9. EMOTIONAL AND AESTHETIC QUALITIES
- **Mood**: What emotional tone does the frame convey?
- **Aesthetic Style**: Modern, vintage, artistic, documentary, etc.
- **Visual Appeal**: Compositionally pleasing elements
- **Storytelling Elements**: What story might this frame be telling?

### 10. TECHNICAL OBSERVATIONS
- **Image Quality**: Resolution, clarity, any technical issues
- **Color Grading**: Any apparent color correction or filtering
- **Artifacts**: Any compression artifacts, noise, or distortions

## Output Format
Please structure your response as a JSON object with the following format:

```json
{{
    "timestamp": "{frame_info.get('timestamp', 'Unknown')}",
    "frame_number": {frame_info.get('frame_number', 'Unknown')},
    "analysis": {{
        "scene_overview": {{
            "scene_type": "",
            "primary_setting": "",
            "scene_context": ""
        }},
        "objects": [
            {{
                "name": "",
                "location": "",
                "size_prominence": "",
                "condition": "",
                "relevance": ""
            }}
        ],
        "people": {{
            "count": 0,
            "individuals": [
                {{
                    "position": "",
                    "distance_from_camera": "",
                    "body_language": "",
                    "activity": "",
                    "demographics": "",
                    "clothing_appearance": ""
                }}
            ]
        }},
        "environment": {{
            "lighting": "",
            "weather": "",
            "time_of_day": "",
            "season": "",
            "atmosphere": ""
        }},
        "technical_composition": {{
            "camera_angle": "",
            "shot_type": "",
            "depth_of_field": "",
            "color_palette": "",
            "movement_indicators": "",
            "visual_focus": ""
        }},
        "text_content": {{
            "visible_text": "",
            "language": "",
            "text_context": "",
            "graphic_elements": ""
        }},
        "activity_indicators": {{
            "primary_action": "",
            "secondary_actions": "",
            "movement_direction": "",
            "energy_level": ""
        }},
        "contextual_clues": {{
            "time_period": "",
            "cultural_context": "",
            "genre_indicators": "",
            "production_quality": ""
        }},
        "emotional_aesthetic": {{
            "mood": "",
            "aesthetic_style": "",
            "visual_appeal": "",
            "storytelling_elements": ""
        }},
        "technical_observations": {{
            "image_quality": "",
            "color_grading": "",
            "artifacts": ""
        }}
    }}
}}
```

Be thorough, precise, and objective in your analysis. If something is unclear or not visible, indicate "not visible" or "unclear" rather than guessing."""

        return prompt
    
    @staticmethod
    def get_video_summary_prompt(frame_analyses: List[Dict[str, Any]], video_info: Dict[str, Any]) -> str:
        """
        Generate prompt for summarizing video content based on frame analyses.
        
        Args:
            frame_analyses: List of individual frame analysis results
            video_info: Information about the video
            
        Returns:
            Video summary prompt
        """
        frame_count = len(frame_analyses)
        total_duration = video_info.get("duration", 0)
        
        prompt = f"""# Video Content Summary Analysis

## Video Information
- **Total Duration**: {total_duration:.2f} seconds ({int(total_duration // 60):02d}:{int(total_duration % 60):02d})
- **Frames Analyzed**: {frame_count}
- **Analysis Coverage**: Frames extracted from the video at regular intervals

## Frame Analysis Data
The following are detailed analyses of {frame_count} frames extracted from this video:

"""
        
        # Add individual frame summaries
        for i, analysis in enumerate(frame_analyses):
            timestamp = analysis.get('timestamp', i)
            frame_num = analysis.get('frame_number', i + 1)
            
            prompt += f"""
### Frame {frame_num} (at {timestamp}s)
```json
{analysis}
```
"""
        
        prompt += f"""

## Synthesis Instructions

Based on the {frame_count} frame analyses above, please provide a comprehensive video content summary:

### 1. OVERALL VIDEO NARRATIVE
- **Main Story/Content**: What is this video about? What's the primary narrative or purpose?
- **Content Type**: Is this entertainment, educational, documentary, promotional, personal, etc.?
- **Progression**: How does the content evolve throughout the analyzed timeframe?

### 2. CONSISTENT ELEMENTS
- **Recurring Settings**: What locations or environments appear consistently?
- **Main Characters/Subjects**: Who are the primary people or subjects throughout?
- **Persistent Objects**: What objects or elements appear across multiple frames?
- **Visual Style**: What consistent visual or aesthetic elements are present?

### 3. SCENE TRANSITIONS AND CHANGES
- **Location Changes**: Does the video move between different locations?
- **Character Changes**: Do different people appear at different times?
- **Activity Progression**: How do activities or actions change over time?
- **Visual Evolution**: How does the visual presentation change throughout?

### 4. PRODUCTION ANALYSIS
- **Production Quality**: Professional, semi-professional, amateur, user-generated content?
- **Camera Work**: Static shots, handheld, professional cinematography, etc.?
- **Editing Style**: Fast-paced, slow, documentary-style, artistic, etc.?
- **Audio Indicators**: Any visual cues about audio content (musicians, speakers, etc.)?

### 5. CONTENT CATEGORIZATION
- **Primary Category**: What is the main category of this content?
- **Secondary Categories**: What other categories might apply?
- **Target Audience**: Who appears to be the intended audience?
- **Content Themes**: What themes or subjects are explored?

### 6. TEMPORAL CONTEXT
- **Time Period**: When was this likely filmed? Any historical indicators?
- **Duration Appropriateness**: Does the content justify the video length?
- **Pacing**: How is the pacing of the content based on frame analysis?

### 7. ENGAGEMENT INDICATORS
- **Visual Interest**: How visually engaging does the content appear?
- **Action Level**: How much activity and movement is present?
- **Information Density**: How much information is being conveyed?
- **Entertainment Value**: How entertaining does the content appear to be?

### 8. TECHNICAL ASSESSMENT
- **Video Quality**: Overall technical quality assessment
- **Consistency**: How consistent is the quality and style throughout?
- **Accessibility**: Any indicators of accessibility features (captions, clear visuals, etc.)?

## Output Format

Please provide your analysis in the following JSON structure:

```json
{{
    "video_summary": {{
        "overall_narrative": {{
            "main_story": "",
            "content_type": "",
            "progression": ""
        }},
        "consistent_elements": {{
            "recurring_settings": [],
            "main_subjects": [],
            "persistent_objects": [],
            "visual_style": ""
        }},
        "scene_transitions": {{
            "location_changes": "",
            "character_changes": "",
            "activity_progression": "",
            "visual_evolution": ""
        }},
        "production_analysis": {{
            "production_quality": "",
            "camera_work": "",
            "editing_style": "",
            "audio_indicators": ""
        }},
        "content_categorization": {{
            "primary_category": "",
            "secondary_categories": [],
            "target_audience": "",
            "content_themes": []
        }},
        "temporal_context": {{
            "time_period": "",
            "duration_appropriateness": "",
            "pacing": ""
        }},
        "engagement_indicators": {{
            "visual_interest": "",
            "action_level": "",
            "information_density": "",
            "entertainment_value": ""
        }},
        "technical_assessment": {{
            "video_quality": "",
            "consistency": "",
            "accessibility": ""
        }},
        "key_insights": [
            "Most important insights about this video based on frame analysis"
        ],
        "content_summary": "Comprehensive 2-3 paragraph summary of the video content"
    }},
    "frame_analysis_metadata": {{
        "total_frames_analyzed": {frame_count},
        "video_duration": {total_duration},
        "analysis_timestamp": "{datetime.utcnow().isoformat()}"
    }}
}}
```

Be thorough and analytical, but also provide clear, actionable insights about the video content."""
        
        return prompt
    
    @staticmethod
    def get_comparative_frame_analysis_prompt(frames_data: List[Dict[str, Any]]) -> str:
        """
        Generate prompt for comparing multiple frames to identify patterns, changes, and progressions.
        
        Args:
            frames_data: List of frame information and analyses
            
        Returns:
            Comparative analysis prompt
        """
        frame_count = len(frames_data)
        
        prompt = f"""# Comparative Video Frame Analysis

## Analysis Scope
You are analyzing {frame_count} frames extracted from a video to identify patterns, changes, and progressions.

## Frame Data
"""
        
        for i, frame in enumerate(frames_data):
            prompt += f"""
### Frame {i+1}
- Timestamp: {frame.get('timestamp', 'Unknown')}s
- Analysis: {frame.get('analysis', 'No analysis available')}
"""
        
        prompt += """

## Comparative Analysis Instructions

Please analyze these frames comparatively to identify:

### 1. TEMPORAL PROGRESSION
- **Scene Evolution**: How does the scene change over time?
- **Movement Patterns**: What movement or motion can be inferred?
- **Activity Development**: How do activities progress or change?

### 2. CONSISTENCY ANALYSIS
- **Stable Elements**: What remains consistent across frames?
- **Variable Elements**: What changes between frames?
- **Lighting Changes**: How does lighting evolve?
- **Environmental Shifts**: Any environmental changes?

### 3. NARRATIVE FLOW
- **Story Progression**: What story is being told through these frames?
- **Action Sequence**: Is there a clear sequence of actions?
- **Character Development**: How do people or subjects change?

### 4. PRODUCTION PATTERNS
- **Camera Movement**: Evidence of camera movement or position changes?
- **Shot Progression**: How do shot types or angles change?
- **Visual Continuity**: How consistent is the visual presentation?

Provide your analysis in a structured format focusing on these comparative elements."""
        
        return prompt