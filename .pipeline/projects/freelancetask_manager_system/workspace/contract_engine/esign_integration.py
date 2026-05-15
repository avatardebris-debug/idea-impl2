from core.contract import Contract, ContractStatus
import datetime

class ESignIntegration:
    """Mock e-signature integration (e.g. DocuSign/HelloSign)."""
    
    def send_for_signature(self, contract: Contract, client_email: str) -> str:
        """Mocks sending a contract for e-signature. Returns a mockup signature URL."""
        contract.status = ContractStatus.PENDING_SIGNATURE
        contract.signature_url = f"https://esign.mock/sign/{contract.id}?email={client_email}"
        return contract.signature_url

    def verify_signature(self, contract: Contract) -> bool:
        """Mocks verifying if a contract was signed. For testing, always returns True."""
        contract.status = ContractStatus.SIGNED
        contract.signed_at = datetime.datetime.now(datetime.UTC).isoformat()
        return True
