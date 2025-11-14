import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GOOGLE_API_KEY')
url = f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}'

response = requests.get(url)
models = response.json()

print("\n🤖 Available Gemini models for generateContent:\n")
print("=" * 70)

for model in models.get('models', []):
    if 'generateContent' in model.get('supportedGenerationMethods', []):
        name = model['name']
        display_name = model.get('displayName', '')
        description = model.get('description', '')
        
        print(f"\n✅ Model: {name}")
        print(f"   Display Name: {display_name}")
        if description:
            print(f"   Description: {description[:100]}...")

print("\n" + "=" * 70)
print("\n💡 Use these model names in your ChatGoogleGenerativeAI() calls")
print("   Example: model='models/gemini-1.5-flash-latest'\n")
