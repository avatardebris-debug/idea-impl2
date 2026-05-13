# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | Yes                |
| < 0.1   | No                 |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please:

1. **Do NOT open a public issue.**
2. Email your findings to the maintainers.
3. Include steps to reproduce the issue.
4. Allow time for a fix before public disclosure.

## Security Measures

### API Security
- **CORS**: Configurable via `CORS_ORIGINS` environment variable. Default allows all origins in development; restrict in production.
- **Rate Limiting**: Configurable via `RATE_LIMIT_PER_MINUTE`. Default is 60 requests per minute per IP.
- **Input Validation**: All API inputs are validated via Pydantic schemas.
- **SQL Injection**: All database queries use SQLAlchemy ORM parameterized queries.

### Data Security
- **Database**: SQLite database stored locally. Use a production-grade database (PostgreSQL) in production.
- **Sensitive Data**: No passwords or API keys are stored in the database.
- **File Uploads**: Not supported in the current version.

### Infrastructure Security
- **Docker**: Runs as non-root user. Health checks verify service availability.
- **Dependencies**: Regularly update dependencies via `pip`.
- **Network**: API binds to `0.0.0.0` by default. Use a reverse proxy (nginx, Caddy) in production.

## Best Practices for Production Deployment

1. Set `CORS_ORIGINS` to specific trusted domains.
2. Use a production database (PostgreSQL recommended).
3. Place the API behind a reverse proxy with TLS.
4. Configure rate limiting appropriate for your use case.
5. Monitor logs for unusual activity.
6. Keep dependencies updated.
7. Use environment variables for all configuration (never hardcode secrets).
