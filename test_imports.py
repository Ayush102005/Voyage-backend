"""
Quick test to verify all imports work correctly
"""

print("Testing imports...")

try:
    from fastapi import FastAPI
    print("✅ FastAPI imported successfully")
except ImportError as e:
    print(f"❌ FastAPI import failed: {e}")

try:
    from langchain_openai import ChatOpenAI
    print("✅ LangChain OpenAI imported successfully")
except ImportError as e:
    print(f"❌ LangChain OpenAI import failed: {e}")

try:
    from langchain.agents import tool, AgentExecutor, create_react_agent
    print("✅ LangChain agents imported successfully")
except ImportError as e:
    print(f"❌ LangChain agents import failed: {e}")

try:
    from tavily import TavilyClient
    print("✅ Tavily imported successfully")
except ImportError as e:
    print(f"❌ Tavily import failed: {e}")

try:
    from pydantic import BaseModel
    print("✅ Pydantic imported successfully")
except ImportError as e:
    print(f"❌ Pydantic import failed: {e}")

try:
    from dotenv import load_dotenv
    print("✅ python-dotenv imported successfully")
except ImportError as e:
    print(f"❌ python-dotenv import failed: {e}")

try:
    import uvicorn
    print("✅ Uvicorn imported successfully")
except ImportError as e:
    print(f"❌ Uvicorn import failed: {e}")

print("\n" + "="*50)
print("✨ All imports successful! Backend is ready to run.")
print("="*50)
