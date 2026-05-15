import pytest
import datetime
from core.contract import Contract, ContractStatus
from contract_engine.clause_library import ClauseLibrary
from contract_engine.contract_generator import ContractGenerator
from contract_engine.esign_integration import ESignIntegration

def test_contract_model():
    contract = Contract(
        client_id="c-123",
        proposal_id="p-456",
        amount=1500.0,
        deliverables=["Item A", "Item B"]
    )
    assert contract.client_id == "c-123"
    assert contract.amount == 1500.0
    assert contract.status == ContractStatus.DRAFT
    assert len(contract.id) > 10

def test_clause_library():
    standard_clauses = ClauseLibrary.get_standard_clauses()
    assert len(standard_clauses) == 3
    assert "confidential" in standard_clauses[0].lower()
    
    specific_clause = ClauseLibrary.get_clause("termination")
    assert "terminate" in specific_clause.lower()

def test_contract_generator():
    generator = ContractGenerator()
    contract = generator.generate_from_proposal(
        client_id="client-x",
        proposal_id="prop-y",
        amount=2500.50,
        deliverables=["Software module"]
    )
    
    assert contract.client_id == "client-x"
    assert len(contract.clauses) == 3
    
    markdown = generator.format_as_markdown(contract)
    assert "## 1. Services Provided" in markdown
    assert "2500.50" in markdown
    assert "Contract ID" in markdown

def test_esign_integration():
    contract = Contract(
        client_id="c",
        proposal_id="p",
        amount=100.0,
        deliverables=["D"]
    )
    
    esign = ESignIntegration()
    url = esign.send_for_signature(contract, "test@example.com")
    
    assert contract.status == ContractStatus.PENDING_SIGNATURE
    assert "test@example.com" in url
    assert contract.signature_url == url
    
    verified = esign.verify_signature(contract)
    assert verified is True
    assert contract.status == ContractStatus.SIGNED
    assert contract.signed_at is not None
