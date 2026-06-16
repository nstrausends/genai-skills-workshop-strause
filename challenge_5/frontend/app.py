"""Streamlit demo website for the Alaska Department of Snow agent.

Requirement: "Generative AI agent deployed to a website." A minimal chat page
(question box, submit, answer) that calls the deployed Agent Engine app.

Run:  uv run streamlit run frontend/app.py   (requires ADS_AGENT_ENGINE_RESOURCE in .env)
"""

import streamlit as st

from ads_agent import config, remote

st.set_page_config(page_title="Alaska Department of Snow", page_icon="❄️")
st.title("❄️ Alaska Department of Snow — Resident Assistant")
st.caption("Ask about plowing, school/road closures, winter prep, and current conditions.")

if not config.AGENT_ENGINE_RESOURCE:
    st.error("ADS_AGENT_ENGINE_RESOURCE is not set in .env. Deploy the agent first.")
    st.stop()

if "history" not in st.session_state:
    st.session_state.history = []

for role, text in st.session_state.history:
    with st.chat_message(role):
        st.markdown(text)

if question := st.chat_input("Ask a question..."):
    st.session_state.history.append(("user", question))
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Checking ADS resources..."):
            answer = remote.query_agent(question)
        st.markdown(answer)
    st.session_state.history.append(("assistant", answer))
