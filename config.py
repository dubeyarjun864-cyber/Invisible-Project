import os
from dotenv import load_dotenv

# .env फ़ाइल से वेरिएबल्स लोड करने के लिए
load_dotenv()

class Config:
    # टेलीग्राम API क्रेडेंशियल्स (my.telegram.org से मिलेंगे)
    API_ID = int(os.getenv("API_ID", "0"))  # यहाँ डिफ़ॉल्ट में कोई नंबर भी डाल सकते हो
    API_HASH = os.getenv("API_HASH", "your_api_hash_here")
    
    # बोट का टोकन (@BotFather से मिलेगा)
    BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")
    
    # एडमिन की टेलीग्राम न्यूमेरिक ID (Optional)
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
