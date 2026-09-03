from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Draft:

    id: str

    proposed: dict

    status: str = "OPEN"

    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    converted_at: Optional[str] = None

    actual: Optional[dict] = None

    diff: Optional[dict] = None