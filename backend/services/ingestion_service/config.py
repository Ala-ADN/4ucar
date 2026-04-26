"""Ingestion service settings — extends shared base settings."""

from functools import lru_cache

from backend.shared.config import Settings


class IngestionSettings(Settings):
    # File handling
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 50
    max_pdf_pages: int = 30

    # OCR confidence thresholds
    ocr_confidence_high: float = 0.90
    ocr_confidence_low: float = 0.60

    # Claude API
    claude_timeout_seconds: int = 15
    claude_max_retries: int = 2

    # Data retention
    rollback_window_days: int = 7
    file_retention_days: int = 365

    # Redis pub/sub channel
    events_channel: str = "data.events"

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> IngestionSettings:
    return IngestionSettings()
