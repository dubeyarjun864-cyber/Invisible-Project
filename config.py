import os
from dotenv import load_dotenv

# .env फ़ाइल से वेरिएबल्स लोड करने के लिए
load_dotenv()

class Config:
    # टेलीग्राम API क्रेडेंशियल्स (my.telegram.org से मिलेंगे)
    API_ID = int(os.getenv("API_ID", "37876980"))  # यहाँ डिफ़ॉल्ट में कोई नंबर भी डाल सकते हो
    API_HASH = os.getenv("API_HASH", "5de17ccad483d9870dd94e1d705c0c54")
    
    # बोट का टोकन (@BotFather से मिलेगा)
    BOT_TOKEN = os.getenv("BOT_TOKEN", "8915750105:AAG9B5Um-qGutD7obhYqeFb982NnGKRPTXo")
    
    # एडमिन की टेलीग्राम न्यूमेरिक ID (Optional)
    ADMIN_ID = int(os.getenv("ADMIN_ID", "8802295647"))
