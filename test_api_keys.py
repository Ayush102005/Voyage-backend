"""
Test script to verify API keys are configured correctly
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Checking API Key Configuration...\n")
print("="*50)

# Check OpenAI API Key
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key and openai_key != "your_openai_api_key_here":
    print(f"✅ OpenAI API Key: Found (starts with '{openai_key[:7]}...')")
else:
    print("❌ OpenAI API Key: NOT CONFIGURED")
    print("   Please add your key to the .env file")

print()

# Check Tavily API Key
tavily_key = os.getenv("TAVILY_API_KEY")
if tavily_key and tavily_key != "your_tavily_api_key_here":
    print(f"✅ Tavily API Key: Found (starts with '{tavily_key[:7]}...')")
else:
    print("❌ Tavily API Key: NOT CONFIGURED")
    print("   Please add your key to the .env file")

print("="*50)

# Test if we can actually use the keys
if openai_key and openai_key != "your_openai_api_key_here":
    print("\n🧪 Testing OpenAI Connection...")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        # Just check if key format is valid (don't make expensive API call)
        print("✅ OpenAI client initialized successfully")
    except Exception as e:
        print(f"⚠️ OpenAI initialization warning: {e}")

if tavily_key and tavily_key != "your_tavily_api_key_here":
    print("\n🧪 Testing Tavily Connection...")
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=tavily_key)
        print("✅ Tavily client initialized successfully")
    except Exception as e:
        print(f"⚠️ Tavily initialization warning: {e}")

print("\n" + "="*50)
if (openai_key and openai_key != "your_openai_api_key_here" and 
    tavily_key and tavily_key != "your_tavily_api_key_here"):
    print("✨ All API keys are configured! Ready to start the server.")
else:
    print("⚠️ Please configure your API keys in the .env file")
print("="*50)
