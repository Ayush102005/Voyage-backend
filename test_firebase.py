"""
Test script to verify Firebase is configured correctly
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("🔥 Testing Firebase Configuration...\n")
print("="*50)

# Check if credentials file exists
cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
print(f"Looking for credentials at: {cred_path}")

if os.path.exists(cred_path):
    print("✅ Firebase credentials file found")
else:
    print("❌ Firebase credentials file NOT found")
    print("\n📋 Next steps:")
    print("1. Go to Firebase Console: https://console.firebase.google.com/")
    print("2. Select your project")
    print("3. Go to Project Settings → Service Accounts")
    print("4. Click 'Generate new private key'")
    print("5. Save as 'firebase-credentials.json' in the backend folder")
    print("\nSee FIREBASE_SETUP.md for detailed instructions")
    exit(1)

# Check Firebase Web API Key
web_api_key = os.getenv("FIREBASE_WEB_API_KEY")
if web_api_key and web_api_key != "your_firebase_web_api_key_here":
    print(f"✅ Firebase Web API Key found (starts with '{web_api_key[:7]}...')")
else:
    print("⚠️  Firebase Web API Key not configured in .env")
    print("   This is needed for frontend authentication")

print("\n" + "="*50)
print("\n🧪 Attempting to initialize Firebase...\n")

try:
    from firebase_config import initialize_firebase, get_firestore_client
    
    # Initialize Firebase
    result = initialize_firebase()
    
    if result:
        print("✅ Firebase Admin SDK initialized successfully!")
        
        # Test Firestore connection
        db = get_firestore_client()
        if db:
            print("✅ Firestore database connected!")
            
            # Try to access a collection (doesn't create it)
            print("\n📊 Testing Firestore access...")
            test_ref = db.collection('_test_')
            print("✅ Firestore is ready to use!")
            
        else:
            print("❌ Could not connect to Firestore")
    else:
        print("❌ Firebase initialization failed")
        
except Exception as e:
    print(f"❌ Error during Firebase setup: {e}")
    print("\nMake sure firebase-admin is installed:")
    print("  pip install firebase-admin")

print("\n" + "="*50)
print("\n🎯 Firebase Setup Status:")
print("✅ Credentials file: Present" if os.path.exists(cred_path) else "❌ Credentials file: Missing")
print("✅ Web API Key: Configured" if web_api_key and web_api_key != "your_firebase_web_api_key_here" else "⚠️  Web API Key: Not configured")

print("\n" + "="*50)
print("\n📚 For setup instructions, see: FIREBASE_SETUP.md")
print("="*50)
