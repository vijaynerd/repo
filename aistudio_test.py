import google.generativeai as genai
import os

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env

# API Key setup (as before)
API_KEY_NAME = "GOOGLE_API_KEY"  # Or your specific key name
GOOGLE_API_KEY = os.environ.get(API_KEY_NAME)

if not GOOGLE_API_KEY:
    print(f"Error: {API_KEY_NAME} environment variable not set.")
    exit()

genai.configure(api_key=GOOGLE_API_KEY)

# List available models
print("Available Models:")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(model)

# Your code to generate content (after verifying the model name)
try:
    model = genai.GenerativeModel('models/gemini-1.5-pro')  # Replace with a valid model name from the list
    response = model.generate_content("Tell me a short joke.")
     print(response.text)
except Exception as e:
    print(f"An error occurred during content generation: {e}")