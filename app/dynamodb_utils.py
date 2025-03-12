from langchain_community.chat_message_histories import DynamoDBChatMessageHistory
from . import chat_utils


def init_history_message(table_name, current_session_id):
    history = DynamoDBChatMessageHistory(table_name=table_name, session_id=current_session_id)
    return history


def select_history_message(session_state, history, current_id):
    print(f"select_history_message:{history}")
    if "messages" not in session_state:
        session_state.messages = []

        # Load the stored messages from DynamoDB
        stored_messages = history.messages  # Retrieve all stored messages

        # Populate the session state with the retrieved messages
        for msg in stored_messages:
            role = "user" if msg.__class__.__name__ == "HumanMessage" else "assistant"
            session_state.messages.append({"role": role, "content": msg.content})

        # 提取上下文信息并更新到会话元数据
        if session_state.messages:
            updated_context = chat_utils.extract_context_from_messages(
                session_state.messages,
                session_state.conversations[current_id].get("context", {})
            )
            session_state.conversations[current_id]["context"] = updated_context
