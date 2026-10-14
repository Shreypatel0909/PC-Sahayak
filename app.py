import base64
import streamlit as st
from groq import Groq, APIError, AuthenticationError, RateLimitError

st.set_page_config(
    page_title="PC Sahayak",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1100px;
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    .subtitle {
        color: #9ca3af;
        margin-top: -10px;
    }
    [data-testid="stChatMessage"] {
        border-radius: 16px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.75rem;
    }
    [data-testid="stChatMessage"] [data-testid="stChatMessageContent"] {
        min-width: 0;
        line-height: 1.65;
    }
    [data-testid="stChatMessage"] {
        width: 100%;
        box-sizing: border-box;
    }
    [data-testid="stChatMessage"] ul,
    [data-testid="stChatMessage"] ol {
        padding-left: 1.4rem;
        margin-top: 0.4rem;
        margin-bottom: 0.8rem;
    }
    [data-testid="stChatInput"] {
        border-radius: 18px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    api_ready = True
except Exception:
    client = None
    api_ready = False

TEXT_MODEL = "openai/gpt-oss-20b"
VISION_MODEL = "qwen/qwen3.8-27b"

SYSTEM_PROMPT = """
You are PC Sahayak, a friendly Windows PC troubleshooting assistant.

Help users diagnose Windows PC problems using their messages and screenshots.

Rules:
1. Use simple, beginner-friendly English.
2. Remember the conversation history.
3. Ask one focused diagnostic question at a time when needed.
4. Give one or two safe steps at a time.
5. Avoid repeating steps already explained.
6. If an image is attached, describe relevant visible details.
7. Distinguish what is visible in a screenshot from what you infer.
8. Never claim to access or control the user's computer.
9. Never ask users to expose passwords, API keys, or private data.
10. Avoid risky registry edits and destructive commands.
11. Warn users before steps that may cause data loss.
12. If a screenshot is unclear, explain what cannot be identified.
13. Keep answers practical and concise.
"""

if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_category" not in st.session_state:
    st.session_state.active_category = "General"
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

with st.sidebar:
    st.title("💻 PC Sahayak")
    st.caption("Your Windows troubleshooting companion")
    st.divider()

    category = st.selectbox(
        "Troubleshooting category",
        [
            "General",
            "Performance Issues",
            "Network Problems",
            "Overheating",
            "Storage Problems",
            "Other Windows Issue",
        ],
        key="category_selector",
    )

    if category != st.session_state.active_category:
        st.session_state.active_category = category
        st.session_state.messages = []
        st.session_state.pending_prompt = None
        st.rerun()

    if st.button("＋ New chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_prompt = None
        st.rerun()

    st.divider()
    st.markdown("### Supported issues")
    st.markdown(
        "- 🐢 Slow computer\n"
        "- 🌐 Network problems\n"
        "- 🌡️ Overheating\n"
        "- 💾 Storage issues"
    )
    st.divider()
    st.caption("Powered by Groq")

st.title("PC Sahayak")
st.markdown(
    '<p class="subtitle">Describe your problem or attach a screenshot. '
    "We will troubleshoot it together.</p>",
    unsafe_allow_html=True,
)

if not st.session_state.messages:
    st.markdown("### How can I help with your PC today?")
    st.write(
        "Describe the issue, include an error message, "
        "or attach a screenshot in the message bar."
    )
    suggestions = [
        "My laptop is running slowly",
        "My Wi-Fi is connected but the internet does not work",
        "My laptop gets too hot",
        "My C drive is almost full",
    ]
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(
                suggestion,
                key=f"suggestion_{i}",
                use_container_width=True,
            ):
                st.session_state.pending_prompt = suggestion
                st.rerun()


def render_message(message):
    """Render user messages on the right and assistant messages on the left."""
    if message["role"] == "user":
        _, target = st.columns([1, 4], gap="medium")
    else:
        target, _ = st.columns([4, 1], gap="medium")

    with target:
        with st.chat_message(message["role"]):
            st.markdown(message.get("display_text", ""))
            if message.get("image_bytes"):
                st.image(
                    message["image_bytes"],
                    caption=message.get("image_name", "Attached screenshot"),
                    width=360,
                )


for saved_message in st.session_state.messages:
    render_message(saved_message)

prompt = st.chat_input(
    "Message PC Sahayak...",
    max_chars=5000,
    accept_file=True,
    file_type=["png", "jpg", "jpeg", "webp"],
    max_upload_size=5,
    key="chat_input",
)

typed_message = ""
uploaded_files = []
if prompt is not None:
    typed_message = (prompt.text or "").strip()
    uploaded_files = list(prompt.files or [])

user_input = typed_message or st.session_state.pending_prompt
st.session_state.pending_prompt = None

image_bytes = None
image_name = None
image_mime = None
if uploaded_files:
    uploaded_image = uploaded_files[0]
    image_bytes = uploaded_image.getvalue()
    image_name = uploaded_image.name
    image_mime = uploaded_image.type or "image/png"

if user_input or image_bytes:
    if not user_input and image_bytes:
        user_input = (
            "Please inspect this screenshot and explain what it shows, "
            "then suggest a safe troubleshooting step."
        )

    if image_bytes:
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{image_mime};base64,{encoded_image}"
        api_content = [
            {"type": "text", "text": user_input},
            {"type": "image_url", "image_url": {"url": data_url}},
        ]
    else:
        api_content = user_input

    user_message = {
        "role": "user",
        "display_text": user_input,
        "image_bytes": image_bytes,
        "image_name": image_name,
        "api_content": api_content,
    }
    st.session_state.messages.append(user_message)
    render_message(user_message)

    if not api_ready:
        st.error(
            "Groq API key not found. Check `.streamlit/secrets.toml` "
            "and make sure it contains `GROQ_API_KEY`."
        )
    else:
        api_messages = [
            {
                "role": "system",
                "content": (
                    SYSTEM_PROMPT
                    + "\nCurrent troubleshooting category: "
                    + st.session_state.active_category
                ),
            }
        ]
        for item in st.session_state.messages:
            api_messages.append(
                {
                    "role": item["role"],
                    "content": item.get("api_content", item["display_text"]),
                }
            )

        selected_model = VISION_MODEL if image_bytes else TEXT_MODEL
        left, _ = st.columns([4, 1], gap="medium")
        with left:
            with st.chat_message("assistant"):
                with st.spinner("PC Sahayak is analyzing your problem..."):
                    try:
                        response = client.chat.completions.create(
                            model=selected_model,
                            messages=api_messages,
                            temperature=0.3,
                            max_completion_tokens=1000,
                        )
                        answer = (
                            response.choices[0].message.content
                            or "Sorry, I couldn't generate a response."
                        )
                        st.markdown(answer)
                        st.session_state.messages.append(
                            {"role": "assistant", "display_text": answer}
                        )
                    except AuthenticationError:
                        st.error("Authentication failed. Check your Groq API key.")
                    except RateLimitError:
                        st.error(
                            "The API rate limit may have been reached. "
                            "Please wait a little and try again."
                        )
                    except APIError as error:
                        st.error(
                            "Groq could not process this request. The model "
                            "may be unavailable or the request may be unsupported."
                        )
                        st.caption(str(error))
                    except Exception as error:
                        st.error("Something went wrong. Please try again.")
                        st.caption(str(error))

st.divider()
st.caption("PC Sahayak • AI-powered Windows troubleshooting")
