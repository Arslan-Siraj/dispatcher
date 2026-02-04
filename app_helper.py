import streamlit as st
import os
import base64

def show_app_dev_info():
    # Sidebar with logo and version
    with st.sidebar:
        
        # Spacer to push text down
        st.markdown('<div style="margin-top: 400px;"></div>', unsafe_allow_html=True)

        logo_path = "assets/logo-removebg.png"
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
            st.markdown(f'''
            <div style="text-align: center; line-height: 1; margin-top: 20px;">
                <img src="data:image/png;base64,{img_data}" width="150" style="display:block; margin: 0 auto 5px auto;">
            </div>
            ''', unsafe_allow_html=True)

        # Developed by + version
        st.markdown('''
        <div style="text-align: center; color: #AAAAAA; font-size: 14px;">
            Developed by<br>
            DispatcherApp v1.0.0
        </div>
        ''', unsafe_allow_html=True)