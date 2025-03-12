from langchain_aws import ChatBedrockConverse
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import DynamoDBChatMessageHistory
# 创建 Bedrock 模型
def create_chat_model():
    model = ChatBedrockConverse(
        model="amazon.nova-lite-v1:0",
        max_tokens=4096,  # 增加最大token数
        temperature=0.0,  # 适度增加创造性
        top_p=0.9,
        stop_sequences=["\n\nHuman"],
        verbose=True
    )
    return model

# 集成消息历史
def create_chain_with_history(chain, table_name):
    chain_with_history = RunnableWithMessageHistory(
        chain,
        lambda session_id: DynamoDBChatMessageHistory(
            table_name=table_name, session_id=session_id
        ),
        input_messages_key="question",
        history_messages_key="history",
    )
    return chain_with_history