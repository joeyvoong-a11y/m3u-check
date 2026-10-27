"""Startpunkt för PyInstaller-bygget av m3u-check.exe.

cli.py använder relativa importer och kan därför inte vara startskript
direkt, så den här filen importerar paketet som vanligt.
"""

from m3ucheck.cli import main

raise SystemExit(main())
