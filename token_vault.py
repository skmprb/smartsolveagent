import json
import os
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

class TokenVault:
    def __init__(self, storage_file="tokens.json"):
        self.storage_file = storage_file
        self._ensure_storage()
    
    def _ensure_storage(self):
        if not os.path.exists(self.storage_file):
            with open(self.storage_file, 'w') as f:
                json.dump({}, f)
    
    def store_token(self, user_id, credentials):
        tokens = self._load_tokens()
        tokens[user_id] = {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "expires_at": credentials.expiry.isoformat() if credentials.expiry else None
        }
        self._save_tokens(tokens)
    
    def get_token(self, user_id):
        tokens = self._load_tokens()
        if user_id not in tokens:
            return None
        
        token_data = tokens[user_id]
        credentials = Credentials(
            token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self._get_client_id()
        )
        
        # Refresh if expired
        if credentials.expired:
            credentials.refresh(Request())
            self.store_token(user_id, credentials)
        
        return credentials
    
    def _load_tokens(self):
        with open(self.storage_file, 'r') as f:
            return json.load(f)
    
    def _save_tokens(self, tokens):
        with open(self.storage_file, 'w') as f:
            json.dump(tokens, f)
    
    def _get_client_id(self):
        with open("client-secret.json", 'r') as f:
            return json.load(f)["web"]["client_id"]