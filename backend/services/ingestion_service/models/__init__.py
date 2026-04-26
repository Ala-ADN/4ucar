"""SQLAlchemy ORM models for the ingestion pipeline.

Imported here so Alembic env.py can register every table on Base.metadata
by importing this single module.
"""

from backend.services.ingestion_service.models.audit import (  # noqa: F401
    AuditAction,
    AuditEntry,
)
from backend.services.ingestion_service.models.document_template import (  # noqa: F401
    DocumentTemplate,
    DocumentTemplateField,
)
from backend.services.ingestion_service.models.import_record import (  # noqa: F401
    DataRecord,
    DataRequest,
    DataRequestResponse,
    ImportRecord,
    LockedPeriod,
    QuarantineRow,
)
