"""
Firebase Authentication utilities for FastAPI
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from typing import Optional

security = HTTPBearer(auto_error=False)  # auto_error=False makes it optional


class FirebaseUser:
    """
    Simple class to represent a Firebase authenticated user
    """
    def __init__(self, uid: str, email: str, name: Optional[str] = None):
        self.uid = uid
        self.email = email
        self.name = name or email.split('@')[0]


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> FirebaseUser:
    """
    Dependency to get the current authenticated Firebase user.
    
    The frontend should send the Firebase ID token in the Authorization header:
    Authorization: Bearer <firebase_id_token>
    
    Args:
        credentials: HTTP Bearer token from request header
        
    Returns:
        FirebaseUser object with user information
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    if not credentials or not hasattr(credentials, "credentials"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials",
        )

    token = credentials.credentials

    try:
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(token)

        # Extract user information
        uid = decoded_token.get('uid')
        email = decoded_token.get('email', 'unknown@example.com')
        name = decoded_token.get('name')

        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )

        return FirebaseUser(uid=uid, email=email, name=name)

    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[FirebaseUser]:
    """
    Dependency to get the current user if authenticated, or None if not.
    Used for endpoints that work with or without authentication.
    This won't raise an error if no credentials are provided.
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        
        uid = decoded_token.get('uid')
        email = decoded_token.get('email', 'unknown@example.com')
        name = decoded_token.get('name')
        
        if uid:
            return FirebaseUser(uid=uid, email=email, name=name)
        return None
    except Exception as e:
        # Silently return None if token verification fails
        print(f"Optional auth failed (this is OK): {e}")
        return None
