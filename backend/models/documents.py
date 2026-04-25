"""Documents schema: files, extraction results, templates, ingestion log."""


class DocumentFile:
    """`documents.files` — uploaded raw file metadata."""


class ExtractionResult:
    """`documents.extraction_results` — extracted JSON + confidence."""


class DocumentTemplate:
    """`documents.templates` — reusable extraction template."""


class IngestionLog:
    """Per-pipeline-stage audit row."""
