"""MASS-ADK Signal Studio package."""

try:
    from . import agent
except ModuleNotFoundError as exc:  # pragma: no cover - supports utility tests.
    if not (exc.name or "").startswith("google"):
        raise
    agent = None
