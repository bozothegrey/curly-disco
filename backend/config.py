import os
from datetime import timedelta

class Config:
    # MongoDB Configuration
    MONGODB_URI = os.getenv("MONGODB_URI")
    DATABASE_NAME = "kids_chat"
    
    # API Configuration
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
    
    # Conversation Settings
    CONVERSATION_TIMEOUT = 30 * 60  # 30 minutes in seconds
    
    # Conversation topic change
    TOPIC_OVERLAP_THRESHOLD = 0.3

    # Timeout Profiles
    TIMEOUT_PROFILE = {
        "simple": 15,
        "complex": 30,
        "fallback": 5
    }
    
    # Thread Pool Settings
    MAX_WORKERS = 4
    
    # Flask Settings
    HOST = "0.0.0.0"
    PORT = int(os.environ.get("PORT", 10000))
    
    # System Prompts
    SYSTEM_PROMPT = """You are a friendly AI tutor for children aged 6-9. 
Key requirements:
1. Use simple words and short sentences
2. Add emojis to make it fun only if the user asks 🎨
3. Ask one follow-up question
4. Relate to previous topics when possible
5. Do not react to trolling. You can ignore or send "..." or "zzz". 
    Or explain that wasting time in front of AI is not good use of time and resources.

IMPORTANT: If the child says they want to end the conversation, stop the chat, 
or use phrases like "let's end", "done talking", "finish this", etc., 
say a nice goodbye and append "CHAT-ENDED" to your response """


    SUMMARY_PROMPT = """Act as a child development expert analyzing this conversation. Create a structured summary for future reference:

**Child Profile Update**
1. Observed Interests: Identify 2-3 specific interests the child demonstrated
2. Learning Patterns: Note any curiosity patterns or learning styles shown
3. Knowledge Gaps: Highlight misunderstandings to address later

**Educational Strategy**
1. Concepts Taught: List core concepts covered (max 3)
2. Teaching Methods: Detail metaphors/analogies that worked well
3. Engagement Level: Rate 1-5 how engaged the child seemed

**Development Notes**
1. Curiosity Spark: Suggest 1 related topic to explore next
2. Parental Note: Flag any concerns (social/emotional/cognitive) with constructive suggestions
3. Positive Reinforcement: Identify 1 strength to encourage

**Format Requirements**
- Use child-friendly terms avoid technical jargon
- Keep each section under 15 words
- Emphasize interests over weaknesses
- Write in third-person neutral tone

Conversation:
{conversation_text}

Effective summary:"""

