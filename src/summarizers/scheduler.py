"""
Summarization scheduler for AI Tutor Proof of Concept.

Provides APScheduler background job for write-time summarization.
"""

import logging
from typing import Optional
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.config import (
    DB_PATH,
    SUMMARIZATION_INTERVAL_SECONDS,
    SUMMARIZATION_MAX_CONCURRENT_TOPICS,
    SUMMARIZATION_ENABLED,
)
from src.summarizers.update import (
    get_topics_needing_refresh,
    refresh_topic_summaries,
)

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[BackgroundScheduler] = None


def process_summarization_job(db_path: Optional[Path] = None) -> None:
    """
    Background job to process summarization for topics with new events.
    
    Gets topics needing refresh and processes them in batches.
    
    Args:
        db_path: Path to database file (defaults to config.DB_PATH)
    """
    if not SUMMARIZATION_ENABLED:
        logger.debug("Summarization disabled, skipping job")
        return
    
    db_path = db_path or DB_PATH
    
    try:
        # Get topics needing refresh
        topics_needing_refresh = get_topics_needing_refresh(db_path=db_path)
        
        if not topics_needing_refresh:
            logger.debug("No topics need summarization refresh")
            return
        
        logger.info(f"Processing summarization for {len(topics_needing_refresh)} topics")
        
        # Process topics in batches (respect max concurrent)
        batch_size = SUMMARIZATION_MAX_CONCURRENT_TOPICS
        for i in range(0, len(topics_needing_refresh), batch_size):
            batch = topics_needing_refresh[i:i + batch_size]
            
            # Refresh batch
            results = refresh_topic_summaries(
                topic_ids=batch,
                db_path=db_path,
            )
            
            # Log results
            success_count = sum(1 for topic, _ in results.values() if topic is not None)
            failure_count = len(results) - success_count
            
            logger.info(
                f"Processed batch: {success_count} succeeded, {failure_count} failed "
                f"out of {len(batch)} topics"
            )
    
    except Exception as e:
        logger.error(f"Summarization job failed: {e}", exc_info=True)


def start_summarization_scheduler(
    db_path: Optional[Path] = None,
    interval_seconds: Optional[int] = None,
) -> BackgroundScheduler:
    """
    Start background scheduler for summarization jobs.
    
    Args:
        db_path: Path to database file (defaults to config.DB_PATH)
        interval_seconds: Optional interval in seconds (defaults to config.SUMMARIZATION_INTERVAL_SECONDS)
        
    Returns:
        BackgroundScheduler instance
    """
    global _scheduler
    
    if _scheduler and _scheduler.running:
        logger.warning("Summarization scheduler already running")
        return _scheduler
    
    interval = interval_seconds or SUMMARIZATION_INTERVAL_SECONDS
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=process_summarization_job,
        trigger=IntervalTrigger(seconds=interval),
        args=(db_path,),
        id="summarization_job",
        name="Process summarization for topics with new events",
        replace_existing=True,
    )
    
    scheduler.start()
    _scheduler = scheduler
    
    logger.info(f"Summarization scheduler started with {interval}s interval")
    
    return scheduler


def stop_summarization_scheduler() -> None:
    """Stop background scheduler for summarization jobs."""
    global _scheduler
    
    if _scheduler and _scheduler.running:
        _scheduler.shutdown()
        _scheduler = None
        logger.info("Summarization scheduler stopped")
    else:
        logger.warning("Summarization scheduler not running")


def is_scheduler_running() -> bool:
    """Check if summarization scheduler is running."""
    return _scheduler is not None and _scheduler.running

