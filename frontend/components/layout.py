"""
Layout Components
Reusable layout components for consistent UI
"""
import streamlit as st


def render_header(title: str, icon: str = "🤖"):
    """Render page header"""
    st.title(f"{icon} {title}")


def render_footer():
    """Render page footer"""
    st.divider()
    st.caption("© 2025 Assistant - Powered by AI & FastAPI")
