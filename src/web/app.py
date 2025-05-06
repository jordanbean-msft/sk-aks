import json
import time
import asyncio
import threading
import time
from services.chat import realtime, transcribe


import streamlit as st
from streamlit_extras.bottom_container import bottom

from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents import ImageContent, TextContent, ChatMessageContent

from models.chat_output import ChatOutput, deserialize_chat_output
from models.content_type_enum import ContentTypeEnum
from services.chat import chat, get_thread, get_image, get_image_contents, create_thread, realtime
from utilities import output_formatter

st.set_page_config(
    page_title="AKS AI Assistant",
    page_icon=":robot_face:",
    layout="centered",
    initial_sidebar_state="expanded",
)

def _handle_user_interaction():
    st.session_state["waiting_for_response"] = True

if "waiting_for_response" not in st.session_state:
    st.session_state["waiting_for_response"] = False

with open('assets/css/style.css', encoding='utf-8') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html = True)

st.image("assets/images/aks.svg", width=192)
st.title("AKS AI Assistant")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = ChatHistory()

if "thread_id" not in st.session_state:
    with st.spinner("Creating thread..."):
        thread_id = create_thread()
        st.session_state.thread_id = thread_id

def render_response(response):
    full_delta_content = ""
    images = []
    for chunk in response:
        delta = deserialize_chat_output(json.loads(chunk))

        if delta and delta.content:
            if delta.content_type == ContentTypeEnum.MARKDOWN:
                full_delta_content += delta.content

                # Display the content incrementally
                # if delta.content.startswith("```python"):
                #     st.code(full_delta_content, language="python")
                # elif delta.content.startswith("```"):
                #     st.code(full_delta_content)
                # else:
                st.markdown(full_delta_content)                                    
            elif delta.content_type == ContentTypeEnum.FILE:
                image = get_image(file_id=delta.content)
                st.image(image=image, use_container_width=True)
                images.append(image)                                

    st.session_state.messages.add_assistant_message(full_delta_content)

    for image in images:
        content = ChatMessageContent(
                                    role=AuthorRole.ASSISTANT,
                                    items=[
                                        ImageContent(data=image)
                                    ]    
                                )
        st.session_state.messages.add_message(content)                 

@st.fragment
def response(question):
    # Display assistant response in chat message container
    with st.chat_message(AuthorRole.ASSISTANT):
        with st.spinner("Reticulating splines..."):
            response = chat(thread_id=st.session_state.thread_id,
                            aks_cluster_name=st.session_state.aks_cluster_name,
                            content=question)

            with st.empty():
                render_response(response)

@st.fragment
def display_chat_history():
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message.role):
            for item in message.items:
                if isinstance(item, TextContent):
                    st.write(item.text)
                elif isinstance(item, ImageContent):
                    st.image(item.data, use_container_width=True)
                else:
                    raise TypeError(f"Unknown content type: {type(item)}")
                
@st.fragment
def audio_chat():
    if audio := st.audio_input("Record audio"):
        question_text = ""
        with st.chat_message(AuthorRole.USER):
            with st.spinner("Transcribing..."):
                audio_transcription = transcribe(content=audio)

                with st.empty():
                    question_text = str(audio_transcription)
                    
                    st.markdown(question_text)
                            
                st.session_state.messages.add_user_message(question_text)

        response(question_text)

if "aks_cluster_name" not in st.session_state:
    if aks_cluster_name := st.chat_input("Enter the name of your AKS cluster to get started."):
        st.session_state.aks_cluster_name = aks_cluster_name
        st.session_state.messages.add_user_message(f"AKS cluster name: {aks_cluster_name}")
        st.rerun()

if "aks_cluster_name" in st.session_state and "thread_id" in st.session_state:
    with st.sidebar:
        st.subheader(body="Thread ID", divider=True)
        st.write(st.session_state.thread_id)

    display_chat_history()
   
    if question := st.chat_input(
        placeholder="Ask me...",
        on_submit=_handle_user_interaction,
        disabled=st.session_state["waiting_for_response"],
    ):
        # Add user message to chat history
        st.session_state.messages.add_user_message(question)
        # Display user message in chat message container
        with st.chat_message(AuthorRole.USER):
            st.markdown(question)

        response(question)
    # with bottom():
    #     audio_chat()
       
if st.session_state["waiting_for_response"]:
    st.session_state["waiting_for_response"] = False
    st.rerun()

    # # Display chat messages from history on app rerun
    # for message in st.session_state.messages:
    #     with st.chat_message(message.role):
    #         #st.write(output_formatter(message.content))
    #         st.write(message.content)

    # # Accept user input
    # if question := st.chat_input("Ask me about your AKS cluster..."):
    #     # Add user message to chat history
    #     st.session_state.messages.add_user_message(question)
    #     # Display user message in chat message container
    #     with st.chat_message(AuthorRole.USER):
    #         st.markdown(question)

    #     # Display assistant response in chat message container
    #     with st.chat_message("assistant"):
    #         with st.spinner("Thinking..."):
    #             response = chat(aks_cluster_name=st.session_state.aks_cluster_name,
    #                             thread_id=st.session_state.thread_id,
    #                             content=st.session_state.messages)

    #             with st.empty():
    #                 full_response = st.write_stream(response)
    #                 #st.write(output_formatter(full_response))

    #     st.session_state.messages.add_assistant_message(full_response)

    #     image_contents = get_image_contents(thread_id=st.session_state.thread_id)

    #     for image_content in image_contents:
    #         if image_content["type"] == "image_file":
    #             image = get_image(file_id=image_content["file_id"])

    #             st.image(image=image, use_container_width=True)
