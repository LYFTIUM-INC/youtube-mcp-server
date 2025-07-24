"""
Structured prompts for AI-driven video and audio analysis in advanced trimming operations.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class AnalysisPrompt:
    """Structured prompt for AI analysis."""
    title: str
    system_prompt: str
    user_prompt_template: str
    expected_output_format: str
    confidence_indicators: List[str]


class AdvancedTrimmingPrompts:
    """
    Comprehensive prompts for AI-driven video and audio analysis.
    Designed to work with Claude and other LLMs for content understanding.
    """
    
    @staticmethod
    def get_scene_analysis_prompt(video_context: Dict[str, Any]) -> AnalysisPrompt:
        """
        Generate prompt for detailed scene analysis.
        
        Args:
            video_context: Context about the video (title, description, etc.)
            
        Returns:
            Structured prompt for scene analysis
        """
        system_prompt = """You are an expert video content analyst specializing in scene detection and visual storytelling. Your task is to analyze video frame sequences and identify meaningful scene boundaries, content changes, and visual transitions.

Key Analysis Areas:
1. Visual composition changes (lighting, color palette, camera angles)
2. Subject matter transitions (new objects, people, environments)
3. Narrative flow and storytelling elements
4. Technical transitions (cuts, fades, dissolves)
5. Temporal indicators (time of day, seasons, progression)

Output precise timestamps and confidence scores for your analysis."""
        
        user_prompt_template = """Analyze the following video content for scene changes and transitions:

VIDEO CONTEXT:
- Title: {title}
- Description: {description}
- Duration: {duration} seconds
- Frame Analysis Data: {frame_data}

ANALYSIS TASK:
Identify distinct scenes and provide:
1. Scene start/end timestamps
2. Scene description (2-3 sentences)
3. Transition type (cut, fade, dissolve, etc.)
4. Confidence score (0.0-1.0)
5. Key visual elements
6. Narrative significance

Focus on meaningful content changes rather than minor camera movements."""
        
        expected_output = """JSON format:
{
  "scenes": [
    {
      "start_time": 0.0,
      "end_time": 15.3,
      "description": "Opening scene description",
      "transition_type": "cut|fade|dissolve|motion",
      "confidence": 0.85,
      "visual_elements": ["element1", "element2"],
      "narrative_significance": "sets the context/introduces character/etc."
    }
  ],
  "analysis_metadata": {
    "total_scenes_detected": 5,
    "average_scene_length": 12.4,
    "dominant_transition_type": "cut"
  }
}"""
        
        return AnalysisPrompt(
            title="Video Scene Analysis",
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            expected_output_format=expected_output,
            confidence_indicators=[
                "Clear visual transitions",
                "Consistent lighting changes",
                "Subject matter shifts",
                "Camera angle changes",
                "Audio cues alignment"
            ]
        )
    
    @staticmethod
    def get_audio_pattern_analysis_prompt(audio_context: Dict[str, Any]) -> AnalysisPrompt:
        """
        Generate prompt for audio pattern and event analysis.
        
        Args:
            audio_context: Context about the audio content
            
        Returns:
            Structured prompt for audio analysis
        """
        system_prompt = """You are an expert audio analyst specializing in sound pattern recognition, acoustic event detection, and audio content classification. Your expertise covers speech analysis, environmental sounds, music identification, and acoustic fingerprinting.

Analysis Capabilities:
1. Speech detection and speaker identification
2. Environmental sound classification (birds, traffic, nature, etc.)
3. Music and musical instrument identification
4. Acoustic event timing and duration
5. Sound quality and clarity assessment
6. Emotional tone and ambience analysis

Provide precise temporal analysis with confidence metrics."""
        
        user_prompt_template = """Analyze the following audio content for patterns and significant events:

AUDIO CONTEXT:
- Source: {source_description}
- Duration: {duration} seconds
- Sample Rate: {sample_rate} Hz
- Channels: {channels}
- Transcription: {transcription}
- Audio Classification Results: {classification_data}

ANALYSIS TASK:
Identify and categorize:
1. Speech segments (speakers, language, emotional tone)
2. Music segments (genre, instruments, tempo)
3. Environmental sounds (nature, urban, mechanical)
4. Sound effects and artificial sounds
5. Silence and background noise
6. Audio quality issues

For each identified pattern, provide:
- Start/end timestamps
- Confidence score
- Detailed description
- Category classification
- Contextual significance

Target Pattern: {target_pattern}"""
        
        expected_output = """JSON format:
{
  "audio_events": [
    {
      "start_time": 5.2,
      "end_time": 12.8,
      "event_type": "speech|music|environmental|effect",
      "subcategory": "specific classification",
      "description": "detailed description",
      "confidence": 0.92,
      "characteristics": {
        "volume_level": "low|medium|high",
        "clarity": "clear|muffled|distorted",
        "background_noise": true/false
      },
      "contextual_significance": "importance in content"
    }
  ],
  "pattern_matches": [
    {
      "pattern": "target pattern searched",
      "timestamps": [[start, end], ...],
      "confidence": 0.78,
      "match_quality": "excellent|good|fair|poor"
    }
  ],
  "overall_analysis": {
    "dominant_audio_type": "speech|music|environmental",
    "audio_quality": "assessment",
    "notable_features": ["feature1", "feature2"]
  }
}"""
        
        return AnalysisPrompt(
            title="Audio Pattern Analysis",
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            expected_output_format=expected_output,
            confidence_indicators=[
                "Clear audio signature",
                "Consistent frequency patterns",
                "Distinct acoustic events",
                "Background noise separation",
                "Temporal pattern recognition"
            ]
        )
    
    @staticmethod
    def get_content_trimming_strategy_prompt(trimming_context: Dict[str, Any]) -> AnalysisPrompt:
        """
        Generate prompt for intelligent trimming strategy development.
        
        Args:
            trimming_context: Context about trimming requirements
            
        Returns:
            Structured prompt for trimming strategy
        """
        system_prompt = """You are an expert video editor and content strategist specializing in intelligent video trimming and content optimization. Your expertise includes narrative flow analysis, engagement optimization, and content-driven editing decisions.

Core Competencies:
1. Content value assessment and prioritization
2. Narrative structure preservation
3. Engagement pattern analysis
4. Technical quality considerations
5. Platform-specific optimization
6. Accessibility and clarity enhancement

Your goal is to create optimal trimming strategies that preserve content value while meeting specific requirements."""
        
        user_prompt_template = """Develop an intelligent trimming strategy for the following content:

VIDEO CONTENT ANALYSIS:
- Original Duration: {duration} seconds
- Content Type: {content_type}
- Key Topics: {topics}
- Scene Analysis: {scene_data}
- Audio Analysis: {audio_data}
- Engagement Indicators: {engagement_data}

TRIMMING REQUIREMENTS:
- Target Instruction: "{trim_instruction}"
- Desired Output Length: {target_length}
- Quality Priority: {quality_priority}
- Content Preservation Goals: {preservation_goals}

STRATEGY DEVELOPMENT:
Create a comprehensive trimming plan that:
1. Identifies optimal cut points
2. Preserves narrative coherence
3. Maintains content value
4. Ensures smooth transitions
5. Optimizes for target audience

Consider both technical and creative aspects of the editing decision."""
        
        expected_output = """JSON format:
{
  "trimming_strategy": {
    "approach": "time_based|content_based|hybrid",
    "rationale": "explanation of strategy choice",
    "confidence": 0.87
  },
  "recommended_cuts": [
    {
      "start_time": 0.0,
      "end_time": 30.5,
      "segment_type": "intro|main_content|outro|transition",
      "importance_score": 0.92,
      "justification": "why this segment should be kept/removed",
      "transition_notes": "how to handle cut points"
    }
  ],
  "alternative_options": [
    {
      "strategy_name": "alternative approach",
      "segments": [...],
      "pros_cons": {
        "advantages": ["advantage1", "advantage2"],
        "disadvantages": ["disadvantage1"]
      }
    }
  ],
  "technical_considerations": {
    "cut_point_precision": "frame-accurate recommendations",
    "audio_fade_requirements": "fade in/out suggestions",
    "quality_preservation": "encoding recommendations"
  },
  "content_preservation_score": 0.85
}"""
        
        return AnalysisPrompt(
            title="Content Trimming Strategy",
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            expected_output_format=expected_output,
            confidence_indicators=[
                "Clear narrative structure",
                "Identifiable content segments",
                "Quality transition points",
                "Engagement pattern clarity",
                "Technical feasibility"
            ]
        )
    
    @staticmethod
    def get_multimodal_content_analysis_prompt(content_context: Dict[str, Any]) -> AnalysisPrompt:
        """
        Generate prompt for comprehensive multimodal content analysis.
        
        Args:
            content_context: Combined video and audio context
            
        Returns:
            Structured prompt for multimodal analysis
        """
        system_prompt = """You are an expert multimodal content analyst with deep expertise in video, audio, and text analysis. You excel at synthesizing information across different media types to create comprehensive content understanding and generate actionable insights.

Analytical Framework:
1. Visual-Audio Synchronization Analysis
2. Cross-modal Content Correlation
3. Narrative Coherence Assessment
4. Engagement and Attention Modeling
5. Content Quality and Production Value
6. Accessibility and Comprehension Factors

Your analysis should integrate all available modalities to provide holistic content understanding."""
        
        user_prompt_template = """Perform comprehensive multimodal analysis of the following content:

CONTENT OVERVIEW:
- Title: {title}
- Description: {description}
- Duration: {duration} seconds
- Content Category: {category}

VISUAL ANALYSIS DATA:
{visual_data}

AUDIO ANALYSIS DATA:
{audio_data}

TEXT/TRANSCRIPT DATA:
{transcript_data}

ANALYSIS OBJECTIVES:
1. Identify key content moments and highlights
2. Assess narrative flow and structure
3. Evaluate production quality and clarity
4. Determine optimal segments for various purposes
5. Provide content-aware trimming recommendations
6. Assess accessibility and comprehension factors

Focus on moments where visual, audio, and textual elements align to create impactful content."""
        
        expected_output = """JSON format:
{
  "content_highlights": [
    {
      "timestamp": 45.2,
      "duration": 15.3,
      "highlight_type": "key_moment|explanation|demonstration|transition",
      "multimodal_score": 0.91,
      "components": {
        "visual": "clear demonstration of concept",
        "audio": "clear narration with emphasis",
        "text": "key terminology introduced"
      },
      "significance": "why this moment is important",
      "trimming_recommendation": "keep|optional|remove"
    }
  ],
  "narrative_structure": {
    "introduction": {"start": 0, "end": 30, "quality": 0.85},
    "main_content": {"start": 30, "end": 180, "quality": 0.92},
    "conclusion": {"start": 180, "end": 210, "quality": 0.78}
  },
  "content_quality_assessment": {
    "visual_clarity": 0.88,
    "audio_quality": 0.85,
    "information_density": 0.79,
    "engagement_potential": 0.82,
    "accessibility_score": 0.75
  },
  "optimal_segments": {
    "best_summary_segment": {
      "start": 45.0,
      "end": 90.0,
      "rationale": "contains core message with high production value"
    },
    "most_engaging_segment": {
      "start": 120.0,
      "end": 150.0,
      "rationale": "peak visual and audio interest alignment"
    }
  },
  "trimming_strategies": [
    {
      "purpose": "social_media_short",
      "target_length": 30,
      "recommended_segments": [...],
      "adaptation_notes": "how to optimize for platform"
    }
  ]
}"""
        
        return AnalysisPrompt(
            title="Multimodal Content Analysis",
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            expected_output_format=expected_output,
            confidence_indicators=[
                "Visual-audio synchronization",
                "Content coherence across modalities",
                "Clear narrative structure",
                "Engagement pattern identification",
                "Quality consistency assessment"
            ]
        )
    
    @staticmethod
    def get_prompt_for_task(task_type: str, context: Dict[str, Any]) -> Optional[AnalysisPrompt]:
        """
        Get appropriate prompt for specific analysis task.
        
        Args:
            task_type: Type of analysis task
            context: Task-specific context
            
        Returns:
            Appropriate analysis prompt or None if task type unknown
        """
        prompt_map = {
            "scene_analysis": AdvancedTrimmingPrompts.get_scene_analysis_prompt,
            "audio_analysis": AdvancedTrimmingPrompts.get_audio_pattern_analysis_prompt,
            "trimming_strategy": AdvancedTrimmingPrompts.get_content_trimming_strategy_prompt,
            "multimodal_analysis": AdvancedTrimmingPrompts.get_multimodal_content_analysis_prompt
        }
        
        if task_type in prompt_map:
            return prompt_map[task_type](context)
        else:
            return None
    
    @staticmethod
    def format_prompt(prompt: AnalysisPrompt, context_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Format prompt with actual context data.
        
        Args:
            prompt: Structured prompt template
            context_data: Data to fill template
            
        Returns:
            Formatted prompt ready for AI model
        """
        try:
            formatted_user_prompt = prompt.user_prompt_template.format(**context_data)
            
            return {
                "system": prompt.system_prompt,
                "user": formatted_user_prompt,
                "expected_format": prompt.expected_output_format,
                "title": prompt.title,
                "confidence_indicators": prompt.confidence_indicators
            }
        except KeyError as e:
            # Handle missing context data gracefully
            return {
                "system": prompt.system_prompt,
                "user": f"Context data incomplete. Missing: {e}. Please provide complete context for analysis.",
                "expected_format": prompt.expected_output_format,
                "title": prompt.title,
                "confidence_indicators": prompt.confidence_indicators,
                "error": f"Missing context key: {e}"
            }
    
    @staticmethod
    def get_validation_prompt(analysis_result: Dict[str, Any], original_context: Dict[str, Any]) -> AnalysisPrompt:
        """
        Generate prompt for validating analysis results.
        
        Args:
            analysis_result: Results from previous analysis
            original_context: Original analysis context
            
        Returns:
            Validation prompt
        """
        system_prompt = """You are an expert quality assurance analyst specializing in AI-generated content analysis validation. Your role is to critically evaluate analysis results for accuracy, completeness, and practical applicability.

Validation Criteria:
1. Logical consistency and coherence
2. Technical accuracy and feasibility
3. Completeness of analysis coverage
4. Practical applicability of recommendations
5. Confidence score calibration
6. Output format compliance

Provide constructive feedback and improvement suggestions."""
        
        user_prompt_template = """Validate the following analysis results:

ORIGINAL CONTEXT:
{original_context}

ANALYSIS RESULTS:
{analysis_results}

VALIDATION TASKS:
1. Verify logical consistency of findings
2. Assess technical feasibility of recommendations
3. Evaluate completeness of analysis
4. Check confidence score appropriateness
5. Validate output format compliance
6. Identify potential improvements

Provide detailed validation feedback with specific recommendations for enhancement."""
        
        expected_output = """JSON format:
{
  "validation_results": {
    "overall_quality_score": 0.85,
    "logical_consistency": 0.90,
    "technical_feasibility": 0.80,
    "completeness": 0.85,
    "format_compliance": 0.95
  },
  "issues_identified": [
    {
      "issue_type": "accuracy|completeness|format|feasibility",
      "description": "specific issue description",
      "severity": "high|medium|low",
      "suggested_fix": "how to address this issue"
    }
  ],
  "improvement_suggestions": [
    "specific actionable suggestions"
  ],
  "validation_confidence": 0.88
}"""
        
        return AnalysisPrompt(
            title="Analysis Validation",
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            expected_output_format=expected_output,
            confidence_indicators=[
                "Clear validation criteria",
                "Specific issue identification",
                "Actionable improvement suggestions",
                "Appropriate severity assessment",
                "Constructive feedback tone"
            ]
        )