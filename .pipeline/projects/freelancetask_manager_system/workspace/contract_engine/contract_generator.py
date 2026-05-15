from typing import Any, Dict
from core.contract import Contract
from contract_engine.clause_library import ClauseLibrary

class ContractGenerator:
    def generate_from_proposal(self, client_id: str, proposal_id: str, amount: float, deliverables: list[str]) -> Contract:
        contract = Contract(
            client_id=client_id,
            proposal_id=proposal_id,
            amount=amount,
            deliverables=deliverables,
            clauses=ClauseLibrary.get_standard_clauses()
        )
        return contract

    def format_as_markdown(self, contract: Contract) -> str:
        lines = []
        lines.append(f"# Freelance Service Agreement")
        lines.append(f"**Contract ID:** {contract.id}")
        lines.append(f"**Date:** {contract.created_at}")
        lines.append(f"**Status:** {contract.status.value}")
        lines.append("")
        lines.append(f"## 1. Services Provided")
        for d in contract.deliverables:
            lines.append(f"- {d}")
        lines.append("")
        lines.append(f"## 2. Compensation")
        lines.append(f"The total fee for the services is **${contract.amount:.2f}**.")
        lines.append("")
        lines.append(f"## 3. Standard Terms & Conditions")
        for i, clause in enumerate(contract.clauses, 1):
            lines.append(f"**3.{i}.** {clause}")
        lines.append("")
        lines.append(f"## Signatures")
        lines.append(f"Client Signature: _______________________ Date: ________")
        lines.append(f"Provider Signature: _____________________ Date: ________")
        
        return "\n".join(lines)
