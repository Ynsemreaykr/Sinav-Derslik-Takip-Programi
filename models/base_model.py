# models/base_model.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class BaseModel:
    id: Optional[int] = None
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
