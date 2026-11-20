"""Vercel-Einstieg: alle /api/*-Routen (siehe vercel.json)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from service.http import Handler  # noqa: E402


class handler(Handler):  # noqa: N801 - Vercel erwartet diesen Namen
    pass
