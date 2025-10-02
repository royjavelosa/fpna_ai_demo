import streamlit as st
import pandas as pd
from io import StringIO
from openai import OpenAI
from style import apply_global_styles 
import os

# Page config
st.set_page_config(page_title="FP&A AI Demo", layout="wide")
apply_global_styles()

# 🔑 Load API key (works locally & on Heroku)
api_key = None
try:
    # Check: Local secrets.toml (Elesi style)
    if "general" in st.secrets and "OPENAI_API_KEY" in st.secrets["general"]:
        api_key = st.secrets["general"]["OPENAI_API_KEY"]
    elif "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    # Check: If st.secrets not available, fall back to Heroku env vars
    api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    st.error("⚠️ OpenAI API key not found. Please set it in Streamlit secrets (local) or Heroku Config Vars.")
    st.stop()

client = OpenAI(api_key=api_key)

# Title and description
st.title("📊 FP&A AI Demo")

st.markdown(
    """
    <div style="font-size: 0.95em; color: #aaa; margin-bottom: 20px;">
        Built with ❤️ by 
        <a href="https://www.linkedin.com/in/royjavelosa" target="_blank" style="color:#4CAF50; text-decoration:none; font-weight:600;">
        Roy Javelosa</a>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("Upload a CSV with Forecast vs Actual data, or use sample data to test the app.")

# File upload (custom label to override Streamlit’s default 200MB text)
MAX_FILE_SIZE_MB = 5
uploaded_file = st.file_uploader(
    f"📤 Upload CSV file — Max {MAX_FILE_SIZE_MB} MB",
    type=["csv"]
)

use_sample = st.button("Use Sample Data")

df = None

if uploaded_file:
    # File size check
    max_size = MAX_FILE_SIZE_MB * 1024 * 1024  # 5 MB
    if uploaded_file.size > max_size:
        st.error("⚠️ File too large! Please upload a CSV smaller than 5 MB.")
        st.stop()

    try:
        df = pd.read_csv(uploaded_file)
        if df.empty:
            st.error("⚠️ The uploaded CSV is empty.")
            st.stop()
    except Exception as e:
        st.error(f"⚠️ Error reading CSV: {e}")
        st.stop()

elif use_sample:
    st.info("ℹ️ Using built-in sample dataset. You can also download it below to prepare your own file.")
    sample_csv = """Department,Forecast,Actual
Sales,100000,95000
Marketing,50000,60000
Engineering,120000,125000
HR,30000,28000
Finance,40000,45000
"""
    df = pd.read_csv(StringIO(sample_csv))
    
    # Allow download of the sample CSV
    st.download_button(
        label="📥 Download Sample CSV",
        data=sample_csv,
        file_name="sample_fpna.csv",
        mime="text/csv",
    )

    st.info("💡 Tip: Upload your own CSV using the same column pattern from the Sample CSV (Department, Forecast, Actual).")

# If we have data (uploaded or sample), continue
if df is not None:
    st.subheader("Raw Data")
    st.dataframe(df)

    required_cols = {"Department", "Forecast", "Actual"}
    if required_cols.issubset(df.columns):
        # Variance calculations
        df["Variance"] = df["Actual"] - df["Forecast"]
        df["Variance %"] = ((df["Variance"] / df["Forecast"]) * 100).round(2)

        st.subheader("Variance Analysis")
        st.dataframe(df)

        # Bar chart
        st.subheader("Forecast vs Actual")
        st.bar_chart(df.set_index("Department")[["Forecast", "Actual"]])

        # --- AI Analysis ---
        st.subheader("🤖 AI-Generated Insights")
        data_str = df.to_csv(index=False)

        if st.button("Generate Analysis"):
            with st.spinner("Analyzing with AI..."):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an FP&A analyst."},
                        {
                            "role": "user",
                            "content": f"""
                            Analyze this financial data. Highlight key variances,
                            explain possible reasons, and suggest one action for next quarter.

                            Data:
                            {data_str}
                            """
                        },
                    ],
                )
                ai_text = response.choices[0].message.content
                st.markdown(ai_text)
    else:
        st.error(f"CSV must contain columns: {', '.join(required_cols)}")
