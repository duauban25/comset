import os
import sys

# Ensure local imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import main
    main()
except Exception as e:
    # Graceful fallback UI
    import streamlit as st
    st.set_page_config(page_title="CompSet Dashboard — Error", layout="wide")
    st.error("🚨 Aplikasi gagal saat start.")
    st.write("**Error:**")
    st.code(f"{type(e).__name__}: {str(e)[:200]}")
    st.markdown("---")
    st.markdown("**Saran:**")
    st.markdown("- Set Secret `DATA_DIR = /mount/data` di Streamlit Cloud.")
    st.markdown("- Klik 'Restart and clear cache' di menu Manage app.")
