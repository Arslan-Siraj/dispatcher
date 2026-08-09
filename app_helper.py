import streamlit as st
import os
import base64

def show_app_dev_info():
    # Sidebar with logo and version
    with st.sidebar:
        
        # Spacer to push text down
        st.markdown('<div style="margin-top: 200px;"></div>', unsafe_allow_html=True)

        st.sidebar.markdown(
            """
        <div class="dispatcher-sidebar-brand">
            <div class="dispatcher-brand-icon">🚚</div>
            <div class="dispatcher-brand-copy">
                <div class="dispatcher-brand-title">DISPATCHER</div>
                <div class="dispatcher-brand-subtitle">Parcel Scan System</div>
                <div class="dispatcher-sidebar-label">NAVIGASI v1.0.1</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        logo_path = "assets/logo-removebg.png"
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
            st.markdown(f'''
            <div style="text-align: center; line-height: 1; margin-top: 20px;">
                Developed by
                <img src="data:image/png;base64,{img_data}" width="150" style="display:block; margin: 0 auto 5px auto;">
            </div>
            ''', unsafe_allow_html=True)

       
