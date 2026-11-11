import logging
from datetime import UTC, datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from kangaroo.repositories import RecentHistoryRepository
from kangaroo.services import RecentHistoryService
from kangaroo.settings import settings

logger = logging.getLogger(__name__)


def prune_recent_history(engine: Engine) -> None:
    with Session(engine) as session, session.begin():
        RecentHistoryService(RecentHistoryRepository(session)).prune()
    logger.info("Pruned recent history")


def build_scheduler(engine: Engine) -> BlockingScheduler:
    """Schedule every background job. Jobs run in this process, not the API's."""
    scheduler = BlockingScheduler()
    scheduler.add_job(
        prune_recent_history,
        "interval",
        args=[engine],
        minutes=settings.recent_history_prune_interval_minutes,
        id="prune_recent_history",
        next_run_time=datetime.now(UTC),
        coalesce=True,
        max_instances=1,
    )
    return scheduler
