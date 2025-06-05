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
    CONVERSATION_TIMEOUT = 5 * 60  # 5 minutes in seconds
    
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
    SYSTEM_PROMPT = """You are a friendly AI tutor for children aged 6-12. 
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


    TOPICS_PROMPT = """This is an online conversation between an AI and a child: 
    {conversation_text}
    
    You will now write a list of topics covered in this conversation as a sequence of words separated by commas:"""

    SUMMARY_PROMPT = """Act as a child development expert analyzing this conversation. Create or, if a previous profile is provided, 
    update the child profile in structured form for future reference by a parent or guardian:

    
**Educational Strategy**
1. Learning Patterns: Note any curiosity patterns or learning styles shown
2. Teaching Methods: Detail metaphors/analogies that worked well
3. Engagement Level: Rate 1-5 how engaged the child seemed

**Development Notes**
1. Curiosity Spark: Suggest 1 related topic to explore next
2. Parental Note: Flag any concerns (social/emotional/cognitive) with constructive suggestions
3. Positive Reinforcement: Identify 1 strength to encourage


- Keep each section under 15 words
- Write in third-person neutral tone

Conversation:
{conversation_text}

Previous Child Profile:
{previous_profile}

Updated profile:"""
