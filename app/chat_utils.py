import datetime
from datetime import timedelta

import boto3
from langchain_community.chat_message_histories import DynamoDBChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

table_name="SessionHistoryTable"
# 添加在初始化会话状态之后，用于从DynamoDB加载所有对话
def load_all_conversations_from_dynamodb(user_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    # print(f"st.session_state.user_id:{st.session_state.user_id}")
    # 查询属于当前用户的所有会话
    response = table.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr('SessionId').begins_with(f"{user_id}-")
    )
    print(f"response:{response}")
    conversations = {}
    for item in response.get('Items', []):
        conv_id = item.get('SessionId')
        if conv_id and conv_id not in conversations:
            # 尝试从第一条消息提取标题
            history = DynamoDBChatMessageHistory(table_name=table_name, session_id=conv_id)
            print(f"history:{history}")
            messages = history.messages

            # 找出第一条用户消息作为标题
            title = "对话"
            last_message = "无消息"
            if messages:
                for msg in messages:
                    if msg.__class__.__name__ == "HumanMessage":
                        title = msg.content[:15] + "..." if len(msg.content) > 15 else msg.content
                        break

                # 获取最后一条用户消息
                for msg in reversed(messages):
                    if msg.__class__.__name__ == "HumanMessage":
                        last_message = msg.content[:20] + "..." if len(msg.content) > 20 else msg.content
                        break

            # 从会话ID中提取创建时间
            created_at = datetime.datetime.now()
            try:
                time_str = conv_id.split('-')[-1]
                created_at = datetime.datetime.strptime(time_str, '%Y%m%d%H%M%S')
            except:
                pass

            conversations[conv_id] = {
                "title": title,
                "created_at": created_at,
                "last_message": last_message,
                "context": {},  # 添加上下文字典来存储对话中的关键信息
            }

    return conversations

# Create the chat prompt template with personalized system message and improved context awareness
def get_prompt_template(user_name, context=None):
    context_str = ""
    if context and len(context) > 0:
        context_str = "对话上下文信息:\n"
        for key, value in context.items():
            context_str += f"- {key}: {value}\n"

    return ChatPromptTemplate.from_messages(
        [
            ("system", f"""你是一个有帮助的AI助手。当前用户是：{user_name}。

    {context_str}

    请记住用户在对话中提到的重要信息，并在后续回答中利用这些信息提供连贯、个性化的回应。
    回答应当简洁、准确、有帮助。尽量引用用户之前提到过的细节来表明你理解整个对话的上下文。"""),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

# 增加一个提取对话关键信息的功能
def extract_context_from_messages(messages, current_context=None):
    if current_context is None:
        current_context = {}

    # 这里可以使用更复杂的逻辑，比如NER或关键信息提取
    # 简单示例：假设问题中包含"我的名字是XXX"这样的模式就提取
    for message in messages:
        if message["role"] == "user":
            content = message["content"].lower()

            # 提取姓名
            if "我的名字是" in content or "我叫" in content:
                name_start = content.find("我的名字是")
                if name_start == -1:
                    name_start = content.find("我叫")
                    if name_start != -1:
                        name_start += 2
                else:
                    name_start += 5

                if name_start != -1:
                    name_end = content.find("。", name_start)
                    if name_end == -1:
                        name_end = len(content)
                    name = content[name_start:name_end].strip()
                    if name and len(name) < 20:  # 合理的名字长度
                        current_context["用户姓名"] = name

            # 提取兴趣爱好
            if "我喜欢" in content or "我的爱好是" in content:
                hobby_start = content.find("我喜欢")
                if hobby_start == -1:
                    hobby_start = content.find("我的爱好是")
                    if hobby_start != -1:
                        hobby_start += 5
                else:
                    hobby_start += 3

                if hobby_start != -1:
                    hobby_end = content.find("。", hobby_start)
                    if hobby_end == -1:
                        hobby_end = len(content)
                    hobby = content[hobby_start:hobby_end].strip()
                    if hobby:
                        current_context["兴趣爱好"] = hobby

    return current_context

# Get time periods for grouping conversations
def get_time_period(created_at):
    now = datetime.datetime.now()
    if created_at > now - timedelta(days=1):
        return "今天"
    elif created_at > now - timedelta(days=2):
        return "昨天"
    elif created_at > now - timedelta(days=7):
        return "7 天内"
    elif created_at > now - timedelta(days=30):
        return "30 天内"
    else:
        return "更早"