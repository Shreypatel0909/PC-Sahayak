"""FastAPI server for the React UI.

A thin HTTP layer over the existing ``pc_helper`` package: every request goes
through the same AppContext, TroubleshootingEngine (Groq + RAG) and
ConversationStore that the Streamlit app uses, so both UIs share one core and
one local chat history. No troubleshooting logic lives here.

Run from the project root (the pc-helper/ folder):
    uvicorn api.main:app --port 8000

If the React app has been built (``npm run build`` in web/), it is served at /.
"""
from __future__ import annotations

import base64
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError

from pc_helper.core.context import AppContext
from pc_helper.core.logging_config import get_logger
from pc_helper.models.conversation_models import ConversationState, Message, SourceRef, SystemSpecs
from pc_helper.services.conversation_store import _safe_id
from pc_helper.services.llm_service import LLMError

from .categories import resolve_category

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_DIST = PROJECT_ROOT / "web" / "dist"

# Intake form options (the same lists the Streamlit form offers).
UNKNOWN = "Don't know"
OPTIONS = {
    "device_types": ["Laptop", "Desktop", UNKNOWN],
    "os": ["Windows 11", "Windows 10", "Windows 8.1", "Windows 7", "Other", UNKNOWN],
    "ram_sizes": ["4 GB", "8 GB", "16 GB", "32 GB", "64 GB or more", UNKNOWN],
    "ram_types": ["DDR3", "DDR4", "DDR5", "LPDDR4 / LPDDR4X", "LPDDR5 / LPDDR5X", UNKNOWN],
    "storage_sizes": ["128 GB", "256 GB", "512 GB", "1 TB", "2 TB or more", UNKNOWN],
    "storage_types": ["NVMe SSD", "SATA SSD", "HDD (hard disk)", "SSD + HDD", "eMMC", UNKNOWN],
}
IMAGE_TYPES = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_TEXT = 5000
SCREENSHOT_PLACEHOLDER = "(screenshot attached)"


# --------------------------------------------------------------------------- #
# Response models
# --------------------------------------------------------------------------- #
class SourceOut(BaseModel):
    file: str
    heading: Optional[str] = None


class MessageOut(BaseModel):
    role: str
    content: str
    kind: str
    timestamp: float
    image_url: Optional[str] = None
    sources: List[SourceOut]
    suggestions: List[str]
    tag: Optional[str] = None


class RouteOut(BaseModel):
    origin: str
    done: List[str]
    current: Optional[str] = None
    fixed: bool


class ConversationOut(BaseModel):
    id: str
    title: str
    status: str
    category: str
    locked: bool
    created_at: float
    updated_at: float
    specs: Optional[SystemSpecs] = None
    route: RouteOut
    messages: List[MessageOut]
    sources: List[SourceOut]


class SummaryOut(BaseModel):
    id: str
    title: str
    status: str
    category: str
    updated_at: float
    steps: int


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def make_title(text: str, has_image: bool) -> str:
    line = " ".join((text or "").split())
    if not line:
        return "Screenshot troubleshooting" if has_image else "New chat"
    return line if len(line) <= 60 else line[:57].rstrip() + "…"


def _image_url(conversation_id: str, image_path: Optional[str]) -> Optional[str]:
    if not image_path:
        return None
    return f"/api/uploads/{_safe_id(conversation_id)}/{Path(image_path).name}"


def _sources(items: List[SourceRef]) -> List[SourceOut]:
    return [SourceOut(file=s.file, heading=s.heading) for s in items]


def _route(state: ConversationState) -> RouteOut:
    fixed = state.status == "resolved"
    current = state.current_step
    if fixed or (current and current in state.completed_steps):
        current = None
    started = state.problem_summary or any(
        m.role == "assistant" and m.kind == "normal" and m.tag != "off_topic" for m in state.messages
    )
    # Nothing to map yet (e.g. only off-topic messages so far): the UI shows an empty route.
    origin = (state.problem_summary or state.title or "Your problem") if started else ""
    return RouteOut(origin=origin, done=list(state.completed_steps), current=current, fixed=fixed)


def _steps(state: ConversationState) -> int:
    route = _route(state)
    return len(route.done) + (1 if route.current else 0)


def _message(conversation_id: str, m: Message) -> MessageOut:
    return MessageOut(
        role=m.role, content=m.content, kind=m.kind, timestamp=m.timestamp,
        image_url=_image_url(conversation_id, m.image_path),
        sources=_sources(m.sources), suggestions=list(m.suggestions), tag=m.tag,
    )


def to_out(state: ConversationState) -> ConversationOut:
    return ConversationOut(
        id=state.conversation_id,
        title=state.title or make_title(next((m.content for m in state.messages if m.role == "user"), ""), False),
        status=state.status,
        category=resolve_category(state),
        locked=state.locked,
        created_at=state.created_at,
        updated_at=state.updated_at,
        specs=state.system_specs,
        route=_route(state),
        messages=[_message(state.conversation_id, m) for m in state.messages],
        sources=_sources(state.retrieved_sources),
    )


async def _read_image(upload: Optional[UploadFile]) -> Optional[tuple]:
    """Validate an uploaded screenshot; return (bytes, mime, filename) or None."""
    if upload is None or not upload.filename:
        return None
    mime = (upload.content_type or "").lower()
    if mime not in IMAGE_TYPES:
        raise HTTPException(415, "Screenshots must be PNG, JPG or WebP images.")
    data = await upload.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "That screenshot is over 10 MB. Try a smaller image.")
    if not data:
        raise HTTPException(400, "That screenshot file is empty.")
    return data, mime, upload.filename


def _data_url(data: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def _run_turn(ctx: AppContext, state: ConversationState, text: str, image: Optional[tuple]) -> None:
    """One troubleshooting turn through the shared engine, then persist.

    LLM failures are already recorded in the transcript by the engine as a
    user-safe error message, so the client just renders the conversation."""
    image_rel = data_url = None
    if image is not None:
        data, mime, name = image
        image_rel = ctx.conversation_store.save_image(state.conversation_id, data, name)
        data_url = _data_url(data, mime)
    _respond(ctx, state, text, data_url, image_rel)


def _respond(ctx: AppContext, state: ConversationState, text: str,
             data_url: Optional[str], image_rel: Optional[str]) -> None:
    if not state.title:
        state.title = make_title(text, data_url is not None)
    try:
        ctx.engine.respond(state, text, image_data_url=data_url, image_path=image_rel)
    except LLMError:
        pass
    except Exception:  # noqa: BLE001 - never leak a stack trace to the client
        logger.exception("Unexpected error while answering")
        if not state.messages or state.messages[-1].role != "user":
            state.add_message("user", text or SCREENSHOT_PLACEHOLDER, image_path=image_rel)
        state.add_message("assistant", "Something went wrong. Please try again.", kind="error")
    ctx.conversation_store.save(state)


LOCKED = "This chat is closed because the problem is solved. Unlock it to keep chatting."


def _clean_text(text: Optional[str]) -> str:
    text = (text or "").strip()
    if len(text) > MAX_TEXT:
        raise HTTPException(422, f"Messages can be at most {MAX_TEXT} characters.")
    return text


def _last_specs(ctx: AppContext) -> Optional[SystemSpecs]:
    store = ctx.conversation_store
    for summary in store.list_conversations(limit=10):
        saved = store.get(summary.conversation_id)
        if saved is not None and saved.system_specs is not None:
            return saved.system_specs
    return None


def _kb_info(ctx: AppContext) -> dict:
    manifest = ctx.index.manifest
    return {
        "documents": ctx.index.documents,
        "chunks": ctx.index.chunks,
        "embedder": getattr(manifest, "embedder", None) or ctx.embedder.name,
        "built_at": getattr(manifest, "built_at", None),
    }


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #
def create_app(context: Optional[AppContext] = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.ctx = context or AppContext()
        yield

    app = FastAPI(title="PC Helper API", lifespan=lifespan)

    def ctx_of(request: Request) -> AppContext:
        return request.app.state.ctx

    def get_state(ctx: AppContext, conversation_id: str) -> ConversationState:
        state = ctx.conversation_store.get(conversation_id)
        if state is None:
            raise HTTPException(404, "That chat no longer exists. It may have been deleted.")
        return state

    @app.get("/api/meta")
    def meta(request: Request) -> dict:
        ctx = ctx_of(request)
        cfg = ctx.settings.config
        last = _last_specs(ctx)
        return {
            "name": cfg.project.name,
            "starter_suggestions": list(cfg.ui.starter_suggestions),
            "options": OPTIONS,
            "llm": {
                "configured": bool(ctx.llm.is_configured),
                "text_model": cfg.llm.text_model,
                "vision_model": cfg.llm.vision_model,
                "rag": cfg.llm.use_rag,
            },
            "kb": _kb_info(ctx),
            "last_specs": last.model_dump() if last else None,
        }

    @app.get("/api/conversations", response_model=List[SummaryOut])
    def list_conversations(request: Request):
        ctx = ctx_of(request)
        out = []
        for s in ctx.conversation_store.list_conversations(limit=100):
            state = ctx.conversation_store.get(s.conversation_id)
            if state is None:
                continue
            out.append(SummaryOut(
                id=s.conversation_id, title=s.title, status=state.status,
                category=resolve_category(state), updated_at=s.updated_at, steps=_steps(state),
            ))
        return out

    @app.get("/api/conversations/{conversation_id}", response_model=ConversationOut)
    def get_conversation(conversation_id: str, request: Request):
        return to_out(get_state(ctx_of(request), conversation_id))

    @app.post("/api/conversations", response_model=ConversationOut)
    async def start_conversation(
        request: Request,
        specs: str = Form("{}"),
        issue: str = Form(""),
        image: Optional[UploadFile] = File(None),
    ):
        ctx = ctx_of(request)
        text = _clean_text(issue)
        shot = await _read_image(image)
        if not text and shot is None:
            raise HTTPException(422, "Describe the problem or add a screenshot so I know where to start.")
        try:
            parsed = SystemSpecs.model_validate_json(specs or "{}")
        except ValidationError:
            raise HTTPException(422, "The PC details could not be read. Check the form and try again.")
        state = ConversationState()
        state.apply_specs(parsed)
        state.title = make_title(text, shot is not None)
        _run_turn(ctx, state, text, shot)
        return to_out(state)

    @app.post("/api/conversations/{conversation_id}/messages", response_model=ConversationOut)
    async def send_message(
        conversation_id: str,
        request: Request,
        text: str = Form(""),
        image: Optional[UploadFile] = File(None),
    ):
        ctx = ctx_of(request)
        state = get_state(ctx, conversation_id)
        if state.locked:
            raise HTTPException(409, LOCKED)
        message = _clean_text(text)
        shot = await _read_image(image)
        if not message and shot is None:
            raise HTTPException(422, "Type a message or attach a screenshot.")
        _run_turn(ctx, state, message, shot)
        return to_out(state)

    @app.post("/api/conversations/{conversation_id}/resolve", response_model=ConversationOut)
    def resolve(conversation_id: str, request: Request):
        """The user confirmed the fix: closing summary of every step, then lock the chat."""
        ctx = ctx_of(request)
        state = get_state(ctx, conversation_id)
        if state.locked:
            raise HTTPException(409, LOCKED)
        try:
            ctx.engine.resolve(state)
        except LLMError:
            pass  # recorded in the transcript as an error the user can retry
        except Exception:  # noqa: BLE001
            logger.exception("Unexpected error while closing a chat")
            state.add_message("assistant", "Something went wrong. Please try again.", kind="error")
        ctx.conversation_store.save(state)
        return to_out(state)

    @app.post("/api/conversations/{conversation_id}/unlock", response_model=ConversationOut)
    def unlock(conversation_id: str, request: Request):
        ctx = ctx_of(request)
        state = get_state(ctx, conversation_id)
        state.locked = False
        ctx.conversation_store.save(state)
        return to_out(state)

    @app.post("/api/conversations/{conversation_id}/retry", response_model=ConversationOut)
    def retry(conversation_id: str, request: Request):
        """Re-run the last user turn after an error reply."""
        ctx = ctx_of(request)
        state = get_state(ctx, conversation_id)
        if not state.messages or state.messages[-1].kind != "error":
            raise HTTPException(409, "There's nothing to retry in this chat.")
        state.messages.pop()
        if not state.messages or state.messages[-1].role != "user":
            ctx.conversation_store.save(state)
            raise HTTPException(409, "There's nothing to retry in this chat.")
        last = state.messages.pop()
        text = "" if last.content == SCREENSHOT_PLACEHOLDER else last.content
        data_url = image_rel = None
        path = ctx.conversation_store.resolve_image(last.image_path)
        if path is not None:  # reuse the screenshot already on disk
            suffix = path.suffix.lower()
            mime = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/webp" if suffix == ".webp" else "image/png"
            data_url, image_rel = _data_url(path.read_bytes(), mime), last.image_path
        _respond(ctx, state, text, data_url, image_rel)
        return to_out(state)

    @app.delete("/api/conversations/{conversation_id}")
    def delete_conversation(conversation_id: str, request: Request) -> dict:
        if not ctx_of(request).conversation_store.delete(conversation_id):
            raise HTTPException(404, "That chat no longer exists.")
        return {"deleted": 1}

    @app.delete("/api/conversations")
    def delete_all(request: Request) -> dict:
        store = ctx_of(request).conversation_store
        ids = [s.conversation_id for s in store.list_conversations(limit=100_000)]
        for cid in ids:
            store.delete(cid)
        return {"deleted": len(ids)}

    @app.post("/api/reindex")
    def reindex(request: Request) -> dict:
        ctx = ctx_of(request)
        try:
            stats = ctx.reindex()
        except RuntimeError as exc:
            raise HTTPException(409, str(exc))
        return {"documents": stats.documents, "chunks": stats.chunks, "skipped": stats.skipped,
                "errors": list(stats.errors), "kb": _kb_info(ctx)}

    @app.get("/api/uploads/{conversation_id}/{filename}")
    def upload_file(conversation_id: str, filename: str, request: Request):
        uploads = ctx_of(request).conversation_store.uploads_dir.resolve()
        target = (uploads / _safe_id(conversation_id) / Path(filename).name).resolve()
        if uploads not in target.parents or not target.is_file():
            raise HTTPException(404, "Screenshot not found.")
        return FileResponse(target)

    if WEB_DIST.is_dir():
        app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")

    return app


app = create_app()
