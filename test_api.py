import google.generativeai as genai
from dotenv import load_dotenv
import os
import time

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Test fastest model
model = genai.GenerativeModel('gemini-2.5-flash-lite')

start = time.time()
try:
    response = model.generate_content("Extract: KFC 500 PKR 11/30/2025")
    print(f"✅ Success in {time.time()-start:.2f}s")
    print(response.text)
except Exception as e:
    print(f"❌ Error: {e}")