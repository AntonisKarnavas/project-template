"""
Firebase Admin SDK Configuration

This module initializes the Firebase Admin SDK for backend authentication.
Place your Firebase service account JSON file in the backend directory.
"""
import os
from pathlib import Path

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials


# Initialize Firebase Admin SDK
def initialize_firebase():
    """
    Initialize Firebase Admin SDK with service account credentials.

    You need to:
    1. Go to Firebase Console > Project Settings > Service Accounts
    2. Click "Generate New Private Key"
    3. Save the JSON file as 'firebase-service-account.json' in the backend directory
    4. Or set FIREBASE_SERVICE_ACCOUNT_PATH in your .env file
    """
    if not firebase_admin._apps:
        # Check if service account file exists
        service_account_path = os.getenv(
            "FIREBASE_SERVICE_ACCOUNT_PATH",
            str(Path(__file__).parent.parent / "firebase-service-account.json"),
        )

        if not os.path.exists(service_account_path):
            raise FileNotFoundError(
                f"Firebase service account file not found at: {service_account_path}\n"
                f"Please download it from Firebase Console > Project Settings > Service Accounts"
            )

        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized successfully")


def verify_firebase_token(id_token: str) -> dict:
    """
    Verify a Firebase ID token from the client.

    Args:
        id_token: The Firebase ID token from the client

    Returns:
        dict: The decoded token containing user info (uid, email, etc.)

    Raises:
        firebase_admin.auth.InvalidIdTokenError: If token is invalid
        firebase_admin.auth.ExpiredIdTokenError: If token is expired
    """
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        raise e


def get_user_by_uid(uid: str):
    """Get Firebase user by UID"""
    try:
        return firebase_auth.get_user(uid)
    except Exception as e:
        raise e
