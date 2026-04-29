import streamlit as st
from strategy_advisor import run_strategy_session

st.set_page_config(page_title="AI Strategy Advisor", layout="centered")

st.title("AI Multi-Agent Strategy Advisor")

question = st.text_input(
    "Enter your strategy question",
    "We want high engagement with limited budget"
)

org = st.selectbox(
    "Select organization type",
    ["student", "business", "nonprofit", "university"]
)

if st.button("Generate Strategy"):

    result = run_strategy_session(question, org)

    st.subheader("Final Recommendation")
    st.success(result["winner"])

    st.subheader("Confidence Level")
    st.write(f"{result['confidence']}%")

    st.subheader("Votes")
    st.json(result["votes"])

    st.subheader("Calculated Scores")
    st.json(result["scores"])
