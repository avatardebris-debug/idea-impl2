"""Custom exceptions for the invoice processor."""


class InvoiceProcessorError(Exception):
    """Base exception for invoice processor errors."""
    pass


class ParsingError(InvoiceProcessorError):
    """Raised when a file cannot be parsed."""
    def __init__(self, file_path: str, message: str = "Failed to parse file"):
        self.file_path = file_path
        super().__init__(f"{message} for file: {file_path}")


class LedgerError(InvoiceProcessorError):
    """Raised when a ledger operation fails."""
    pass
