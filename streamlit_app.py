import os
import sys

# Ensure local imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Importing app will execute the Streamlit app since it runs at top-level
    import app  # noqa: F401
except Exception as e:
    # Graceful fallback UI so the app still shows something on Cloud
    import streamlit as st
    st.set_page_config(page_title="CompSet Dashboard — Fallback", layout="wide")
    st.error("🚨 Aplikasi gagal saat start. Menampilkan halaman fallback.")
    st.write("Detail error ringkas:")
    st.code(f"{type(e).__name__}: {e}")
    st.markdown("---")
    st.markdown("**Langkah saran:**")
    st.markdown("- Pastikan file `app.py` tidak mengandalkan variabel lingkungan yang belum diset.")
    st.markdown("- Jika butuh direktori tulis, set Secret `DATA_DIR` ke path writable (contoh: `/mount/data`).")
    st.markdown("- Coba Restart and clear cache dari menu Manage app.")

if __name__ == "__main__":
    # Nothing needed; Streamlit runs on import or fallback
    pass
