"""Application service layer (orchestration, no I/O of its own)."""

from .recompute import recompute_all_domains

__all__ = ["recompute_all_domains"]
