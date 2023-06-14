import streamlit as st
import os
from pandasai import PandasAI
from pandasai.llm.openai import OpenAI
import pandas as pd
import requests
import json
import re

# Configure Streamlit Page
page_icon = (
    "https://cdn.iconscout.com/icon/premium/png-256-thumb/openai-1523664-1290202.png"
)
st.set_page_config(page_title="Web3 AI Analyst", page_icon=page_icon, layout="wide")

# Read Custom CSS
with open("assets/css/style.css", "r") as f:
    css_text = f.read()
custom_css = f"<style>{css_text}</style>"
st.markdown(custom_css, unsafe_allow_html=True)

# OpenAI "powered by" component
powered_by = """
<div style="display: flex; align-items: center; margin-bottom:20px">
    <span style="font-size: 14px; margin-right: 4px; font-style: italic;">Powered by:</span>
    <img src="https://www.freelogovectors.net/wp-content/uploads/2023/01/openai-logo-freelogovectors.net_.png" alt="OpenAI logo" height="24">
</div>
"""

# Get API Keys
openai_api_key = os.environ["OPENAI_KEY"]
dune_api_key = os.environ["DUNE_KEY"]

# Heading
st.write(
    f"""<h1>
            <img src="https://dune.com/assets/DuneLogoCircle.svg" alt="OpenAI logo" height="36" style="margin-bottom:6px">
            <img src="https://avatars.githubusercontent.com/u/32752226?s=280&v=4" alt="OpenAI logo" height="36" style="margin-bottom:6px">              
            Web3 AI Analyst
        </h1>""",
    unsafe_allow_html=True,
)
st.subheader("Analyze any Web3 dataset using natural language")
st.markdown(powered_by, unsafe_allow_html=True)


# Query Dune Analytics using API
def query_dune(q):
    url = f"https://api.dune.com/api/v1/query/{q}/results?api_key={dune_api_key}"
    response = requests.get(url)
    results_json = json.loads(response.text)["result"]["rows"]
    results_df = pd.DataFrame.from_dict(results_json)
    return results_df


# Query Flipside Crypto using API
def query_flipside(q):
    query_api_url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    results_json = requests.get(query_api_url).json()
    results_df = pd.DataFrame.from_dict(results_json)
    return results_df


def run_query(q, provider):
    # Dictionary of provider names and their respective query functions
    provider_query = {
        "Flipside": query_flipside,
        "Dune": query_dune,
    }
    df = provider_query[provider](q)
    return df


# Initialize Session State
if "df" not in st.session_state:
    st.session_state["df"] = ""

col1, col2 = st.columns(2)

# Query Dune
with col1:
    provider = st.selectbox("(1a) Select Provider", ["Dune", "Flipside"])
    query = st.text_input("(1b) Enter a Query Id.")
    with st.expander("Example Query Ids:"):
        st.write("Helium device onboards by maker (Dune, @HeliumFndn): `2470060`")
        st.write(
            "Helium device mints by type (Flipside, @fknmarqu): `82c8b727-2c82-45f4-a1d3-fde2ce8a3fe1`"
        )
    submit_query = st.button("Query Data")
    if submit_query:
        st.session_state.df = run_query(query, provider)
        st.table(st.session_state.df.head())
    elif isinstance(st.session_state.df, pd.DataFrame):
        st.table(st.session_state.df.head())

# Ask Question
with col2:
    # Setup Pandas AI
    llm = OpenAI(openai_api_key)
    pandas_ai = PandasAI(llm, save_charts=True)

    # Analyze Data
    question = st.text_input("(2) Ask a question or plot results.")
    with st.expander("Example Questions:"):
        st.code("Plot the total number of num_onboarded by maker_name.")
        st.code("What is the total number of MINTS by DEVICE_NAME?")
    submit_question = st.button("Analyze Data")

    if submit_question:
        answer = pandas_ai(st.session_state.df, prompt=question)
        try:
            # Display image if generated
            pattern = r"Charts saved to: (.*)"
            file_path = re.search(pattern, answer).group(1)
            st.image(f"{file_path}/chart.png")
        except:
            # Otherwise display text
            st.write("Answer:", answer)
