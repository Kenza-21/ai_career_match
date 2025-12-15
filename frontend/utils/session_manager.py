"""
Session Management Utilities
Handles user session state and persistence
"""
import uuid
import streamlit as st
from typing import Optional


class SessionManager:
    """Manages user session state"""
    
    @staticmethod
    def get_session_id() -> str:
        """Get or create session ID"""
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        return st.session_state.session_id
    
    @staticmethod
    def get_last_response() -> Optional[dict]:
        """Get last API response"""
        return st.session_state.get("last_response")
    
    @staticmethod
    def set_last_response(response: dict):
        """Store last API response"""
        st.session_state.last_response = response
    
    @staticmethod
    def clear_last_response():
        """Clear last API response"""
        if "last_response" in st.session_state:
            del st.session_state.last_response

