"""Rapport över en kontrollerad spellista, och hur den visas som text."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .checks import Issue, Level


@dataclass
class Report:
    channel_count: int
    issues: list[Issue]
    show_warnings: bool = True

    @property
    def errors(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.level is Level.ERROR]

    @property
    def warnings(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.level is Level.WARNING]

    @property
    def shown(self) -> list[Issue]:
        """De issues som visas. Summeringen räknar alltid alla."""
        return self.issues if self.show_warnings else self.errors

    def errors_only(self) -> Report:
        return replace(self, show_warnings=False)


def _summary(report: Report) -> str:
    summary = f"{report.channel_count} kanaler, {len(report.errors)} fel, {len(report.warnings)} varningar"
    if not report.show_warnings and report.warnings:
        summary += " (visas inte)"
    return summary


def render_text(report: Report) -> str:
    lines = [
        f"rad {issue.line:>4}  {issue.level.value.upper():7}  {issue.message}\n"
        for issue in report.shown
    ]
    return "".join(lines) + f"\n{_summary(report)}\n"
