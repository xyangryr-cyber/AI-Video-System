import json
from pathlib import Path

from src.shared.constants.auth import DEFAULT_USER_ID

_BRAND_KIT_TEMPLATE: dict[str, str | None] = {
    "logo_url": None,
    "primary_color": "#000000",
    "secondary_color": "#ffffff",
    "font_family": "Inter",
}


def ensure_user_dir(base: Path | None = None) -> None:
    """Create the default user directory and seed missing files on first run."""
    root = base if base is not None else Path(".")
    user_dir = root / "data" / "users" / DEFAULT_USER_ID
    user_dir.mkdir(parents=True, exist_ok=True)

    brand_kit = user_dir / "brand_kit.json"
    if not brand_kit.exists():
        brand_kit.write_text(json.dumps(_BRAND_KIT_TEMPLATE, indent=2))
