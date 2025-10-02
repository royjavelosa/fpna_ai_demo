import streamlit as st
import pandas as pd
from openai import OpenAI

# Page config
st.set_page_config(page_title="FP&A AI Demo", layout="wide")
# st.write("Secrets available:", list(st.secrets.keys()))


# Load API key from Streamlit secrets
if "general" not in st.secrets or "OPENAI_API_KEY" not in st.secrets["general"]:
    st.error("⚠️ OpenAI API key not found in Streamlit secrets.")
    st.stop()

client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])

st.title("📊 FP&A AI Demo")
st.write("Upload a CSV with Forecast vs Actual data, view variance analysis, and generate AI insights.")

# File upload
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    
    # Check file size (limit = 5 MB)
    max_size = 5 * 1024 * 1024  # 5 MB in bytes
    if uploaded_file.size > max_size:
        st.error("⚠️ File too large! Please upload a CSV smaller than 5 MB.")
        st.stop()
    
    try:
        # Read CSV safely
        df = pd.read_csv(uploaded_file)

        if df.empty:
            st.error("⚠️ The uploaded CSV is empty.")
            st.stop()

        st.subheader("Raw Data")
        st.dataframe(df)

        # Check expected columns
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

    except Exception as e:
        st.error(f"⚠️ Error reading CSV: {e}")
