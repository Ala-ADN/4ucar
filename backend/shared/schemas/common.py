"""Common response envelopes — bilingual error format + pagination."""

from pydantic import BaseModel


class BilingualMessage(BaseModel):
    fr: str
    ar: str | None = None


class ErrorEnvelope(BaseModel):
    code: str
    message_fr: str
    message_ar: str | None = None
    detail: str | None = None


class Page(BaseModel):
    page: int
    page_size: int
    total: int
