import requests
from config import Config
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.api_url = Config.DEEPSEEK_API_URL
        self.api_key = Config.DEEPSEEK_API_KEY
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
    
    def get_chat_response(self, messages, timeout=30, include_functions=False):
        """Get response from AI API"""
        try:
            payload = {
                "model": "deepseek-chat",
                "messages": messages
            }
            
            if include_functions:
                payload["functions"] = [self._get_end_conversation_function()]
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=timeout
            )
            
            if response.status_code != 200:
                logger.error(f"AI API error: {response.status_code} - {response.text}")
                raise Exception(f"AI API error: {response.status_code}")
            
            return response.json()["choices"][0]["message"]["content"]
            
        except requests.exceptions.Timeout:
            logger.warning("AI API timeout")
            raise
        except Exception as e:
            logger.error(f"AI service error: {str(e)}")
            raise
    
    def generate_summary(self, conversation_text):
        """Generate conversation summary"""
        try:
            prompt = Config.SUMMARY_PROMPT.format(conversation_text=conversation_text)
            
            messages = [{
                "role": "user",
                "content": prompt
            }]
            
            return self.get_chat_response(messages, timeout=30)
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return "Summary generation failed"
    
    def generate_session_summary(self, conversation_text):
        """Generate comprehensive session summary"""
        session_prompt = f"""Analyze this complete conversation session with a child and create a comprehensive educational summary:

**Session Overview**
- Duration: Estimate conversation length
- Main Topics: List 3-5 key subjects discussed
- Learning Objectives: What the child was trying to learn/understand

**Child Development Insights**
- Curiosity Patterns: What sparked the most interest
- Learning Style: How the child best absorbed information
- Knowledge Level: Age-appropriate assessment of understanding

**Educational Effectiveness**
- Successful Teaching Moments: What explanations worked well
- Missed Opportunities: Topics that could be explored further
- Engagement Quality: Rate overall interaction (1-5)

**Recommendations for Future Sessions**
- Follow-up Topics: 2-3 subjects to revisit
- Teaching Strategies: Methods that worked best for this child
- Areas for Growth: Gentle suggestions for development

Keep summary under 200 words, child-development focused.

Conversation:
{conversation_text}"""
        
        try:
            messages = [{
                "role": "user",
                "content": session_prompt
            }]
            
            return self.get_chat_response(messages, timeout=30)
            
        except Exception as e:
            logger.error(f"Session summary generation failed: {str(e)}")
            return "Session summary generation failed"
    
    def _get_end_conversation_function(self):
        """Function definition for AI to call when conversation ends"""
        return {
            "name": "end_conversation",
            "description": "Call when the conversation is naturally finished or the child wants to end the chat",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Reason for ending (e.g., 'user_goodbye', 'natural_conclusion', 'task_completed')"
                    }
                },
                "required": ["reason"]
            }
        }
