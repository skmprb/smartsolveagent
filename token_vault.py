import json
import os
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.cloud import firestore

class TokenVault:
    def __init__(self):
        self.db = firestore.Client(database='smartsolve')
        self.collection = 'user_tokens'
    
    def store_token(self, user_email, credentials):
        doc_ref = self.db.collection(self.collection).document(user_email)
        doc_ref.set({
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
    
    def get_token(self, user_email):
        doc_ref = self.db.collection(self.collection).document(user_email)
        doc = doc_ref.get()
        
        if not doc.exists:
            return None
        
        token_data = doc.to_dict()
        credentials = Credentials(
            token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self._get_client_id()
        )
        
        # Refresh if expired
        if credentials.expired:
            credentials.refresh(Request())
            self.store_token(user_email, credentials)
        
        return credentials
    
    def _get_client_id(self):
        with open("client-secret.json", 'r') as f:
            return json.load(f)["web"]["client_id"]