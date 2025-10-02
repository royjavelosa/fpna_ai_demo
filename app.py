import streamlit as st
import pandas as pd
from io import StringIO
from openai import OpenAI
from style import apply_global_styles
import os
import plotly.express as px

# Page config
st.set_page_config(page_title="FP&A AI Demo", layout="wide")
apply_global_styles()

# 🔑 Load API key (works locally & on Heroku)
api_key = None
try:
    if "general" in st.secrets and "OPENAI_API_KEY" in st.secrets["general"]:
        api_key = st.secrets["general"]["OPENAI_API_KEY"]
    elif "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    st.error("⚠️ OpenAI API key not found. Please set it in Streamlit secrets (local) or Heroku Config Vars.")
    st.stop()

client = OpenAI(api_key=api_key)

# Title and credit
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

# Initialize session_state
if "df" not in st.session_state:
    st.session_state.df = None

MAX_FILE_SIZE_MB = 5
uploaded_file = st.file_uploader(
    f"📤 Upload CSV file — Max {MAX_FILE_SIZE_MB} MB",
    type=["csv"]
)

# Handle file upload
if uploaded_file:
    max_size = MAX_FILE_SIZE_MB * 1024 * 1024
    if uploaded_file.size > max_size:
        st.error("⚠️ File too large! Please upload a CSV smaller than 5 MB.")
        st.stop()
    try:
        df = pd.read_csv(uploaded_file)
        if df.empty:
            st.error("⚠️ The uploaded CSV is empty.")
            st.stop()
        st.session_state.df = df  # ✅ Persist in session_state
    except Exception as e:
        st.error(f"⚠️ Error reading CSV: {e}")
        st.stop()

# Handle sample data
if st.button("Use Sample Data"):
    sample_csv = """Department,Forecast,Actual
Sales,100000,95000
Marketing,50000,60000
Engineering,120000,125000
HR,30000,28000
Finance,40000,45000
"""
    df = pd.read_csv(StringIO(sample_csv))
    st.session_state.df = df  # ✅ Persist in session_state

# Always read df from session_state
df = st.session_state.df

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

        # Grouped bar chart
        st.subheader("Forecast vs Actual")
        fig = px.bar(
            df,
            x="Department",
            y=["Forecast", "Actual"],
            barmode="group",  # ✅ Side-by-side bars
            title="Forecast vs Actual by Department"
        )
        st.plotly_chart(fig, use_container_width=True)

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
