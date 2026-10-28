"""The two record types the app works with. All times are timezone-aware UTC."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Actual:
    """Measured national wind generation for one half hour (Elexon FUELHH)."""

    start_time: datetime
    generation_mw: float


@dataclass(frozen=True)
class Forecast:
    """One forecast value: made at `publish_time`, for the hour starting at `start_time` (Elexon WINDFOR)."""

    publish_time: datetime
    start_time: datetime
    generation_mw: float
