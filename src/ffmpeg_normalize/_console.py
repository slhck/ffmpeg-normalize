"""
Terminal output helpers based on rich.

All human-facing output (log messages, progress bars, summary tables) goes
through a single stderr console, so that log messages are printed above live
progress bars instead of breaking them. Machine-readable output such as
`--print-stats` JSON is still written to stdout unchanged.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from types import TracebackType

from rich.console import Console
from rich.markup import escape
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Column
from rich.theme import Theme

THEME = Theme(
    {
        "log.debug": "cyan",
        "log.info": "green",
        "log.warning": "yellow",
        "log.error": "bold red",
        "log.critical": "bold white on red",
        "status.ok": "green",
        "status.skipped": "yellow",
        "status.error": "bold red",
    }
)

_console: Console | None = None


def get_console() -> Console:
    """
    Return the shared stderr console, creating it on first use.

    The console honors the usual `NO_COLOR`, `FORCE_COLOR` and `TERM`
    environment variables and only emits colors when stderr is a terminal.

    Returns:
        Console: The shared console
    """
    global _console
    if _console is None:
        _console = Console(stderr=True, theme=THEME, highlight=False)
    return _console


def display_name(path: str, max_len: int = 24) -> str:
    """
    Shorten a file path for display in a progress bar.

    Args:
        path (str): The file path
        max_len (int, optional): Maximum length. Defaults to 24.

    Returns:
        str: The base name, truncated in the middle if it is too long
    """
    name = os.path.basename(path) or path
    if len(name) <= max_len:
        return name
    keep = (max_len - 1) // 2
    return f"{name[:keep]}…{name[-(max_len - keep - 1) :]}"


class ProgressDisplay:
    """
    A progress display with one overall bar and transient per-pass bars.

    When disabled, all methods are no-ops, so callers do not need to check
    whether progress output was requested.
    """

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        self._progress: Progress | None = None
        self._overall: TaskID | None = None
        self._overall_label = ""

    def __enter__(self) -> ProgressDisplay:
        if self.enabled:
            self._progress = Progress(
                SpinnerColumn(finished_text="[green]✔[/green]"),
                TextColumn(
                    "{task.description}",
                    table_column=Column(width=40, no_wrap=True, overflow="ellipsis"),
                ),
                BarColumn(),
                TaskProgressColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                TextColumn("[dim]eta[/dim]"),
                TimeRemainingColumn(),
                console=get_console(),
            )
            self._progress.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._progress is not None:
            self._progress.stop()
            self._progress = None
            self._overall = None

    def start_overall(self, description: str, total: int) -> None:
        """
        Start (or replace) the overall bar, e.g. counting files.

        Args:
            description (str): Label of the bar
            total (int): Number of steps
        """
        if self._progress is None:
            return
        self._overall_label = description
        self._overall = self._progress.add_task(
            self._overall_description(None), total=total
        )

    def _overall_description(self, current: str | None) -> str:
        label = f"[bold]{escape(self._overall_label)}[/bold]"
        if current:
            label += f" [cyan]{escape(current)}[/cyan]"
        return label

    def set_current(self, name: str | None) -> None:
        """
        Show the name of the item currently being processed next to the overall bar.

        Args:
            name (str | None): The name, or None to clear it
        """
        if self._progress is not None and self._overall is not None:
            self._progress.update(
                self._overall, description=self._overall_description(name)
            )

    def advance_overall(self) -> None:
        """Advance the overall bar by one step."""
        if self._progress is not None and self._overall is not None:
            self._progress.advance(self._overall)

    @contextmanager
    def task(self, description: str) -> Iterator[Callable[[float], None]]:
        """
        Show a transient bar for a single ffmpeg run that reports 0-100%.

        Args:
            description (str): Label of the bar

        Yields:
            Callable[[float], None]: Function to call with the current percentage
        """
        if self._progress is None:
            yield lambda _: None
            return

        progress = self._progress
        task_id = progress.add_task(f"  {escape(description)}", total=100)

        def update(percentage: float) -> None:
            progress.update(task_id, completed=percentage)

        try:
            yield update
        finally:
            progress.remove_task(task_id)
