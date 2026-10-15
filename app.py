"""PC-Sahayak — Streamlit app.

Built on top of the original "PC Sahayak" Streamlit + Groq prototype, adding a
real Retrieval-Augmented Generation (RAG) pipeline over a Markdown knowledge
base, source citations, structured conversation state, an intake form for the
user's system details, animated replies, and a locally stored, resumable chat
history.

Run from the project root (the pc-helper/ folder):
    streamlit run app.py
"""
from __future__ import annotations

import base64
import html
import os
import re
import time
from datetime import datetime
from typing import Optional

import streamlit as st

from pc_helper.core.config import get_settings
from pc_helper.core.context import AppContext
from pc_helper.core.logging_config import get_logger
from pc_helper.models.conversation_models import UNKNOWN, ConversationState, Message, SystemSpecs
from pc_helper.services.llm_service import LLMError
from pc_helper.services.troubleshooting_service import WELCOME_MESSAGE

logger = get_logger(__name__)
settings = get_settings()

st.set_page_config(
    page_title=settings.config.project.name,
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------- #
# Intake form options
# --------------------------------------------------------------------------- #
DEVICE_TYPES = ["Laptop", "Desktop", UNKNOWN]
OS_OPTIONS = ["Windows 11", "Windows 10", "Windows 8.1", "Windows 7", "Other", UNKNOWN]
RAM_SIZES = ["4 GB", "8 GB", "16 GB", "32 GB", "64 GB or more", UNKNOWN]
RAM_TYPES = ["DDR3", "DDR4", "DDR5", "LPDDR4 / LPDDR4X", "LPDDR5 / LPDDR5X", UNKNOWN]
STORAGE_SIZES = ["128 GB", "256 GB", "512 GB", "1 TB", "2 TB or more", UNKNOWN]
STORAGE_TYPES = ["NVMe SSD", "SATA SSD", "HDD (hard disk)", "SSD + HDD", "eMMC", UNKNOWN]
IMAGE_TYPES = ["png", "jpg", "jpeg", "webp"]

HOW_TO_FIND = """
- **OS and version:** *Settings › System › About* → *Windows specifications* (Edition, Version such as `23H2`, OS build).
- **RAM size:** *Settings › System › About* → *Installed RAM*.
- **RAM type:** *Task Manager* (`Ctrl+Shift+Esc`) › *Performance* › *Memory* shows the speed
  (about 2133–3200 MT/s is usually DDR4, 4800+ MT/s is DDR5). Or run this in PowerShell:
  `Get-CimInstance Win32_PhysicalMemory | Select-Object SMBIOSMemoryType, Speed`
  (24 = DDR3, 26 = DDR4, 34 = DDR5).
- **Storage size and type:** *Task Manager* › *Performance* › *Disk 0* shows the capacity and
  whether it is an SSD (NVMe) or HDD.

Not sure about something? Pick **Don't know** — that's fine.
"""

# Upper bound (seconds) for the word-by-word reveal of a reply. Tests set 0.
REVEAL_SECONDS = float(os.getenv("PC_HELPER_REVEAL_SECONDS", "2.5"))

# Invisible markers: the CSS animates only the chat bubble that contains one, so
# just the newest exchange animates, never the whole history on every rerun.
ANIM_USER = '<span class="anim-user"></span>'
ANIM_BOT = '<span class="anim-bot"></span>'
TYPING_HTML = (
    '<div class="typing" role="status" aria-live="polite">'
    "<span></span><span></span><span></span><em>PC-Sahayak is thinking…</em></div>"
)

st.markdown(
    """
    <style>
    .block-container { max-width: 1100px; padding-top: 1.5rem; padding-bottom: 2rem; }
    .subtitle { color: #9ca3af; margin-top: -10px; }
    [data-testid="stChatMessage"] { border-radius: 16px; padding: 0.75rem 1rem; margin-bottom: 0.6rem; }
    [data-testid="stChatMessage"] [data-testid="stChatMessageContent"] { min-width: 0; line-height: 1.65; }
    [data-testid="stChatMessage"] ul, [data-testid="stChatMessage"] ol { padding-left: 1.4rem; margin: 0.4rem 0 0.8rem; }
    .sources { color: #9ca3af; font-size: 0.85rem; margin-top: 0.35rem; }
    .profile-card {
        border: 1px solid rgba(128, 128, 128, 0.28); border-radius: 12px;
        padding: 0.55rem 0.9rem; margin: 0.2rem 0 1rem; font-size: 0.92rem;
    }

    /* --- Animations: new user message slides in, reply bubble fades up --- */
    [data-testid="stElementContainer"]:has(.anim-user, .anim-bot):not(:has([data-testid="stChatMessage"])) {
        display: none;  /* the marker itself takes no space */
    }
    [data-testid="stChatMessage"]:has(.anim-user) { animation: pcSlideIn 0.38s cubic-bezier(0.2, 0.8, 0.2, 1) both; }
    [data-testid="stChatMessage"]:has(.anim-bot) { animation: pcFadeUp 0.45s ease-out 0.12s both; }

    .typing { display: inline-flex; align-items: center; gap: 6px; color: #9ca3af; padding: 0.15rem 0; }
    .typing span {
        width: 8px; height: 8px; border-radius: 50%; background: currentColor;
        animation: pcBounce 1.2s infinite ease-in-out;
    }
    .typing span:nth-child(2) { animation-delay: 0.15s; }
    .typing span:nth-child(3) { animation-delay: 0.3s; }
    .typing em { margin-left: 6px; font-style: normal; font-size: 0.9rem; animation: pcPulse 1.6s infinite ease-in-out; }

    @keyframes pcSlideIn { from { opacity: 0; transform: translateX(28px) scale(0.98); } to { opacity: 1; transform: none; } }
    @keyframes pcFadeUp  { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
    @keyframes pcBounce  { 0%, 80%, 100% { transform: translateY(0); opacity: 0.35; } 40% { transform: translateY(-5px); opacity: 1; } }
    @keyframes pcPulse   { 0%, 100% { opacity: 0.55; } 50% { opacity: 1; } }

    @media (prefers-reduced-motion: reduce) {
        [data-testid="stChatMessage"], .typing span, .typing em { animation: none !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="Loading the knowledge base…")
def get_context() -> AppContext:
    """Build the shared services once per server process."""
    return AppContext(settings)


ctx = get_context()
store = ctx.conversation_store


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def make_title(text: str, has_image: bool) -> str:
    line = " ".join((text or "").split())
    if not line:
        return "Screenshot troubleshooting" if has_image else "New chat"
    return line if len(line) <= 60 else line[:57].rstrip() + "…"


def short(text: str, limit: int = 34) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def relative_time(ts: float) -> str:
    delta = time.time() - ts
    if delta < 60:
        return "just now"
    if delta < 3600:
        return f"{int(delta // 60)} min ago"
    if delta < 86400:
        return f"{int(delta // 3600)} h ago"
    if delta < 172800:
        return "yesterday"
    return datetime.fromtimestamp(ts).strftime("%d %b %Y")


def image_payload(uploaded) -> dict:
    if uploaded is None:
        return {}
    return {
        "image_bytes": uploaded.getvalue(),
        "image_name": uploaded.name,
        "image_mime": uploaded.type or "image/png",
    }


def reveal(text: str):
    """Yield a reply word by word so it eases in instead of appearing all at once."""
    tokens = re.findall(r"\s*\S+\s*", text)
    if not tokens:
        return
    delay = min(0.04, REVEAL_SECONDS / len(tokens)) if REVEAL_SECONDS > 0 else 0.0
    for tok in tokens:
        yield tok
        if delay:
            time.sleep(delay)


def sources_html(sources) -> str:
    items = ", ".join(
        html.escape(s.file) + (f" › {html.escape(s.heading)}" if s.heading else "") for s in sources
    )
    return f'<div class="sources">📄 Sources: {items}</div>'


# --------------------------------------------------------------------------- #
# Session state and navigation (callbacks run before the next rerun)
# --------------------------------------------------------------------------- #
def set_chat_param(conversation_id: Optional[str]) -> None:
    """Keep ?chat=<id> in the URL so a refresh resumes the same conversation."""
    if conversation_id:
        st.query_params["chat"] = conversation_id
    else:
        st.query_params.pop("chat", None)


def new_chat() -> None:
    st.session_state.state = ConversationState()
    st.session_state.pending_turn = None
    st.session_state.pop("intake_issue", None)
    set_chat_param(None)


def open_chat(conversation_id: str) -> None:
    state = store.get(conversation_id)
    if state is not None:
        st.session_state.state = state
        st.session_state.pending_turn = None
        set_chat_param(conversation_id)


def delete_chat(conversation_id: str) -> None:
    store.delete(conversation_id)
    if st.session_state.state.conversation_id == conversation_id:
        new_chat()


def queue_turn(text: str) -> None:
    st.session_state.pending_turn = {"text": text}


def fill_issue(text: str) -> None:
    st.session_state.intake_issue = text


if "state" not in st.session_state:
    resumed = None
    requested = st.query_params.get("chat")
    if requested:
        resumed = store.get(requested)
    st.session_state.state = resumed or ConversationState()
if "pending_turn" not in st.session_state:
    st.session_state.pending_turn = None


def default_specs() -> Optional[SystemSpecs]:
    """Pre-fill the form from this session, else from the most recent saved chat."""
    if st.session_state.get("last_specs"):
        return st.session_state.last_specs
    for summary in store.list_conversations(limit=5):
        saved = store.get(summary.conversation_id)
        if saved is not None and saved.system_specs is not None:
            return saved.system_specs
    return None


# --------------------------------------------------------------------------- #
# Sidebar: new chat, local history, system profile, progress, knowledge base
# --------------------------------------------------------------------------- #
def render_sidebar() -> None:
    state: ConversationState = st.session_state.state
    with st.sidebar:
        st.title("💻 PC-Sahayak")
        st.caption("Your Windows troubleshooting companion")
        st.button("＋ New chat", key="new_chat", on_click=new_chat, type="primary", width="stretch")

        st.markdown("### 🕘 Chat history")
        history = store.list_conversations(limit=30)
        if not history:
            st.caption("No saved chats yet — your conversations are stored on this computer.")
        for item in history:
            active = item.conversation_id == state.conversation_id
            c1, c2 = st.columns([5, 1], vertical_alignment="center")
            c1.button(
                ("▶ " if active else "") + short(item.title),
                key=f"open_{item.conversation_id}",
                help=f"{item.title}\n\n{relative_time(item.updated_at)} · {item.message_count} messages",
                on_click=open_chat,
                args=(item.conversation_id,),
                width="stretch",
            )
            with c2.popover("🗑", help="Delete this chat"):
                st.caption("Delete this chat permanently?")
                st.button(
                    "Delete",
                    key=f"del_{item.conversation_id}",
                    type="primary",
                    on_click=delete_chat,
                    args=(item.conversation_id,),
                )

        if state.system_specs:
            st.divider()
            st.markdown("### 🖥️ System profile")
            st.caption(state.system_specs.summary())

        if state.problem_summary or state.current_step or state.completed_steps:
            st.divider()
            st.markdown("### 🧭 Progress")
            if state.problem_summary:
                st.caption(f"**Issue:** {state.problem_summary}")
            if state.current_step:
                st.caption(f"**Current step:** {state.current_step}")
            if state.completed_steps:
                st.caption("**Done:** " + "; ".join(state.completed_steps[-4:]))

        st.divider()
        if not ctx.llm.is_configured:
            st.warning("No Groq API key found. Add `GROQ_API_KEY` to `.env` or `.streamlit/secrets.toml`.")
        with st.expander("📚 Knowledge base"):
            st.caption(
                f"{ctx.index.documents} documents · {ctx.index.chunks} chunks\n\n"
                f"embedder: `{ctx.embedder.name}`"
            )
            if st.button("↻ Rebuild index", key="rebuild_index", width="stretch"):
                with st.spinner("Re-indexing…"):
                    stats = ctx.reindex()
                st.success(f"Indexed {stats.documents} docs / {stats.chunks} chunks.")
        st.caption("Powered by Groq · chats are saved locally on this computer")


# --------------------------------------------------------------------------- #
# Intake form (start of every new chat)
# --------------------------------------------------------------------------- #
def _index(options: list, value: Optional[str], fallback: str = UNKNOWN) -> int:
    return options.index(value) if value in options else options.index(fallback)


def render_intake() -> None:
    with st.chat_message("assistant"):
        st.markdown(WELCOME_MESSAGE)

    st.caption("Quick examples — click one to fill in the issue box:")
    cols = st.columns(2)
    for i, example in enumerate(settings.config.ui.starter_suggestions):
        cols[i % 2].button(example, key=f"example_{i}", on_click=fill_issue, args=(example,), width="stretch")

    prev = default_specs()
    with st.form("intake_form"):
        st.markdown("#### 🖥️ Your system")
        if prev is not None:
            st.caption("Pre-filled from your last chat — change anything that's different.")
        c1, c2, c3 = st.columns(3)
        device = c1.selectbox("Device type", DEVICE_TYPES,
                              index=_index(DEVICE_TYPES, prev and prev.device_type), key="intake_device")
        os_name = c2.selectbox("Operating system", OS_OPTIONS,
                               index=_index(OS_OPTIONS, prev.os if prev else "Windows 11"), key="intake_os")
        os_version = c3.text_input("OS version / build", value=(prev.os_version or "") if prev else "",
                                   placeholder="e.g. 23H2 (build 22631)", key="intake_os_version")
        c4, c5 = st.columns(2)
        ram_size = c4.selectbox("RAM size", RAM_SIZES,
                                index=_index(RAM_SIZES, prev and prev.ram_size), key="intake_ram_size")
        ram_type = c5.selectbox("RAM type", RAM_TYPES,
                                index=_index(RAM_TYPES, prev and prev.ram_type), key="intake_ram_type")
        c6, c7 = st.columns(2)
        storage_size = c6.selectbox("Storage size", STORAGE_SIZES,
                                    index=_index(STORAGE_SIZES, prev and prev.storage_size), key="intake_storage_size")
        storage_type = c7.selectbox("Storage type", STORAGE_TYPES,
                                    index=_index(STORAGE_TYPES, prev and prev.storage_type), key="intake_storage_type")
        with st.expander("Not sure where to find these details?"):
            st.markdown(HOW_TO_FIND)

        st.markdown("#### 📝 Describe the issue")
        issue = st.text_area(
            "What's going wrong?",
            key="intake_issue",
            height=140,
            max_chars=4000,
            placeholder="e.g. My laptop gets very hot and slows down after 10 minutes of gaming. "
                        "It started last week after a Windows update.",
        )
        st.markdown("#### 📎 Screenshot (optional)")
        shot = st.file_uploader("Attach a screenshot of the error or problem", type=IMAGE_TYPES, key="intake_image")
        submitted = st.form_submit_button("Start troubleshooting  →", key="intake_submit",
                                          type="primary", width="stretch")

    if not submitted:
        return
    text = (issue or "").strip()
    if not text and shot is None:
        st.error("Please describe the issue or attach a screenshot so I know where to start.")
        return

    specs = SystemSpecs(
        device_type=device, os=os_name, os_version=(os_version or "").strip() or None,
        ram_size=ram_size, ram_type=ram_type, storage_size=storage_size, storage_type=storage_type,
    )
    state: ConversationState = st.session_state.state
    state.apply_specs(specs)
    state.title = make_title(text, shot is not None)
    st.session_state.last_specs = specs
    st.session_state.pending_turn = {"text": text, **image_payload(shot)}
    st.rerun()


# --------------------------------------------------------------------------- #
# Chat view
# --------------------------------------------------------------------------- #
def render_message(m: Message, show_chips: bool) -> None:
    if m.role == "user":
        _, col = st.columns([1, 4], gap="medium")
    else:
        col, _ = st.columns([4, 1], gap="medium")
    with col, st.chat_message(m.role):
        if m.kind == "error":
            st.error(m.content, icon="⚠️")
        else:
            st.markdown(m.content)
        image = store.resolve_image(m.image_path)
        if image is not None:
            st.image(str(image), width=360)
        if m.sources:
            st.markdown(sources_html(m.sources), unsafe_allow_html=True)
        if show_chips and m.suggestions:
            chip_cols = st.columns(len(m.suggestions))
            for i, suggestion in enumerate(m.suggestions):
                chip_cols[i].button(suggestion, key=f"chip_{i}", on_click=queue_turn,
                                    args=(suggestion,), width="stretch")


def process_turn(turn: dict) -> None:
    """Show the new exchange live (animated), then rerun to render it from state."""
    state: ConversationState = st.session_state.state
    text = (turn.get("text") or "").strip()
    image_bytes = turn.get("image_bytes")
    image_rel = data_url = None
    if image_bytes:
        image_rel = store.save_image(state.conversation_id, image_bytes, turn.get("image_name") or "screenshot.png")
        encoded = base64.b64encode(image_bytes).decode("ascii")
        data_url = f"data:{turn.get('image_mime') or 'image/png'};base64,{encoded}"
    if not state.title:
        state.title = make_title(text, image_bytes is not None)

    # The user's message slides in…
    _, col = st.columns([1, 4], gap="medium")
    with col, st.chat_message("user"):
        st.markdown(ANIM_USER, unsafe_allow_html=True)
        st.markdown(text or "_(screenshot attached)_")
        if image_bytes:
            st.image(image_bytes, width=360)

    # …PC-Sahayak "thinks", then its reply eases in word by word.
    col, _ = st.columns([4, 1], gap="medium")
    with col, st.chat_message("assistant"):
        st.markdown(ANIM_BOT, unsafe_allow_html=True)
        slot = st.empty()
        slot.markdown(TYPING_HTML, unsafe_allow_html=True)
        result = None
        try:
            result = ctx.engine.respond(state, text, image_data_url=data_url, image_path=image_rel)
        except LLMError as exc:  # the engine already recorded it in the transcript
            slot.error(str(exc), icon="⚠️")
        except Exception:  # noqa: BLE001 - never show a stack trace to the user
            logger.exception("Unexpected error while answering")
            if not state.messages or state.messages[-1].role != "user":
                state.add_message("user", text or "(screenshot attached)", image_path=image_rel)
            state.add_message("assistant", "Something went wrong. Please try again.", kind="error")
            slot.error("Something went wrong. Please try again.", icon="⚠️")

        # Save before the reveal, so nothing is lost if the animation is interrupted.
        store.save(state)
        set_chat_param(state.conversation_id)

        if result is not None:
            with slot.container():
                st.write_stream(reveal(result.reply))
                if result.sources:
                    st.markdown(sources_html(result.sources), unsafe_allow_html=True)
    st.rerun()


def render_chat() -> None:
    state: ConversationState = st.session_state.state

    chat = st.chat_input(
        "Message PC-Sahayak…",
        key="chat_input",
        max_chars=5000,
        accept_file=True,
        file_type=IMAGE_TYPES,
        submit_mode="disable",
    )
    turn = None
    if chat is not None:
        text = chat if isinstance(chat, str) else (getattr(chat, "text", "") or "")
        files = [] if isinstance(chat, str) else list(getattr(chat, "files", None) or [])
        if text.strip() or files:
            turn = {"text": text.strip(), **image_payload(files[0] if files else None)}
    if turn is None and st.session_state.pending_turn:
        turn = st.session_state.pending_turn
    st.session_state.pending_turn = None

    if state.system_specs:
        st.markdown(
            f'<div class="profile-card">🖥️ <b>Your system:</b> {html.escape(state.system_specs.summary())}</div>',
            unsafe_allow_html=True,
        )

    last = len(state.messages) - 1
    for i, m in enumerate(state.messages):
        show_chips = turn is None and i == last and m.role == "assistant" and m.kind == "normal"
        render_message(m, show_chips)

    if turn is not None:
        process_turn(turn)


# --------------------------------------------------------------------------- #
# Page
# --------------------------------------------------------------------------- #
render_sidebar()
st.title(settings.config.project.name)
st.markdown(
    '<p class="subtitle">Tell me about your PC and the problem — '
    "we'll fix it together, one safe step at a time.</p>",
    unsafe_allow_html=True,
)

current: ConversationState = st.session_state.state
if not current.intake_complete and not current.messages:
    render_intake()
else:
    render_chat()
