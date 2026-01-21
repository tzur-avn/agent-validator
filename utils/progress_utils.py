"""Progress tracking utilities for agent execution."""

import logging
from typing import Optional, Callable
from contextlib import contextmanager
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.console import Console

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Track progress of agent execution with visual feedback."""

    def __init__(self, show_progress: bool = True):
        """
        Initialize progress tracker.

        Args:
            show_progress: Whether to show progress bars (default: True)
        """
        self.show_progress = show_progress
        self.console = Console()
        self._progress: Optional[Progress] = None
        self._task_ids = {}

    def _create_progress(self) -> Progress:
        """Create a rich Progress instance with custom columns."""
        return Progress(
            SpinnerColumn(),
            TextColumn("{task.description}", markup=True),
            BarColumn(complete_style="green", finished_style="bold green"),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            transient=False,
            refresh_per_second=10,
        )

    @contextmanager
    def track(self, description: str = "Processing", total: int = 100):
        """
        Context manager for tracking progress.

        Args:
            description: Task description
            total: Total number of steps

        Yields:
            Callable to update progress
        """
        if not self.show_progress:
            # Provide a no-op function if progress is disabled
            yield lambda advance=1: None
            return

        if self._progress is None:
            self._progress = self._create_progress()
            self._progress.start()

        task_id = self._progress.add_task(description, total=total)
        self._task_ids[description] = task_id

        def update_progress(advance: int = 1):
            """Update progress by advancing the task."""
            if self._progress:
                self._progress.update(task_id, advance=advance)

        try:
            yield update_progress
        finally:
            # Mark task as complete
            if self._progress:
                self._progress.update(task_id, completed=total)

    def start_task(
        self, agent_name: str, description: str = "Initializing", total: int = 100
    ) -> str:
        """
        Start a new progress task.

        Args:
            agent_name: Name of the agent
            description: Initial description (can already include formatting)
            total: Total steps

        Returns:
            Task identifier
        """
        if not self.show_progress:
            return ""

        if self._progress is None:
            self._progress = self._create_progress()
            self._progress.start()

        # Use description as-is (already formatted in orchestrator)
        task_id = self._progress.add_task(description, total=total)
        self._task_ids[agent_name] = task_id

        return agent_name

    def update_task(
        self,
        task_key: str,
        advance: int = 1,
        description: Optional[str] = None,
        completed: Optional[int] = None,
    ):
        """
        Update a task's progress.

        Args:
            task_key: Task identifier (agent name)
            advance: Amount to advance
            description: Optional new description
            completed: Optional completed count
        """
        if not self.show_progress or not self._progress:
            return

        task_id = self._task_ids.get(task_key)
        if task_id is None:
            logger.warning(f"Task {task_key} not found in progress tracker")
            return

        kwargs = {}
        if advance:
            kwargs["advance"] = advance
        if description:
            kwargs["description"] = description
        if completed is not None:
            kwargs["completed"] = completed

        self._progress.update(task_id, **kwargs)

    def complete_task(self, task_key: str):
        """
        Mark a task as complete.

        Args:
            task_key: Task identifier (agent name)
        """
        if not self.show_progress or not self._progress:
            return

        task_id = self._task_ids.get(task_key)
        if task_id is None:
            return

        # Get the task's total and set completed to total
        task = self._progress.tasks[task_id]
        self._progress.update(task_id, completed=task.total)

    def stop(self):
        """Stop and clean up progress display."""
        if self._progress:
            self._progress.stop()
            self._progress = None
            self._task_ids.clear()

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and clean up."""
        self.stop()
        return False
