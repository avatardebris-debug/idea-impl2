class ClauseLibrary:
    CLAUSES = {
        "confidentiality": "Both parties agree to keep all exchanged information strictly confidential and will not disclose it to any third party without written consent.",
        "payment": "Payment shall be made in full within 14 days of invoice receipt. Late payments may incur a 1.5% monthly interest fee.",
        "revisions": "The project fee includes up to two (2) rounds of minor revisions. Additional revisions will be billed at the standard hourly rate.",
        "ownership": "Upon full payment, all intellectual property rights to the final deliverables will be transferred to the Client.",
        "termination": "Either party may terminate this contract with 7 days written notice. The Client will be billed for all work completed up to the termination date."
    }

    @classmethod
    def get_clause(cls, key: str) -> str:
        return cls.CLAUSES.get(key, "")

    @classmethod
    def get_standard_clauses(cls) -> list[str]:
        return [
            cls.CLAUSES["confidentiality"],
            cls.CLAUSES["payment"],
            cls.CLAUSES["ownership"]
        ]
