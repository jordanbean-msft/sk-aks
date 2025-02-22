import time

import streamlit as st

from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.utils.author_role import AuthorRole

from services.chat import chat, initiate_device_flow, get_aks_access_token
from utilities import output_formatter

st.set_page_config(
    page_title="AKS AI Assistant",
    page_icon=":robot_face:",
    layout="centered",
    initial_sidebar_state="expanded",
)

with open('assets/css/style.css', encoding='utf-8') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html = True)

st.image("assets/images/aks.svg", width=192)
st.title("AKS AI Assistant")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = ChatHistory()

if "aks_cluster_name" in st.session_state:
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message.role):
            st.write(output_formatter(message.content))

    # Accept user input
    if question := st.chat_input("Ask me about your AKS cluster..."):
        # Add user message to chat history
        st.session_state.messages.add_user_message(question)
        # Display user message in chat message container
        with st.chat_message(AuthorRole.USER):
            st.markdown(question)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = chat(aks_cluster_name=st.session_state.aks_cluster_name,
                                aks_access_token=st.session_state.aks_access_token,
                                content=st.session_state.messages)

                with st.empty():
                    full_response = st.write_stream(response)
                    st.write(output_formatter(full_response))

        st.session_state.messages.add_assistant_message(full_response)
