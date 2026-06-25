# 🛠️ Python lightweight image, Debian Bookworm based for maximum stability
FROM python:3.10-slim-bookworm

# वर्क डायरेक्टरी सेट करें
WORKDIR /app

# सिस्टम डिपेंडेंसीज इंस्टॉल करने के लिए (Media handling और Git के लिए ज़रूरी)
RUN apt-get update && apt-get install -y git wget curl ffmpeg && rm -rf /var/lib/apt/lists/*

# requirements.txt को पहले कॉपी करें ताकि डॉकर कैश का सही इस्तेमाल हो सके
COPY requirements.txt .

# बिना कैशे के डिपेंडेंसीज इंस्टॉल करें ताकि इमेज साइज़ छोटा रहे
RUN pip install --no-cache-dir -r requirements.txt

# बाकी पूरे प्रोजेक्ट कोड और मॉड्यूल्स को कॉपी करें
COPY . .

# बोट को बैकग्राउंड में स्टार्ट करने की फाइनल कमांड
CMD ["python", "main.py"]
