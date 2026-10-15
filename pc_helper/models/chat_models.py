"""Small shared result schema used by the troubleshooting engine."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class StepInfo(BaseModel):
    current_issue: Optional[str] = None
    current_step: Optional[str] = None
    completed_steps: List[str] = Field(default_factory=list)
