"""Rapport över en kontrollerad spellista, och hur den visas som text, JSON eller HTML."""

from __future__ import annotations

import html
import json
from dataclasses import dataclass, replace

from . import __version__
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


def render_json(report: Report) -> str:
    data = {
        "version": __version__,
        "channels": report.channel_count,
        "errors": len(report.errors),
        "warnings": len(report.warnings),
        "issues": [
            {
                "line": issue.line,
                "level": issue.level.value,
                "code": issue.code,
                "message": issue.message,
                "channel": issue.channel.name if issue.channel else None,
            }
            for issue in report.shown
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


_HTML = """<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>m3u-check: {title}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 60rem; padding: 0 1rem; color: #1a1a1a; background: #fff; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ text-align: left; padding: .4rem .6rem; border-bottom: 1px solid #ddd; vertical-align: top; }}
  td.line {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .error {{ color: #b00020; font-weight: 600; }}
  .warning {{ color: #8a5a00; }}
  code {{ font-size: .9em; }}
  @media (prefers-color-scheme: dark) {{
    body {{ color: #e6e6e6; background: #161616; }}
    th, td {{ border-color: #333; }}
    .error {{ color: #ff6b81; }}
    .warning {{ color: #f0b429; }}
  }}
</style>
</head>
<body>
<h1>m3u-check: {title}</h1>
<p>{summary}</p>
<table>
<thead><tr><th>Rad</th><th>Nivå</th><th>Meddelande</th><th>Kod</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
<p><small>m3u-check {version}</small></p>
</body>
</html>
"""


def render_html(report: Report, title: str = "rapport") -> str:
    rows = "\n".join(
        f'<tr><td class="line">{issue.line}</td>'
        f'<td class="{issue.level.value}">{issue.level.value.upper()}</td>'
        f"<td>{html.escape(issue.message)}</td><td><code>{issue.code}</code></td></tr>"
        for issue in report.shown
    )
    return _HTML.format(
        title=html.escape(title), summary=html.escape(_summary(report)), rows=rows, version=__version__
    )
