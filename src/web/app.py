import streamlit as st
import time
import json
from io import StringIO

import pandas as pd

import matplotlib.pyplot as plt

from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.utils.author_role import AuthorRole

from services.chat import chat, create_agent, create_thread, initiate_device_flow, get_aks_access_token

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

#if "agent_id" not in st.session_state:
#    with st.spinner("Creating agent..."):
#        st.session_state.agent_id = create_agent()

#if "agent_id" in st.session_state and "thread_id" not in st.session_state:
#    with st.spinner("Creating thread..."):
#        st.session_state.thread_id = create_thread(st.session_state.agent_id)

def output_formatter(content):
    try:
        content = json.loads(content)

        if content['content_type'] == "markdown":
            return content['content']

        if content['content_type'] == "dataframe":
            df = pd.read_csv(StringIO(content['content']), delimiter="|", skiprows=[1], skipinitialspace=True, engine='python')
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')].apply(lambda x: x.str.strip())

            return df

        if content['content_type'] == "matplotlib":
            return plt.figure(content['content'])

        if content['content_type'] == "image":
            return content['content']

        return content['content']

    except:
        # if the content isn't json, return it as is
        pass

    return content

#if "agent_id" in st.session_state and "thread_id" in st.session_state and "aks_cluster_name" in st.session_state and "aks_access_token" in st.session_state:
if "aks_cluster_name" in st.session_state and "aks_access_token" in st.session_state:
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
                response = chat(#agent_id=st.session_state.agent_id,
                                #thread_id=st.session_state.thread_id,
                                aks_cluster_name=st.session_state.aks_cluster_name,
                                aks_access_token=st.session_state.aks_access_token,
                                #content=question)
                                content=st.session_state.messages)

                with st.empty():
                    full_response = st.write_stream(response)
                    st.write(output_formatter(full_response))

        st.session_state.messages.add_assistant_message(full_response)

if "aks_cluster_name" not in st.session_state and "aks_access_token" not in st.session_state:
    if aks_cluster_name := st.chat_input("Enter the name of your AKS cluster to get started."):
        st.session_state.aks_cluster_name = aks_cluster_name
        st.session_state.messages.add_user_message(f"AKS cluster name: {aks_cluster_name}")

        flow = initiate_device_flow(aks_cluster_name)

        with st.chat_message(AuthorRole.ASSISTANT):
            st.write(flow["message"])

            with st.spinner("Waiting for authentication..."):
                time.sleep(30)
                st.session_state.aks_access_token = get_aks_access_token(aks_cluster_name, flow)

                st.rerun()