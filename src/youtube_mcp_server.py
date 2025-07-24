    async def _transcript_analysis_prompt(self, params):
        """Generate a detailed transcript analysis prompt."""
        try:
            video_id = params["video_id"]
            focus_area = params["focus_area"]
            
            logger.info(f"Creating transcript analysis prompt for video: {video_id}, focus: {focus_area}")
            
            # Get the transcript
            transcripts = self.youtube_collector.get_transcripts([video_id])
            
            if video_id not in transcripts or not transcripts[video_id]:
                return {
                    "messages": [{
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": f"I wanted to analyze the transcript of YouTube video {video_id}, but no transcript was found for this video."
                        }
                    }]
                }
            
            # Format the transcript
            transcript_text = ""
            for segment in transcripts[video_id]:
                start_time = self._format_time(segment.get("start", 0))
                text = segment.get("text", "")
                transcript_text += f"[{start_time}] {text}\n"
            
            # Get video details if available
            video_title = ""
            if video_id in self.youtube_collector.video_data:
                video_data = self.youtube_collector.video_data[video_id]
                if isinstance(video_data, list):
                    video_data = video_data[-1]
                video_title = video_data.get("title", "")
            
            # Create focus-specific prompt
            focus_prompts = {
                "content_quality": "Focus on analyzing the quality of content, including factual accuracy, depth of information, and clarity of explanation.",
                "audience_engagement": "Focus on elements that engage or disengage the audience, including storytelling techniques, hooks, and calls to action.",
                "seo_optimization": "Focus on keyword usage, title optimization, description quality, and other SEO factors.",
                "educational_value": "Focus on the educational aspects, including teaching methods, knowledge transfer, and learning outcomes."
            }
            
            focus_instruction = focus_prompts.get(focus_area, "Provide a general analysis of the transcript.")
            
            return {
                "messages": [{
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Please analyze this YouTube video transcript with a focus on {focus_area.replace('_', ' ')}.\n\n"
                               f"Video: {video_title} (ID: {video_id})\n\n"
                               f"INSTRUCTIONS: {focus_instruction}\n\n"
                               f"TRANSCRIPT:\n{transcript_text}\n\n"
                               f"Provide a detailed, structured analysis addressing the focus area of {focus_area.replace('_', ' ')}."
                    }
                }]
            }
        except Exception as e:
            logger.error(f"Error creating transcript analysis prompt: {e}")
            return {
                "messages": [{
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"I was going to analyze the transcript of YouTube video {video_id}, but encountered an error: {str(e)}"
                    }
                }]
            }
    
    async def _thumbnail_analysis_prompt(self, params):
        """Generate a detailed thumbnail analysis prompt."""
        try:
            video_id = params["video_id"]
            
            logger.info(f"Creating thumbnail analysis prompt for video: {video_id}")
            
            # First, ensure we have the video data
            if video_id not in self.youtube_collector.video_data:
                self.youtube_collector.load_data_from_ids([video_id])
            
            if video_id not in self.youtube_collector.video_data:
                return {
                    "messages": [{
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": f"I wanted to analyze the thumbnail of YouTube video {video_id}, but couldn't find data for this video."
                        }
                    }]
                }
            
            # Get the thumbnail URL
            video_data = self.youtube_collector.video_data[video_id]
            if isinstance(video_data, list):
                video_data = video_data[-1]  # Get the most recent data
            
            video_title = video_data.get("title", "")
            thumbnail_url = video_data.get("thumbnail_url", "")
            
            if not thumbnail_url:
                return {
                    "messages": [{
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": f"I wanted to analyze the thumbnail of YouTube video {video_id} ({video_title}), but couldn't find a thumbnail URL."
                        }
                    }]
                }
            
            return {
                "messages": [{
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Please analyze this YouTube video thumbnail in detail.\n\n"
                               f"Video: {video_title} (ID: {video_id})\n"
                               f"Thumbnail URL: {thumbnail_url}\n\n"
                               f"INSTRUCTIONS:\n"
                               f"1. Describe the main visual elements in the thumbnail\n"
                               f"2. Analyze any text present (content, color, font, positioning)\n"
                               f"3. Evaluate the color scheme and visual hierarchy\n"
                               f"4. Assess the thumbnail's ability to attract clicks\n"
                               f"5. Suggest improvements or alternatives\n"
                               f"6. Compare to best practices for YouTube thumbnails\n\n"
                               f"Please provide a comprehensive analysis addressing all aspects of the thumbnail design and effectiveness."
                    }
                }]
            }
        except Exception as e:
            logger.error(f"Error creating thumbnail analysis prompt: {e}")
            return {
                "messages": [{
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"I was going to analyze the thumbnail of YouTube video {video_id}, but encountered an error: {str(e)}"
                    }
                }]
            }
    
    async def _comment_analysis_prompt(self, params):
        """Generate a prompt for analyzing video comments."""
        try:
            video_id = params["video_id"]
            max_comments = params["max_comments"]
            
            logger.info(f"Creating comment analysis prompt for video: {video_id}")
            
            # Get video details
            video_title = ""
            if video_id in self.youtube_collector.video_data:
                video_data = self.youtube_collector.video_data[video_id]
                if isinstance(video_data, list):
                    video_data = video_data[-1]
                video_title = video_data.get("title", "")
            
            # Get comments
            comments = self.youtube_collector.get_comments(
                video_id=video_id,
                max_results=max_comments
            )
            
            if not comments:
                return {
                    "messages": [{
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": f"I wanted to analyze comments from YouTube video {video_id}, but no comments were found."
                        }
                    }]
                }
            
            # Format comments
            comments_text = ""
            for i, comment in enumerate(comments, 1):
                comments_text += f"{i}. Author: {comment.author}\n"
                comments_text += f"   Likes: {comment.like_count}\n"
                comments_text += f"   Text: {comment.text}\n\n"
            
            return {
                "messages": [{
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Please analyze the following comments from the YouTube video: {video_title} (ID: {video_id}).\n\n"
                               f"COMMENTS:\n{comments_text}\n"
                               f"INSTRUCTIONS:\n"
                               f"1. Identify the overall sentiment (positive, negative, neutral, mixed)\n"
                               f"2. Extract key themes and topics mentioned frequently\n"
                               f"3. Highlight any constructive feedback or suggestions\n"
                               f"4. Note any questions or concerns that could be addressed\n"
                               f"5. Identify what viewers liked most about the content\n"
                               f"6. Analyze the engagement level based on comment quality\n"
                               f"7. Provide recommendations on how to improve future content based on this feedback\n\n"
                               f"Please provide a comprehensive analysis that could help the content creator understand their audience better."
                    }
                }]
            }
        except Exception as e:
            logger.error(f"Error creating comment analysis prompt: {e}")
            return {
                "messages": [{
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"I was going to analyze comments from YouTube video {video_id}, but encountered an error: {str(e)}"
                    }
                }]
            }
    
    async def _video_comparison_prompt(self, params):
        """Generate a prompt for comparing multiple videos."""
        try:
            video_ids = params["video_ids"]
            comparison_factors = params["comparison_factors"]
            
            logger.info(f"Creating video comparison prompt for videos: {', '.join(video_ids)}")
            
            # Ensure we have data for all videos
            missing_ids = []
            for video_id in video_ids:
                if video_id not in self.youtube_collector.video_data:
                    missing_ids.append(video_id)
            
            if missing_ids:
                self.youtube_collector.load_data_from_ids(missing_ids)
            
            # Collect video details
            videos_info = []
            for video_id in video_ids:
                if video_id in self.youtube_collector.video_data:
                    video_data = self.youtube_collector.video_data[video_id]
                    if isinstance(video_data, list):
                        video_data = video_data[-1]
                    
                    videos_info.append({
                        "id": video_id,
                        "title": video_data.get("title", ""),
                        "view_count": video_data.get("view_count", 0),
                        "like_count": video_data.get("like_count", 0),
                        "comment_count": video_data.get("comment_count", 0),
                        "upload_date": video_data.get("upload_date", ""),
                        "description": self._truncate_text(video_data.get("description", ""), 200)
                    })
            
            if not videos_info or len(videos_info) < 2:
                return {
                    "messages": [{
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": f"I wanted to compare YouTube videos {', '.join(video_ids)}, but couldn't find enough data for comparison."
                        }
                    }]
                }
            
            # Generate factor-specific instructions
            factor_instructions = {
                "engagement": "Compare engagement metrics (views, likes, comments) and audience reception.",
                "content": "Compare content quality, topic coverage, information depth, and overall value.",
                "production_quality": "Compare production elements like audio quality, visual presentation, editing style, and overall professionalism.",
                "seo": "Compare SEO effectiveness including titles, descriptions, tags, and keyword optimization."
            }
            
            factors_text = "\n".join([f"- {factor.capitalize()}: {factor_instructions.get(factor, '')}" 
                                    for factor in comparison_factors])
            
            # Format videos information
            videos_text = ""
            for i, video in enumerate(videos_info, 1):
                videos_text += f"VIDEO {i}: {video['title']} (ID: {video['id']})\n"
                videos_text += f"- Views: {video['view_count']}\n"
                videos_text += f"- Likes: {video['like_count']}\n"
                videos_text += f"- Comments: {video['comment_count']}\n"
                videos_text += f"- Upload Date: {video['upload_date']}\n"
                videos_text += f"- Description: {video['description']}\n\n"
            
            return {
                "messages": [{
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Please compare the following YouTube videos, focusing on these aspects: {', '.join(comparison_factors)}.\n\n"
                               f"VIDEOS TO COMPARE:\n\n{videos_text}\n"
                               f"COMPARISON FACTORS:\n{factors_text}\n\n"
                               f"INSTRUCTIONS:\n"
                               f"1. Provide a head-to-head comparison of the videos for each factor\n"
                               f"2. Identify strengths and weaknesses of each video\n"
                               f"3. Determine which video performs best in each category\n"
                               f"4. Provide an overall comparison summary\n"
                               f"5. Suggest what each video could learn from the others\n\n"
                               f"Please provide a comprehensive comparison that highlights meaningful differences and similarities."
                    }
                }]
            }
        except Exception as e:
            logger.error(f"Error creating video comparison prompt: {e}")
            return {
                "messages": [{
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"I was going to compare YouTube videos {', '.join(video_ids)}, but encountered an error: {str(e)}"
                    }
                }]
            }
    
    async def _content_guidance_prompt(self, params):
        """Generate a prompt for YouTube content creation guidance."""
        try:
            topic = params["topic"]
            audience = params["audience"]
            length_minutes = params["length_minutes"]
            
            logger.info(f"Creating content guidance prompt for topic: {topic}")
            
            return {
                "messages": [{
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"I'm planning to create a YouTube video about '{topic}' for an audience described as '{audience}'. The video will be approximately {length_minutes} minutes long.\n\n"
                               f"Please provide comprehensive guidance for creating this YouTube video, including:\n\n"
                               f"1. Title suggestions that would perform well in search and attract clicks\n"
                               f"2. A recommended video structure with timeframes for each section\n"
                               f"3. Key points to cover based on the topic and audience\n"
                               f"4. Thumbnail design recommendations\n"
                               f"5. Description template with SEO considerations\n"
                               f"6. Tag suggestions\n"
                               f"7. Hooks and engagement strategies for the first 30 seconds\n"
                               f"8. Ideas for calls-to-action\n"
                               f"9. Potential B-roll/visual suggestions\n"
                               f"10. Common pitfalls to avoid for this type of content\n\n"
                               f"Please be specific and provide actionable guidance that will help me create a high-quality, engaging YouTube video for my target audience."
                    }
                }]
            }
        except Exception as e:
            logger.error(f"Error creating content guidance prompt: {e}")
            return {
                "messages": [{
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"I was going to request guidance for creating YouTube content about '{topic}', but encountered an error: {str(e)}"
                    }
                }]
            }
    
    async def _get_video_metadata_resource(self, uri, params):
        """Resource handler for video metadata."""
        try:
            video_id = params["video_id"]
            logger.info(f"Getting video metadata resource for: {video_id}")
            
            # Check if we already have the video data
            if video_id not in self.youtube_collector.video_data:
                # Load the video data
                self.youtube_collector.load_data_from_ids([video_id])
            
            # Get the video data
            if video_id in self.youtube_collector.video_data:
                video_data = self.youtube_collector.video_data[video_id]
                if isinstance(video_data, list):
                    video_data = video_data[-1]  # Get the most recent data
                
                # Format the metadata as a text resource
                metadata_text = f"# Video: {video_data.get('title', '')}\n\n"
                metadata_text += f"Video ID: {video_id}\n"
                metadata_text += f"URL: {video_data.get('url', f'https://www.youtube.com/watch?v={video_id}')}\n"
                metadata_text += f"Upload Date: {video_data.get('upload_date', '')}\n"
                metadata_text += f"View Count: {video_data.get('view_count', 0)}\n"
                metadata_text += f"Like Count: {video_data.get('like_count', 0)}\n"
                metadata_text += f"Comment Count: {video_data.get('comment_count', 0)}\n\n"
                metadata_text += f"## Description\n\n{video_data.get('description', '')}\n\n"
                
                if video_data.get('tags'):
                    metadata_text += f"## Tags\n\n" + ", ".join(video_data.get('tags', [])) + "\n"
                
                return {
                    "contents": [{
                        "uri": uri.href,
                        "text": metadata_text
                    }]
                }
            else:
                return {
                    "contents": [{
                        "uri": uri.href,
                        "text": f"No metadata found for video '{video_id}'"
                    }]
                }
        except Exception as e:
            logger.error(f"Error getting video metadata resource: {e}")
            return {
                "contents": [{
                    "uri": uri.href,
                    "text": f"Error getting video metadata: {str(e)}"
                }]
            }
            
    async def _get_channel_info_resource(self, uri, params):
        """Resource handler for channel information."""
        try:
            channel_id = params["channel_id"]
            logger.info(f"Getting channel info resource for: {channel_id}")
            
            # Currently, the ytfunc project doesn't have a direct channel info method
            # So we'll construct a basic resource with what we can get
            
            # Try to get channel ID from identifier first
            resolved_channel_id = None
            try:
                resolved_channel_id = self.youtube_collector.get_channel_id(channel_id)
            except Exception as e:
                logger.warning(f"Failed to resolve channel ID: {e}")
                resolved_channel_id = channel_id
            
            # Ideally, we'd query the YouTube API for channel details
            # For now, we'll provide a simple resource with the channel ID and a link
            
            channel_text = f"# YouTube Channel: {channel_id}\n\n"
            
            if resolved_channel_id:
                channel_text += f"Channel ID: {resolved_channel_id}\n"
                channel_text += f"URL: https://www.youtube.com/channel/{resolved_channel_id}\n\n"
            else:
                channel_text += f"Channel identifier: {channel_id}\n"
                channel_text += f"URL: https://www.youtube.com/user/{channel_id}\n\n"
            
            channel_text += f"To get videos from this channel, use the `get_channel_videos` tool."
            
            return {
                "contents": [{
                    "uri": uri.href,
                    "text": channel_text
                }]
            }
        except Exception as e:
            logger.error(f"Error getting channel info resource: {e}")
            return {
                "contents": [{
                    "uri": uri.href,
                    "text": f"Error getting channel info: {str(e)}"
                }]
            }
    
    async def _get_transcript_resource(self, uri, params):
        """Resource handler for video transcript."""
        try:
            video_id = params["video_id"]
            logger.info(f"Getting transcript resource for video: {video_id}")
            
            # Get transcript for the video
            transcripts = self.youtube_collector.get_transcripts([video_id])
            
            if video_id in transcripts and transcripts[video_id]:
                # Format the transcript
                transcript_text = f"# Transcript for video: {video_id}\n\n"
                
                for segment in transcripts[video_id]:
                    start_time = self._format_time(segment.get("start", 0))
                    text = segment.get("text", "")
                    transcript_text += f"[{start_time}] {text}\n"
                
                return {
                    "contents": [{
                        "uri": uri.href,
                        "text": transcript_text
                    }]
                }
            else:
                return {
                    "contents": [{
                        "uri": uri.href,
                        "text": f"No transcript found for video '{video_id}'"
                    }]
                }
        except Exception as e:
            logger.error(f"Error getting transcript resource: {e}")
            return {
                "contents": [{
                    "uri": uri.href,
                    "text": f"Error getting transcript: {str(e)}"
                }]
            }
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to a maximum length with ellipsis."""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as a time string (HH:MM:SS)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def start(self):
        """Start the YouTube MCP server."""
        logger.info("Starting YouTube MCP server")
        
        # Connect the server using stdio transport
        transport = StdioTransport()
        self.server.connect(transport)
        
        logger.info("YouTube MCP server started")


def main():
    """Main entry point for the YouTube MCP server."""
    try:
        server = YouTubeMcpServer()
        server.start()
    except Exception as e:
        logger.error(f"Error starting YouTube MCP server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
