import datetime
import uuid
from . import chat_utils

import boto3

client = boto3.client('sts')


def user_session_state(session_state):
    if "user_id" not in session_state:
        try:
            # Try to get AWS identity first
            identity = client.get_caller_identity()
            session_state.user_id = 'aws123456'
            session_state.user_name = "AWSUser"
        except:
            # Fall back to anonymous ID if not in AWS environment
            session_state.user_id = f"anon-{str(uuid.uuid4())}"
            session_state.user_name = "Anonymous User"

    # Initialize conversation metadata if not exists
    if "conversations" not in session_state:
        session_state.conversations = chat_utils.load_all_conversations_from_dynamodb(session_state.user_id)
        # 如果没有会话，创建一个新会话
        if not session_state.conversations:
            new_conv_id = f"{session_state.user_id}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            session_state.conversations[new_conv_id] = {
                "title": "新对话",
                "created_at": datetime.datetime.now(),
                "last_message": "点击开始对话",
                "context": {}
            }
            session_state.current_conversation = new_conv_id

    if "current_conversation" not in session_state:
        # Create a new conversation by default
        new_conv_id = f"{session_state.user_id}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        session_state.conversations[new_conv_id] = {
            "title": "Chat Bot",
            "created_at": datetime.datetime.now(),
            "last_message": "点击开始对话",
            "context": {}
        }
        session_state.current_conversation = new_conv_id
