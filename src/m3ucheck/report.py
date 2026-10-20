"""Rapport över en kontrollerad spellista, och hur den visas som text."""

from __future__ import annotations

from dataclasses import dataclass

from .checks import Issue, Level


@dataclass
class Report:
    channel_count: int
    issues: list[Issue]

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.level is Level.ERROR]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.level is Level.WARNING]

    def errors_only(self) -> Report:
        return Report(self.channel_count, self.errors)


def render_text(report: Report) -> str:
    # Summeringen räknar issues i just den här rapporten, så en filtrerad
    # rapport (errors_only) visar "0 varningar".
    lines = [f"rad {i.line:>4}  {i.level.value.upper():7}  {i.message}\n" for i in report.issues]
    summary = f"{report.channel_count} kanaler, {len(report.errors)} fel, {len(report.warnings)} varningar"
    return "".join(lines) + f"\n{summary}\n"
