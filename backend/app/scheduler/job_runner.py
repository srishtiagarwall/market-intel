import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


def start_scheduler() -> AsyncIOScheduler:
    """
    Configure and start APScheduler.
    Daily signal job fires at 4:00 PM IST (10:30 UTC) on weekdays.
    """
    from app.scheduler.daily_signal_job import run_daily_signal_job

    scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")

    scheduler.add_job(
        run_daily_signal_job,
        trigger=CronTrigger(
            hour=16,
            minute=0,
            day_of_week="mon-fri",
            timezone="Asia/Kolkata",
        ),
        id="daily_signal_job",
        name="Daily Market Signal Computation",
        replace_existing=True,
        misfire_grace_time=1800,  # 30 minutes — catch up if server was down
        max_instances=1,          # never run two instances concurrently
    )

    scheduler.start()
    logger.info("[Scheduler] Started. Daily signal job scheduled at 4PM IST on weekdays.")
    return scheduler
