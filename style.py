import streamlit as st

def apply_global_styles():
    st.markdown("""
        <style>
            /* Hide Streamlit's default file uploader hint (200MB limit text) */
            div[data-testid="stFileUploader"] small { display: none !important; }

            /* Optional UI polish */
            button:focus {
                outline: none !important;
                box-shadow: 0 0 0 2px #4CAF50 !important;
            }

            button:hover {
                border: 1px solid #4CAF50 !important;
                box-shadow: 0 0 0 2px #4CAF50 !important;
                color: #4CAF50 !important;
            }
        </style>
    """, unsafe_allow_html=True)
