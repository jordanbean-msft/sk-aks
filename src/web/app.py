import streamlit as st
from chat import chat, create_agent, create_thread

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
            response = chat(st.session_state.agent_id, st.session_state.thread_id, question)
            full_response = st.write_stream(response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
