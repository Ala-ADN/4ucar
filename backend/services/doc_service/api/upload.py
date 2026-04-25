"""Multipart upload endpoint + format detection."""

from fastapi import APIRouter

router = APIRouter(prefix="/documents", tags=["documents"])
