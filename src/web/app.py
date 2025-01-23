import streamlit as st
import time
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
    st.session_state.messages = []

if "agent_id" not in st.session_state:
    with st.spinner("Creating agent..."):
        st.session_state.agent_id = create_agent()

if "agent_id" in st.session_state and "thread_id" not in st.session_state:
    with st.spinner("Creating thread..."):
        st.session_state.thread_id = create_thread(st.session_state.agent_id)

if "agent_id" in st.session_state and "thread_id" in st.session_state and "aks_cluster_name" in st.session_state and "aks_access_token" in st.session_state:
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Accept user input
    if question := st.chat_input("Ask me about your AKS cluster..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": question})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(question)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = chat(agent_id=st.session_state.agent_id,
                                thread_id=st.session_state.thread_id,
                                aks_cluster_name=st.session_state.aks_cluster_name,
                                aks_access_token=st.session_state.aks_access_token,
                                content=question)
                full_response = st.write_stream(response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})

if "aks_cluster_name" not in st.session_state and "aks_access_token" not in st.session_state:
    if aks_cluster_name := st.chat_input("Enter the name of your AKS cluster to get started."):
        st.session_state.aks_cluster_name = aks_cluster_name
        st.session_state.messages.append({"role": "user", "content": f"AKS cluster name: {aks_cluster_name}"})

        flow = initiate_device_flow(aks_cluster_name)

        with st.chat_message(name="assistant"):
            st.write(flow["message"])

            with st.spinner("Waiting for authentication..."):
                time.sleep(30)
                st.session_state.aks_access_token = get_aks_access_token(aks_cluster_name, flow)


                st.rerun()