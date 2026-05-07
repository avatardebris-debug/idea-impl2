"""SEC filing schema for PostgreSQL via SQLAlchemy."""

from sqlalchemy import (
    Column, Integer, String, Float, Text, Date, JSON,
    create_engine, MetaData, Table, inspect
)
from sqlalchemy.orm import declarative_base, sessionmaker
import os

Base = declarative_base()


class Filing(Base):
    """Represents a single SEC filing."""
    __tablename__ = "filings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    filing_type = Column(String(20), nullable=False, index=True)  # 10-K, 10-Q, 8-K, etc.
    filing_date = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=True)
    company_name = Column(String(255), nullable=True)
    cik = Column(String(10), nullable=True)
    financial_metrics = Column(JSON, nullable=True)  # Parsed financial data
    raw_text = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    created_at = Column(Date, default=lambda: __import__('datetime').date.today())


class Company(Base):
    """Represents a tracked company."""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=True)
    cik = Column(String(10), nullable=True)
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    market_cap = Column(Float, nullable=True)
    exchange = Column(String(20), nullable=True)
    created_at = Column(Date, default=lambda: __import__('datetime').date.today())


class StockPrice(Base):
    """Daily stock price data."""
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open_price = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
    adjusted_close = Column(Float, nullable=True)


def get_engine(db_url: str = None):
    """Get SQLAlchemy engine."""
    if db_url is None:
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                               "data", "chronovision.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        db_url = f"sqlite:///{db_path}"
    return create_engine(db_url)


def init_db(db_url: str = None):
    """Initialize database schema."""
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)
    return engine


def get_session(db_url: str = None):
    """Get a new database session."""
    engine = get_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()
