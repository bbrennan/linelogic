# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: security@linelogic.dev (or your designated email).

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will respond within 48 hours and provide a timeline for a fix.

## Security Best Practices

### API Keys and Secrets

- Never commit API keys, tokens, or credentials
- Use environment variables for sensitive data
- Always use `.env` file (not committed)
- Rotate keys regularly

### Data Handling

- LineLogic is designed for paper trading only in POC phase
- No real money or personal financial data is handled
- User data should be treated as sensitive
- Follow data minimization principles

### Dependencies

- We regularly update dependencies for security patches
- Use `pip-audit` or similar tools to check for vulnerabilities
- Pin dependency versions in production

### Code Review

- All changes require review before merging
- Security-sensitive code requires additional scrutiny
- Use static analysis tools (ruff, mypy)

### Rate Limiting and API Usage

- Respect all third-party API rate limits
- Implement defensive caching
- Never expose API keys in logs or error messages

## Known Limitations

### POC Disclaimer

This is a proof-of-concept system for paper trading and research purposes:
- Not designed for production financial transactions
- No guarantees of accuracy or reliability
- All predictions are probabilistic estimates with uncertainty

### Third-Party APIs

- BALLDONTLIE: Community API, unofficial, no SLA
- nba_api: Unofficial scraper, subject to breakage
- Risk of service interruptions or API changes

## Compliance

### Responsible Use

- LineLogic is a decision support tool, not an auto-betting system
- Users are responsible for compliance with local gambling laws
- Never use for underage gambling or in prohibited jurisdictions
- Avoid promoting irresponsible gambling behavior

### Data Privacy

- Minimal data collection
- No sharing of user data with third parties
- Local storage by default
- Users control their data

## Security Roadmap

Future enhancements:
- [ ] Encrypted credential storage
- [ ] Audit logging for sensitive operations
- [ ] Rate limiting per user/session
- [ ] Input validation framework
- [ ] Security scanning in CI/CD
