"""Measure document reading durations."""

from __future__ import annotations

from itertools import islice
from operator import itemgetter
import time
from typing import TYPE_CHECKING

from sphinx.domains import Domain
from sphinx.locale import __
from sphinx.util import logging

if TYPE_CHECKING:
    from typing import TypedDict

    from docutils import nodes
    from sphinx.application import Sphinx

    class _DurationDomainData(TypedDict):
        reading_durations: dict[str, float]


logger = logging.getLogger(__name__)


class DurationDomain(Domain):
    """A domain for durations of Sphinx processing."""

    name = 'duration'

    @property
    def reading_durations(self) -> dict[str, float]:
        return self.data.setdefault('reading_durations', {})

    def note_reading_duration(self, duration: float) -> None:
        self.reading_durations[self.env.docname] = duration

    def clear(self) -> None:
        self.reading_durations.clear()

    def clear_doc(self, docname: str) -> None:
        self.reading_durations.pop(docname, None)

    def merge_domaindata(self, docnames: set[str], otherdata: _DurationDomainData) -> None:  # type: ignore[override]
        other_reading_durations = otherdata.get('reading_durations', {})
        docnames_set = frozenset(docnames)
        for docname, duration in other_reading_durations.items():
            if docname in docnames_set:
                self.reading_durations[docname] = duration


def on_builder_inited(app: Sphinx) -> None:
    """Initialize DurationDomain on bootstrap.

    This clears the results of the last build.
    """
    domain = app.env.domains['duration']
    domain.clear()


def on_source_read(app: Sphinx, docname: str, content: list[str]) -> None:
    """Start to measure reading duration."""
    app.env.temp_data['started_at'] = time.monotonic()


def on_doctree_read(app: Sphinx, doctree: nodes.document) -> None:
    """Record a reading duration."""
    started_at = app.env.temp_data['started_at']
    duration = time.monotonic() - started_at
    domain = app.env.domains['duration']
    domain.note_reading_duration(duration)


def on_build_finished(app: Sphinx, error: Exception) -> None:
    """Display duration ranking on the current build."""
    domain = app.env.domains['duration']
    if not domain.reading_durations:
        return
    durations = sorted(domain.reading_durations.items(), key=itemgetter(1), reverse=True)
    n_durations = 100

    logger.info('')
    logger.info(
        __(
            f'====================== slowest {n_durations} reading durations (seconds) ======================='
        )
    )
    for docname, d in islice(durations, n_durations):
        logger.info(f'{int(d)} {docname}')