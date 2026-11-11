from datetime import timedelta
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from kangaroo.jobs import build_scheduler, prune_recent_history
from kangaroo.repositories.repositories import utc_now
from kangaroo.repositories.tables import RecentHistoryRow
from kangaroo.services.recent_history import SAVED


def test_prune_recent_history_trims_to_saved(engine):
    now = utc_now()
    with Session(engine) as session, session.begin():
        session.add_all(
            RecentHistoryRow(
                id=uuid4(),
                owner="a",
                type="work-item",
                item_id=f"w{index}",
                title=f"Item {index}",
                to="/x",
                params={},
                search={},
                created_at=now,
                modified_at=now - timedelta(seconds=index),
            )
            for index in range(SAVED + 5)
        )

    prune_recent_history(engine)

    with Session(engine) as session:
        assert (
            session.scalar(select(func.count()).select_from(RecentHistoryRow)) == SAVED
        )


def test_build_scheduler_registers_prune_job(engine):
    scheduler = build_scheduler(engine)
    job = scheduler.get_job("prune_recent_history")
    assert job is not None
    assert job.max_instances == 1
    assert job.coalesce is True


def test_build_scheduler_registers_advance_pipelines_job(engine):
    scheduler = build_scheduler(engine)
    job = scheduler.get_job("advance_pipelines")
    assert job is not None
    assert job.max_instances == 1
    assert job.coalesce is True
