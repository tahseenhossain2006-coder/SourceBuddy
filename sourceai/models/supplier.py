# sourceai/models/supplier.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class Supplier:
    name: str
    website: Optional[str] = None
    location: Optional[str] = None
    moq: Optional[int] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    evidence: List[Dict[str, Any]] = field(default_factory=list)