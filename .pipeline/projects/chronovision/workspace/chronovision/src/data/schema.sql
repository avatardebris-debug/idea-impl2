-- Chronovision SEC Filing Database Schema
-- Compatible with PostgreSQL

CREATE TABLE IF NOT EXISTS filings (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    filing_type VARCHAR(20) NOT NULL,
    filing_date DATE NOT NULL,
    period_end DATE,
    company_name VARCHAR(255),
    cik VARCHAR(10),
    financial_metrics JSONB,
    raw_text TEXT,
    url VARCHAR(500),
    created_at DATE DEFAULT CURRENT_DATE
);

CREATE INDEX IF NOT EXISTS idx_filings_ticker ON filings(ticker);
CREATE INDEX IF NOT EXISTS idx_filings_filing_type ON filings(filing_type);
CREATE INDEX IF NOT EXISTS idx_filings_filing_date ON filings(filing_date);

CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(255),
    cik VARCHAR(10),
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap DOUBLE PRECISION,
    exchange VARCHAR(20),
    created_at DATE DEFAULT CURRENT_DATE
);

CREATE INDEX IF NOT EXISTS idx_companies_ticker ON companies(ticker);

CREATE TABLE IF NOT EXISTS stock_prices (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open_price DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    adjusted_close DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker ON stock_prices(ticker);
CREATE INDEX IF NOT EXISTS idx_stock_prices_date ON stock_prices(date);
CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker_date ON stock_prices(ticker, date);
