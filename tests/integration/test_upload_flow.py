"""Integration tests for the full upload → status → mapping → commit flow.

Claude API and PaddleOCR are mocked — no real external calls.
"""

from __future__ import annotations

import io
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient

from tests.conftest import make_token
from backend.shared.auth.rbac import Role


@pytest.mark.asyncio
async def test_upload_returns_202(client: AsyncClient, tmp_path, institution_id, admin_token):
    csv_content = "Taux de reussite;Effectif total\n75;1200\n".encode("utf-8")

    # Tasks are imported inside the function body, so patch the module where they live
    with patch("backend.services.ingestion_service.tasks.run_extraction") as mock_task:
        mock_task.apply_async.return_value = MagicMock(id="fake-task-id")
        with patch(
            "backend.services.ingestion_service.routers.upload.get_settings"
        ) as mock_settings:
            s = MagicMock()
            s.max_file_size_bytes = 50 * 1024 * 1024
            s.upload_dir = str(tmp_path)
            mock_settings.return_value = s

            # Also patch the inline import of run_extraction inside the router
            with patch(
                "backend.services.ingestion_service.routers.upload.run_extraction",
                mock_task,
                create=True,
            ):
                response = await client.post(
                    "/upload",
                    files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
                    data={
                        "domain": "academic",
                        "period": "2025-S1",
                        "institution_id": str(institution_id),
                    },
                    headers={"Authorization": f"Bearer {admin_token}"},
                )

    assert response.status_code == 202, response.text
    body = response.json()
    assert "import_id" in body
    assert body["status"] == "pending"


@pytest.mark.asyncio
async def test_upload_rejects_large_file(client: AsyncClient, institution_id, admin_token):
    with patch(
        "backend.services.ingestion_service.routers.upload.get_settings"
    ) as mock_settings:
        s = MagicMock()
        s.max_file_size_bytes = 10  # 10 bytes max
        s.upload_dir = "/tmp"
        mock_settings.return_value = s

        mock_task = MagicMock()
        mock_task.apply_async.return_value = MagicMock(id="x")

        with patch(
            "backend.services.ingestion_service.routers.upload.run_extraction",
            mock_task,
            create=True,
        ):
            response = await client.post(
                "/upload",
                files={"file": ("big.csv", io.BytesIO(b"a" * 100), "text/csv")},
                data={
                    "domain": "academic",
                    "period": "2025-S1",
                    "institution_id": str(institution_id),
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"


@pytest.mark.asyncio
async def test_upload_requires_auth(client: AsyncClient, institution_id):
    response = await client.post(
        "/upload",
        files={"file": ("test.csv", io.BytesIO(b"a,b\n1,2"), "text/csv")},
        data={"domain": "academic", "period": "2025-S1", "institution_id": str(institution_id)},
    )
    assert response.status_code in (401, 422)


@pytest.mark.asyncio
async def test_institution_admin_cannot_access_other_institution(
    client: AsyncClient, institution_id
):
    other_institution = uuid.uuid4()
    token = make_token(institution_id=institution_id, role=Role.INSTITUTION_ADMIN)

    with patch(
        "backend.services.ingestion_service.routers.upload.get_settings"
    ) as ms:
        ms.return_value = MagicMock(max_file_size_bytes=50_000_000, upload_dir="/tmp")
        mock_task = MagicMock()
        mock_task.apply_async.return_value = MagicMock(id="x")

        with patch(
            "backend.services.ingestion_service.routers.upload.run_extraction",
            mock_task,
            create=True,
        ):
            response = await client.post(
                "/upload",
                files={"file": ("f.csv", io.BytesIO(b"a;b\n1;2"), "text/csv")},
                data={
                    "domain": "academic",
                    "period": "2025-S1",
                    "institution_id": str(other_institution),  # different institution
                },
                headers={"Authorization": f"Bearer {token}"},
            )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "TENANT_SCOPE_VIOLATION"


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    # Health check connects to real infra which isn't available in tests;
    # mock at the module level where the imports happen (inside function body)
    with patch(
        "backend.services.ingestion_service.config.get_settings"
    ) as ms:
        ms.return_value = MagicMock(
            postgres_dsn="postgresql+asyncpg://x:x@localhost/x",
            redis_url="redis://localhost:6379/0",
        )
        with patch("sqlalchemy.ext.asyncio.create_async_engine") as mock_engine:
            mock_conn = AsyncMock()
            mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_conn.__aexit__ = AsyncMock(return_value=False)
            mock_conn.execute = AsyncMock()
            mock_engine.return_value.connect.return_value = mock_conn
            mock_engine.return_value.dispose = AsyncMock()

            with patch("redis.asyncio.from_url") as mock_redis:
                mock_r = AsyncMock()
                mock_r.ping = AsyncMock()
                mock_r.aclose = AsyncMock()
                mock_redis.return_value = mock_r

                response = await client.get("/health")

    # Health returns 200 regardless of check results (degraded is still 200)
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "checks" in body


@pytest.mark.asyncio
async def test_mapping_claude_mocked(client: AsyncClient, db_session):
    """Verify the mapping endpoint accepts a confirmed mapping and triggers validation."""
    from backend.services.ingestion_service.models.import_record import ImportRecord

    import_id = uuid.uuid4()
    inst_id = uuid.uuid4()
    user_id = uuid.uuid4()
    token = make_token(user_id=user_id, institution_id=inst_id, role=Role.INSTITUTION_ADMIN)

    record = ImportRecord(
        id=import_id,
        institution_id=inst_id,
        uploaded_by=user_id,
        original_filename="test.csv",
        storage_path="/tmp/test.csv",
        file_size_bytes=100,
        domain="academic",
        period="2025-S1",
        status="mapping_proposed",
        extracted_headers=["Taux de reussite", "Effectif total"],
        extracted_preview=[{"Taux de reussite": "75", "Effectif total": "1200"}],
        total_rows=1,
        mapping_proposal=[
            {"column": "Taux de reussite", "field_id": "success_rate", "confidence": 0.95},
        ],
    )
    db_session.add(record)
    await db_session.commit()

    mock_task = MagicMock()
    mock_task.apply_async.return_value = MagicMock(id="task-123")

    with patch(
        "backend.services.ingestion_service.routers.imports.run_normalization_and_validation",
        mock_task,
        create=True,
    ):
        response = await client.post(
            f"/imports/{import_id}/mapping",
            json={"mapping": {"Taux de reussite": "success_rate", "Effectif total": "enrollment_total"}},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "mapping_confirmed"


@pytest.mark.asyncio
async def test_quarantine_list(client: AsyncClient, db_session):
    from backend.services.ingestion_service.models.import_record import ImportRecord, QuarantineRow

    import_id = uuid.uuid4()
    inst_id = uuid.uuid4()
    user_id = uuid.uuid4()
    token = make_token(user_id=user_id, institution_id=inst_id, role=Role.INSTITUTION_ADMIN)

    record = ImportRecord(
        id=import_id,
        institution_id=inst_id,
        uploaded_by=user_id,
        original_filename="test.csv",
        storage_path="/tmp/test.csv",
        file_size_bytes=100,
        status="validated",
    )
    db_session.add(record)

    q = QuarantineRow(
        import_id=import_id,
        row_index=0,
        raw_data={"success_rate": "105"},
        failed_field="success_rate",
        failure_reason_fr="Taux de reussite hors limites.",
    )
    db_session.add(q)
    await db_session.commit()

    response = await client.get(
        f"/imports/{import_id}/quarantine",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["quarantine_count"] == 1
    assert body["rows"][0]["failed_field"] == "success_rate"


@pytest.mark.asyncio
async def test_quarantine_override_requires_analyst(client: AsyncClient, db_session):
    """Institution admin cannot force-override a quarantined row."""
    from backend.services.ingestion_service.models.import_record import ImportRecord, QuarantineRow

    import_id = uuid.uuid4()
    q_id = uuid.uuid4()
    inst_id = uuid.uuid4()
    user_id = uuid.uuid4()
    token = make_token(user_id=user_id, institution_id=inst_id, role=Role.INSTITUTION_ADMIN)

    record = ImportRecord(
        id=import_id,
        institution_id=inst_id,
        uploaded_by=user_id,
        original_filename="f.csv",
        storage_path="/tmp/f.csv",
        file_size_bytes=10,
        status="validated",
    )
    db_session.add(record)
    q = QuarantineRow(
        id=q_id,
        import_id=import_id,
        row_index=0,
        raw_data={"success_rate": "150"},
        failed_field="success_rate",
        failure_reason_fr="Hors limites.",
    )
    db_session.add(q)
    await db_session.commit()

    response = await client.post(
        f"/imports/{import_id}/quarantine/{q_id}/resolve",
        json={
            "resolution": "override",
            "corrected_value": None,
            "override_justification": "Test override",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_commit_conflict_without_overwrite_mode(client: AsyncClient, db_session):
    """Committing when existing records exist returns 409 without overwrite_mode."""
    from backend.services.ingestion_service.models.import_record import ImportRecord, DataRecord

    import_id = uuid.uuid4()
    inst_id = uuid.uuid4()
    user_id = uuid.uuid4()
    token = make_token(user_id=user_id, institution_id=inst_id, role=Role.INSTITUTION_ADMIN)

    record = ImportRecord(
        id=import_id,
        institution_id=inst_id,
        uploaded_by=user_id,
        original_filename="f.csv",
        storage_path="/tmp/f.csv",
        file_size_bytes=10,
        domain="academic",
        period="2025-S1",
        status="validated",
        records_valid=5,
        records_warned=0,
        records_quarantined=0,
        validation_summary={"valid": 5, "warned": 0, "quarantined": 0},
    )
    db_session.add(record)

    existing = DataRecord(
        import_id=uuid.uuid4(),
        institution_id=inst_id,
        period="2025-S1",
        domain="academic",
        field_id="success_rate",
        normalized_value={"v": 75.0},  # JSON column needs dict
    )
    db_session.add(existing)
    await db_session.commit()

    # Mock the Redis publish that happens on successful commit
    with patch(
        "backend.services.ingestion_service.routers.imports.get_redis",
        create=True,
        return_value=AsyncMock(),
    ):
        with patch(
            "backend.services.ingestion_service.routers.imports.publish",
            create=True,
            new=AsyncMock(),
        ):
            response = await client.post(
                f"/imports/{import_id}/commit",
                json={},
                headers={"Authorization": f"Bearer {token}"},
            )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "COMMIT_CONFLICT"


@pytest.mark.asyncio
async def test_period_lock_blocks_commit(client: AsyncClient, db_session):
    from backend.services.ingestion_service.models.import_record import ImportRecord, LockedPeriod

    import_id = uuid.uuid4()
    inst_id = uuid.uuid4()
    user_id = uuid.uuid4()
    token = make_token(user_id=user_id, institution_id=inst_id, role=Role.INSTITUTION_ADMIN)

    record = ImportRecord(
        id=import_id,
        institution_id=inst_id,
        uploaded_by=user_id,
        original_filename="f.csv",
        storage_path="/tmp/f.csv",
        file_size_bytes=10,
        domain="academic",
        period="2025-S1",
        status="validated",
        records_valid=5,
        records_warned=0,
        records_quarantined=0,
    )
    db_session.add(record)

    lock = LockedPeriod(
        institution_id=inst_id,
        period="2025-S1",
        locked_by=user_id,
    )
    db_session.add(lock)
    await db_session.commit()

    response = await client.post(
        f"/imports/{import_id}/commit",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PERIOD_LOCKED"
