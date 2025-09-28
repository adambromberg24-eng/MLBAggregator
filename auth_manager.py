import streamlit as st
import streamlit_authenticator as stauth
import yaml
from typing import Optional, Tuple

class AuthManager:
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = config_file
        self.config = self._load_config()
        self.authenticator = stauth.Authenticate(
            self.config['credentials'],
            self.config['cookie']['name'],
            self.config['cookie']['key'],
            self.config['cookie']['expiry_days']
        )

    def _load_config(self) -> dict:
        with open(self.config_file, 'r') as file:
            return yaml.safe_load(file)

    def _save_config(self):
        with open(self.config_file, 'w') as file:
            yaml.dump(self.config, file, default_flow_style=False)

    def login(self) -> Tuple[bool, Optional[str]]:
        """Display login form and return (success, username)"""
        result = self.authenticator.login('main', 'Login')
        if result is not None:
            name, authentication_status, username = result
            return authentication_status, username
        else:
            return False, None

    def logout(self):
        """Logout the current user"""
        self.authenticator.logout('Logout', 'main')

    def register_user(self, username: str, name: str, password: str, email: str) -> bool:
        """Register a new user"""
        if username in self.config['credentials']['usernames']:
            return False  # User already exists

        # Hash the password
        hashed_password = stauth.Hasher.hash(password)

        # Add user to config
        self.config['credentials']['usernames'][username] = {
            'name': name,
            'password': hashed_password,
            'email': email
        }

        # Add to preauthorized if needed
        if email not in self.config.get('preauthorized', {}).get('emails', []):
            self.config.setdefault('preauthorized', {}).setdefault('emails', []).append(email)

        self._save_config()
        return True

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.get('authentication_status', False)

    def get_current_user(self) -> Optional[str]:
        """Get current username"""
        return st.session_state.get('username')
