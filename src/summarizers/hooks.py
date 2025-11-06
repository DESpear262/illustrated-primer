"""
Summarization hooks for AI Tutor Proof of Concept.

Provides hooks to trigger summarization after event creation.
"""

import logging
from typing import Optional
from pathlib import Path

from src.config import DB_PATH, SUMMARIZATION_ENABLED
from src.summarizers.scheduler import process_summarization_job

logger = logging.getLogger(__name__)


def queue_summarization_job(
    event_id: Optional[str] = None,
    topic_ids: Optional[list] = None,
    db_path: Optional[Path] = None,
) -> None:
    """
    Queue summarization job after event creation.
    
    This function is called after events are created to trigger
    summarization updates. It can be used as a hook in event creation.
    
    Args:
        event_id: Optional event ID that was created
        topic_ids: Optional list of topic IDs affected
        db_path: Path to database file (defaults to config.DB_PATH)
    """
    if not SUMMARIZATION_ENABLED:
        logger.debug("Summarization disabled, skipping queue")
        return
    
    db_path = db_path or DB_PATH
    
    try:
        # Queue summarization job (non-blocking)
        # In a production system, this would use a proper job queue
        # For now, we'll use APScheduler if running, otherwise just log
        from src.summarizers.scheduler import is_scheduler_running
        
        if is_scheduler_running():
            # Scheduler will handle it on next run
            logger.debug(f"Summarization job queued for event {event_id}")
        else:
            # If scheduler not running, we could trigger immediate processing
            # but for now, just log - user can run refresh command manually
            logger.debug(
                f"Summarization job queued for event {event_id} "
                f"(scheduler not running, use 'refresh summaries' command)"
            )
    
    except Exception as e:
        logger.warning(f"Failed to queue summarization job: {e}")


def on_event_created(event: 'Event', db_path: Optional[Path] = None) -> None:
    """
    Hook to call after event creation.
    
    This function should be called after events are inserted into the database.
    It queues summarization jobs for affected topics.
    
    Args:
        event: Event that was created
        db_path: Path to database file (defaults to config.DB_PATH)
    """
    queue_summarization_job(
        event_id=event.event_id,
        topic_ids=event.topics,
        db_path=db_path,
    )

