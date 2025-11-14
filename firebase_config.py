"""
Firebase configuration and initialization
"""

import firebase_admin
from firebase_admin import credentials, auth, firestore
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Firebase Admin SDK
def initialize_firebase():
    """
    Initialize Firebase Admin SDK with service account credentials.
    This only needs to be called once when the app starts.
    """
    try:
        # Check if Firebase is already initialized
        firebase_admin.get_app()
        print("[OK] Firebase already initialized")
    except ValueError:
        # Firebase not initialized, so initialize it
        env_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        if env_path and os.path.exists(env_path):
            cred_path = env_path
        else:
            cred_path = os.path.join(os.path.dirname(__file__), "firebase-credentials.json")

        if not os.path.exists(cred_path):
            print(f"[ERROR] Firebase credentials file not found at: {cred_path}")
            print("Download your service account JSON from Firebase Console and place it in the backend folder as 'firebase-credentials.json'.")
            raise RuntimeError("Firebase credentials missing. Backend cannot start.")

        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("[OK] Firebase initialized successfully")
        except Exception as e:
            print(f"[ERROR] Error initializing Firebase: {e}")
            raise
    
    return True


# Get Firestore client
def get_firestore_client():
    """
    Get Firestore database client.
    """
    try:
        db = firestore.client()
        return db
    except Exception as e:
        print(f"[ERROR] Error getting Firestore client: {e}")
        return None


# Firebase Auth helper functions
def verify_firebase_token(id_token: str):
    """
    Verify a Firebase ID token and return the decoded token.
    
    Args:
        id_token: Firebase ID token from client
        
    Returns:
        Decoded token dict or None if verification fails
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Token verification error: {e}")
        return None


def get_user_by_uid(uid: str):
    """
    Get Firebase user by UID.
    """
    try:
        user = auth.get_user(uid)
        return user
    except Exception as e:
        print(f"Error getting user: {e}")
        return None


def create_custom_token(uid: str):
    """
    Create a custom Firebase token for a user.
    """
    try:
        custom_token = auth.create_custom_token(uid)
        return custom_token
    except Exception as e:
        print(f"Error creating custom token: {e}")
        return None
