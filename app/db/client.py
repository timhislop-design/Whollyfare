"""app/db/client.py — WhollyFare Supabase client

Single source of truth for the database connection. Every page imports
get_client() from here rather than initialising Supabase directly.

POC:  Credentials loaded from .streamlit/secrets.toml locally,
      or from Streamlit Cloud's Secrets dashboard in deployment.
PROD: Rotate to environment variables managed by the hosting platform;
      add connection pooling (PgBouncer) and service-role key separation.

Usage:
    from app.db.client import get_client
    db = get_client()
    result = db.table("households").select("*").execute()
"""

import streamlit as st
from supabase import create_client, Client


def get_client() -> Client:
    """
    Returns a Supabase client scoped to the current Streamlit session.

    POC:  Stored in st.session_state so each browser tab gets its own client
          with its own auth JWT. This prevents cross-session JWT bleed that
          occurred when @st.cache_resource shared one client across all users.
    PROD: Same pattern — per-session client is correct for user-facing auth.
          Add a separate module-level service-role client for admin/batch ops.
    """
    if "_supabase_client" not in st.session_state:
        url: str = st.secrets["supabase"]["url"]
        key: str = st.secrets["supabase"]["anon_key"]
        st.session_state["_supabase_client"] = create_client(url, key)
    return st.session_state["_supabase_client"]


def test_connection() -> bool:
    """
    Quick sanity check — returns True if the DB is reachable.
    Used on the Admin page and during onboarding to surface connection errors early.

    POC:  Reads one row from feature_flags (public, no auth required).
    PROD: Replace with a dedicated health-check endpoint or a lightweight ping.
    """
    try:
        client = get_client()
        client.table("feature_flags").select("id").limit(1).execute()
        return True
    except Exception:
        return False
