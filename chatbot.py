import logging

import boto3
import streamlit as st
from langchain.text_splitter import TokenTextSplitter
from langchain_core.output_parsers import StrOutputParser

from app.chat_utils import get_prompt_template, extract_context_from_messages
from app.dynamodb_utils import init_history_message, select_history_message
from app.langchain_utils import create_chat_model, create_chain_with_history
from app.sidebar_utils import render_sidebar
from app.user_utils import user_session_state

table_name = "SessionHistoryTable"
client = boto3.client('sts')
logging.basicConfig(level=logging.CRITICAL)

# Initialize session state for user management
user_session_state(st.session_state)

# Create bedrock model with improved parameters for better multi-turn conversations
model = create_chat_model()

# Use sidebar instead of columns
# 渲染侧边栏
render_sidebar(st)

# Main chat interface
current_id = st.session_state.current_conversation

st.title(f"ChatBot")

# Get current session ID
# current_session_id = current_id
history = init_history_message(table_name, current_id)

# Create dynamic prompt based on current user and context
prompt_template = get_prompt_template(
    st.session_state.user_name,
    context=st.session_state.conversations[current_id].get("context", {})
)

# Combine the prompt with the Bedrock LLM
chain = prompt_template | model | StrOutputParser()

# 使用更大的窗口来处理历史消息
text_splitter = TokenTextSplitter(chunk_size=3500)

# Integrate with message history
chain_with_history = create_chain_with_history(chain, table_name)

# Load messages from DynamoDB and populate chat history

# print(f"main_history:{history}")
select_history_message(st.session_state, history, current_id)

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("有什么我可以帮你的？"):
    # Update conversation title if this is the first message
    if len(st.session_state.messages) == 0:
        # Use the first 15 characters of user input as the conversation title
        title = prompt[:15] + "..." if len(prompt) > 15 else prompt
        st.session_state.conversations[current_id]["title"] = title

    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 更新上下文信息
    updated_context = extract_context_from_messages(
        [{"role": "user", "content": prompt}],
        st.session_state.conversations[current_id].get("context", {})
    )
    st.session_state.conversations[current_id]["context"] = updated_context

    # 更新提示模板以包含最新的上下文
    prompt_template = get_prompt_template(
        st.session_state.user_name,
        context=updated_context
    )
    chain = prompt_template | model | StrOutputParser()

    chain_with_history = create_chain_with_history(chain, table_name)

    # Generate assistant response using Bedrock LLM and LangChain
    config = {"configurable": {"session_id": current_id}}
    print(f"current_chat_prompt:{prompt}")

    # 显示加载状态
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("思考中...")

    response = chain_with_history.invoke({"question": prompt}, config=config)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder.markdown(response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

    # Update the last message preview in the conversation list
    st.session_state.conversations[current_id]["last_message"] = prompt[:20] + "..." if len(prompt) > 20 else prompt

    st.rerun()
