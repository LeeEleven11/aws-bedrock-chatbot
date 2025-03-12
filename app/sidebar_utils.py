import datetime

from . import chat_utils


def render_sidebar(st):
    # Use sidebar instead of columns
    with st.sidebar:
        # New conversation button at the top
        if st.button("🔄 开启新对话", use_container_width=True, type="primary"):
            new_conv_id = f"{st.session_state.user_id}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            st.session_state.conversations[new_conv_id] = {
                "title": "新对话",
                "created_at": datetime.datetime.now(),
                "last_message": "点击开始对话",
                "context": {}
            }
            st.session_state.current_conversation = new_conv_id
            if "messages" in st.session_state:
                del st.session_state.messages
            st.rerun()

        # Group conversations by time periods
        st.header("对话历史")
        grouped_conversations = {}
        # conversations = chat_utils.load_all_conversations_from_dynamodb()
        for conv_id, conv_data in st.session_state.conversations.items():
            period = chat_utils.get_time_period(conv_data["created_at"])
            if period not in grouped_conversations:
                grouped_conversations[period] = []
            grouped_conversations[period].append((conv_id, conv_data))

        # Display conversations grouped by time
        for period, convs in sorted(grouped_conversations.items()):
            st.markdown(f"### {period}")
            for conv_id, conv_data in sorted(convs, key=lambda x: x[1]["created_at"], reverse=True):
                # Create a button that looks like text for each conversation
                is_current = conv_id == st.session_state.current_conversation
                button_style = "primary" if is_current else "secondary"

                if st.button(
                        f"{conv_data['title']}\n{conv_data['last_message']}",
                        key=f"conv_{conv_id}",
                        use_container_width=True,
                        type=button_style
                ):
                    st.session_state.current_conversation = conv_id
                    if "messages" in st.session_state:
                        del st.session_state.messages
                    st.rerun()

            st.markdown("---")
