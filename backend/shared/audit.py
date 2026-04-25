"""Append-only audit log writer (see ucar_global.audit_log)."""


async def record_audit(*, action: str, entity_type: str, entity_id, old_value=None, new_value=None) -> None:
    raise NotImplementedError
