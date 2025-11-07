"""
Application entry point for AI Tutor GUI.

Sets up qasync event loop and launches the main window.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from src.interface_gui.views.main_window import MainWindow
from src.interface_common import get_facade

logger = logging.getLogger(__name__)


def create_app() -> tuple[QApplication, QEventLoop]:
    """
    Create and configure QApplication with qasync event loop.
    
    Returns:
        Tuple of (QApplication, QEventLoop)
    """
    app = QApplication(sys.argv)
    app.setApplicationName("AI Tutor")
    app.setOrganizationName("AI Tutor")
    
    # Create qasync event loop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    return app, loop


async def async_main() -> int:
    """
    Async main function that creates and shows the main window.
    
    Returns:
        Exit code (0 for success)
    """
    try:
        # Get facade instance
        facade = get_facade()
        
        # Create main window
        main_window = MainWindow(facade)
        main_window.show()
        
        # Run startup health checks
        await main_window.check_startup_health()
        
        logger.info("GUI application started successfully")
        return 0
        
    except Exception as e:
        logger.exception("Failed to start GUI application")
        return 1


def main() -> int:
    """
    Main entry point for GUI application.
    
    Sets up qasync event loop and runs the application.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    app, loop = create_app()
    
    try:
        # Run async main function
        exit_code = loop.run_until_complete(async_main())
        
        # Start event loop
        with loop:
            sys.exit(app.exec())
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 1
    except Exception as e:
        logger.exception("Fatal error in GUI application")
        return 1


if __name__ == "__main__":
    sys.exit(main())

