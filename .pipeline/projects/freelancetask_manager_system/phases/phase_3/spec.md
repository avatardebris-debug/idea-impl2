# Phase 3 Specification: Contract Engine & Dashboard

## 1. Overview
Phase 3 finalizes the FreelanceTask Manager System by adding the Contract Engine. This subsystem bridges the gap between accepted proposals and signed agreements. It will automatically compile contract terms based on the winning proposal, client details, and SOP pricing.

## 2. Core Features

### 2.1 Core Contract Models
- **contract.py**: Defines the domain model for a contract (terms, deliverables, price, signatures).

### 2.2 Contract Engine Components
- **clause_library.py**: Contains standard legal clauses (Confidentiality, Payment Terms, Revisions).
- **contract_generator.py**: Uses the `clause_library` and a matched proposal to generate a full Markdown or PDF contract.
- **esign_integration.py**: A stub/mock class for integrating DocuSign/HelloSign (we will build the PDF/Markdown fallback generation).

### 2.3 CLI Integration
- Add `contract generate` command to `cli.py`.

## 3. Success Criteria
- [ ] `contract_engine` subsystem is implemented.
- [ ] Contract domain models exist in `core/contract.py`.
- [ ] CLI correctly parses `--match` to generate a contract.
