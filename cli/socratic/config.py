from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

CONFIG_PATH = Path.home() / ".socratic" / "config.json"


@dataclass
class CLIConfig:
    """Local CLI configuration stored on disk."""

    base_url: str = "http://localhost:8000/api/v1"
    token: str | None = None
    email: str | None = None

    def headers(self) -> dict[str, str]:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}


def load_config() -> CLIConfig:
    """Load config from disk or return defaults."""
    if not CONFIG_PATH.exists():
        return CLIConfig()

    try:
        data = json.loads(CONFIG_PATH.read_text())
        return CLIConfig(**data)
    except Exception:
        return CLIConfig()


def save_config(cfg: CLIConfig) -> None:
    """Persist config to disk."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(asdict(cfg), indent=2))

