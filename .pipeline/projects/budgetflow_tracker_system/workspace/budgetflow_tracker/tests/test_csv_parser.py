"""Tests for the CSV parser."""

import os
import sys
import tempfile
import pytest
import importlib.util

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import Database, reset_database


def load_csv_parser_module():
    """Dynamically load the csv_parser module since 'import' is a Python keyword."""
    csv_parser_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'import', 'csv_parser.py')
    spec = importlib.util.spec_from_file_location("csv_parser", csv_parser_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def db_path():
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    for suffix in ('', '-wal', '-shm'):
        p = path + suffix
        if os.path.exists(p):
            try:
                os.remove(p)
            except PermissionError:
                pass


@pytest.fixture
def csv_parser(db_path):
    """Create a CSV parser with a fresh database."""
    reset_database()
    db = Database(db_path)
    db.init_schema()
    db.seed_default_data()
    csv_parser_mod = load_csv_parser_module()
    parser = csv_parser_mod.CSVParser(db)
    yield parser
    db.close()


class TestBankFormat:
    """Test BankFormat dataclass."""

    def test_chase_format(self):
        """Test Chase format detection."""
        csv_parser_mod = load_csv_parser_module()
        fmt = csv_parser_mod.BANK_FORMATS["chase"]
        assert fmt.name == "Chase"
        assert fmt.date_column == "Date"
        assert fmt.description_column == "Description"
        assert fmt.amount_column == "Amount"
        assert fmt.date_format == "%m/%d/%Y"
        assert fmt.amount_negative_is_debit is True

    def test_generic_format(self):
        """Test generic format detection."""
        csv_parser_mod = load_csv_parser_module()
        fmt = csv_parser_mod.BANK_FORMATS["generic"]
        assert fmt.name == "Generic CSV"
        assert fmt.date_column == "date"
        assert fmt.description_column == "description"
        assert fmt.amount_column == "amount"
        assert fmt.date_format == "%Y-%m-%d"


class TestCSVParserDetectFormat:
    """Test format detection."""

    def test_detect_chase_format(self, csv_parser):
        """Test detecting Chase format."""
        csv_content = "Date,Description,Amount\n01/15/2024,Grocery Store,-50.00\n"
        fmt = csv_parser.detect_format(csv_content)
        assert fmt.name == "Chase"

    def test_detect_wells_fargo_format(self, csv_parser):
        """Test detecting Wells Fargo format."""
        csv_content = "Date,Description,Amount\n01/15/2024,Grocery Store,-50.00\n"
        fmt = csv_parser.detect_format(csv_content)
        assert fmt.name == "Wells Fargo"

    def test_detect_bank_of_america_format(self, csv_parser):
        """Test detecting Bank of America format."""
        csv_content = "Date,Description,Amount\n01/15/2024,Grocery Store,-50.00\n"
        fmt = csv_parser.detect_format(csv_content)
        assert fmt.name == "Bank of America"

    def test_detect_generic_format(self, csv_parser):
        """Test detecting generic format."""
        csv_content = "date,description,amount\n2024-01-15,Grocery Store,-50.00\n"
        fmt = csv_parser.detect_format(csv_content)
        assert fmt.name == "Generic CSV"

    def test_detect_empty_csv(self, csv_parser):
        """Test detecting format for empty CSV."""
        fmt = csv_parser.detect_format("")
        assert fmt.name == "Generic CSV"

    def test_detect_auto_format(self, csv_parser):
        """Test auto-detecting format with custom columns."""
        csv_content = "Transaction Date,Merchant,Withdrawal\n2024-01-15,Grocery Store,-50.00\n"
        fmt = csv_parser.detect_format(csv_content)
        assert fmt.name == "Auto-detected"
        assert fmt.date_column == "Transaction Date"
        assert fmt.description_column == "Merchant"
        assert fmt.amount_column == "Withdrawal"


class TestCSVParserParse:
    """Test CSV parsing."""

    def test_parse_chase_csv(self, csv_parser):
        """Test parsing Chase format CSV."""
        csv_content = "Date,Description,Amount\n01/15/2024,Grocery Store,-50.00\n01/16/2024,Salary,2000.00\n"
        transactions = csv_parser.parse(csv_content)
        assert len(transactions) == 2
        assert transactions[0].date.isoformat() == "2024-01-15"
        assert transactions[0].description == "Grocery Store"
        assert transactions[0].amount == -50.00
        assert transactions[1].amount == 2000.00

    def test_parse_generic_csv(self, csv_parser):
        """Test parsing generic format CSV."""
        csv_content = "date,description,amount\n2024-01-15,Grocery Store,-50.00\n"
        transactions = csv_parser.parse(csv_content)
        assert len(transactions) == 1
        assert transactions[0].date.isoformat() == "2024-01-15"
        assert transactions[0].amount == -50.00

    def test_parse_empty_csv(self, csv_parser):
        """Test parsing empty CSV."""
        transactions = csv_parser.parse("")
        assert len(transactions) == 0

    def test_parse_single_line_csv(self, csv_parser):
        """Test parsing CSV with only header."""
        csv_content = "Date,Description,Amount\n"
        transactions = csv_parser.parse(csv_content)
        assert len(transactions) == 0

    def test_parse_with_commas_in_amount(self, csv_parser):
        """Test parsing CSV with commas in amount."""
        csv_content = "Date,Description,Amount\n01/15/2024,Grocery Store,-1,234.56\n"
        transactions = csv_parser.parse(csv_content)
        assert len(transactions) == 1
        assert transactions[0].amount == -1234.56

    def test_parse_with_dollar_sign(self, csv_parser):
        """Test parsing CSV with dollar sign in amount."""
        csv_content = "Date,Description,Amount\n01/15/2024,Grocery Store,-$50.00\n"
        transactions = csv_parser.parse(csv_content)
        assert len(transactions) == 1
        assert transactions[0].amount == -50.00

    def test_parse_with_spaces_in_amount(self, csv_parser):
        """Test parsing CSV with spaces in amount."""
        csv_content = "Date,Description,Amount\n01/15/2024,Grocery Store,- 50.00\n"
        transactions = csv_parser.parse(csv_content)
        assert len(transactions) == 1
        assert transactions[0].amount == -50.00

    def test_parse_invalid_date(self, csv_parser):
        """Test parsing CSV with invalid date."""
        csv_content = "Date,Description,Amount\ninvalid,Grocery Store,-50.00\n"
        transactions = csv_parser.parse(csv_content)
        assert len(transactions) == 0

    def test_parse_invalid_amount(self, csv_parser):
        """Test parsing CSV with invalid amount."""
        csv_content = "Date,Description,Amount\n01/15/2024,Grocery Store,invalid\n"
        transactions = csv_parser.parse(csv_content)
        assert len(transactions) == 0

    def test_parse_with_explicit_format(self, csv_parser):
        """Test parsing with explicit format."""
        csv_parser_mod = load_csv_parser_module()
        csv_content = "date,description,amount\n2024-01-15,Grocery Store,-50.00\n"
        transactions = csv_parser.parse(csv_content, csv_parser_mod.BANK_FORMATS["generic"])
        assert len(transactions) == 1
        assert transactions[0].date.isoformat() == "2024-01-15"


class TestCSVParserValidate:
    """Test transaction validation."""

    def test_validate_valid_transactions(self, csv_parser):
        """Test validating valid transactions."""
        csv_content = "Date,Description,Amount\n01/15/2024,Grocery Store,-50.00\n"
        transactions = csv_parser.parse(csv_content)
        errors = csv_parser.validate_transactions(transactions)
        assert len(errors) == 0

    def test_validate_empty_description(self, csv_parser):
        """Test validating transaction with empty description."""
        csv_content = "Date,Description,Amount\n01/15/2024,, -50.00\n"
        transactions = csv_parser.parse(csv_content)
        errors = csv_parser.validate_transactions(transactions)
        assert len(errors) == 1
        assert errors[0]["field"] == "description"

    def test_validate_zero_amount(self, csv_parser):
        """Test validating transaction with zero amount."""
        csv_content = "Date,Description,Amount\n01/15/2024,Grocery Store,0.00\n"
        transactions = csv_parser.parse(csv_content)
        errors = csv_parser.validate_transactions(transactions)
        assert len(errors) == 1
        assert errors[0]["field"] == "amount"

    def test_validate_future_date(self, csv_parser):
        """Test validating transaction with future date."""
        from datetime import date, timedelta
        future_date = (date.today() + timedelta(days=1)).strftime("%m/%d/%Y")
        csv_content = f"Date,Description,Amount\n{future_date},Grocery Store,-50.00\n"
        transactions = csv_parser.parse(csv_content)
        errors = csv_parser.validate_transactions(transactions)
        assert len(errors) == 1
        assert errors[0]["field"] == "date"

    def test_validate_multiple_errors(self, csv_parser):
        """Test validating transaction with multiple errors."""
        from datetime import date, timedelta
        future_date = (date.today() + timedelta(days=1)).strftime("%m/%d/%Y")
        csv_content = f"Date,Description,Amount\n{future_date},, 0.00\n"
        transactions = csv_parser.parse(csv_content)
        errors = csv_parser.validate_transactions(transactions)
        assert len(errors) == 2
        fields = {e["field"] for e in errors}
        assert "description" in fields
        assert "amount" in fields
