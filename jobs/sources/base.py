"""Shared helpers for sources."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from ..config import Config


def market_for(country: str | None) -> str:
    return "peru" if country == "PE" else "abroad"


def get_json(session: Any, url: str, cfg: Config, params: dict | None = None) -> Any:
    """GET a JSON document with the configured generic User-Agent (no personal data)."""
    response = session.get(
        url,
        params=params,
        headers={"User-Agent": cfg.user_agent, "Accept": "application/json"},
        timeout=cfg.request_timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def from_epoch(value: Any) -> date | None:
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).date()
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def from_iso(value: Any) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None
