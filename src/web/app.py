import os
import streamlit as st
import requests
import uuid

#with open('style.css', encoding='utf-8') as f:
#    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html = True)

#st.image("logo.svg", width=192)
st.title("AI Assistant")

base_url = os.getenv("API_BASE_URL")

def chat(thread_id, user_prompt):
    for event in requests.post(url=f"{base_url}/v1/chat",
                               json={ "thread_id": thread_id,
                                   "message": user_prompt},
                               stream=True,
                               timeout=30):
        yield event.decode('utf-8')

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if 'thread_id' not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Accept user input
if prompt := st.chat_input(""):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

# Display assistant response in chat message container
    with st.chat_message("assistant"):
        response = chat(st.session_state.thread_id, prompt)
        full_response = st.write_stream(response)

    st.session_state.messages.append(
            {"role": "assistant", "content": full_response})
