from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import uuid
import datetime

class ContractStatus(Enum):
    DRAFT = "draft"
    PENDING_SIGNATURE = "pending_signature"
    SIGNED = "signed"
    EXPIRED = "expired"

@dataclass
class Contract:
    client_id: str
    proposal_id: str
    amount: float
    deliverables: List[str]
    clauses: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: ContractStatus = ContractStatus.DRAFT
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    signed_at: Optional[str] = None
    signature_url: Optional[str] = None
