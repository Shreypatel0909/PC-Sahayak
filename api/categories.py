"""Map a conversation to one of the problem types the UI colours its route by.

The LLM sets ``issue_category`` on every structured reply, so that is the main
signal. Models sometimes answer with a near-synonym ("wifi", "Windows") or not
at all (e.g. a screenshot-only first turn, where the vision path returns plain
Markdown), so we normalise synonyms and fall back to keywords in the problem
summary / title.
"""
from __future__ import annotations

import re
from typing import Optional

from pc_helper.models.conversation_models import ConversationState

CATEGORIES = ("network", "performance", "hardware", "software", "boot", "security", "other")

_ALIASES = {
    "wifi": "network", "wi-fi": "network", "internet": "network", "dns": "network", "connect": "network",
    "boot": "boot", "startup": "boot", "start-up": "boot", "windows": "boot", "bsod": "boot", "blue screen": "boot",
    "slow": "performance", "speed": "performance", "storage": "performance", "disk": "performance",
    "overheat": "hardware", "device": "hardware", "peripheral": "hardware", "usb": "hardware",
    "app": "software", "driver": "software", "install": "software", "update": "software",
    "malware": "security", "virus": "security", "privacy": "security",
}

_RULES = [
    ("boot", re.compile(r"\b(boot|booting|start ?up|won'?t (start|turn on)|bios|uefi|blue screen|bsod|automatic repair|black screen)\b", re.I)),
    ("security", re.compile(r"\b(virus|malware|hack(ed)?|pop-?ups?|ransomware|antivirus|phishing|suspicious)\b", re.I)),
    ("network", re.compile(r"(wi-?fi|internet|network|\bdns\b|router|ethernet|offline|connect|bluetooth)", re.I)),
    ("hardware", re.compile(r"(\bhot\b|heat|overheat|\bfans?\b|\busb\b|mouse|keyboard|battery|charg|noise|beep|flicker|monitor|printer|\bram\b)", re.I)),
    ("performance", re.compile(r"(slow|\blag|freez|hang|100 ?%|disk usage|almost full|disk space|storage|c drive|high memory|high cpu)", re.I)),
    ("software", re.compile(r"(crash|\bapps?\b|install|driver|update|program|error code|won'?t open|not opening|game)", re.I)),
]


def _from_label(raw: Optional[str]) -> Optional[str]:
    label = (raw or "").strip().lower()
    if not label:
        return None
    if label in CATEGORIES:
        return label
    for key, cat in _ALIASES.items():
        if key in label:
            return cat
    return None


def classify_text(text: str) -> Optional[str]:
    for cat, rule in _RULES:
        if rule.search(text or ""):
            return cat
    return None


def resolve_category(state: ConversationState) -> str:
    from_llm = _from_label(state.issue_category)
    if from_llm:
        return from_llm
    first_user = next((m.content for m in state.messages if m.role == "user"), "")
    text = " ".join(filter(None, [state.problem_summary, state.title, first_user]))
    return classify_text(text) or "other"
