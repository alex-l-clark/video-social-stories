# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in this project, please report it privately by emailing the maintainers. Do not create public issues for security vulnerabilities.

## Repository Security Configuration

### Administrator Steps for Enhanced Security

To protect against accidental commits of secrets and certificates, administrators should enable the following GitHub security features:

#### 1. Enable Push Protection for Secrets

1. Go to **Settings** → **Code security and analysis**
2. Enable **Secret scanning**
3. Enable **Push protection** for secret scanning
4. This will block pushes that contain known secret patterns

#### 2. Create Branch Protection Rules

1. Go to **Settings** → **Branches**
2. Add a branch protection rule for the default branch (`main`)
3. Configure the following requirements:
   - ✅ **Require a pull request before merging**
   - ✅ **Require status checks to pass before merging**
     - Add required status checks: `gitleaks` (from Secret Scan workflow)
   - ✅ **Require conversation resolution before merging**
   - ✅ **Restrict pushes that create files** with these patterns:
     - `*.key`
     - `*.pem` 
     - `*.crt`
     - `*.p12`
     - `*.der`
     - `*.pfx`
   - ✅ **Require at least 1 review**

#### 3. Enable Additional Security Features

1. **Dependency scanning**: Enable Dependabot alerts
2. **Code scanning**: Enable CodeQL analysis  
3. **Private vulnerability reporting**: Enable for responsible disclosure

## Development Security Requirements

### Pre-commit Hooks

All developers must install and use pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

This will automatically scan for secrets before commits.

### Prohibited Content

Never commit the following to this repository:

- Private keys (`*.key`, `*.pem`)
- Certificates (`*.crt`, `*.der`, `*.p12`, `*.pfx`)
- Environment files with real credentials (`.env` with actual API keys)
- Database connection strings with credentials
- Authentication tokens or API keys

### Test Certificates

For testing purposes, use the ephemeral certificate generation script:

```bash
./scripts/generate_smoke_certs.sh
```

These certificates are automatically ignored by `.gitignore` and expire after 7 days.

## Incident Response

If secrets are accidentally committed:

1. **Immediately revoke/rotate** the exposed credentials
2. **Run the cleanup procedure** documented in this repository
3. **Notify the security team** of the incident
4. **Force push** cleaned history (coordinating with all collaborators)

## Security Scanning

This repository includes automated security scanning:

- **Secret scanning**: Runs on every push and PR via GitHub Actions
- **History verification**: Use `./scripts/verify_no_secrets.sh` to check for leaked secrets
- **Pre-commit scanning**: Gitleaks runs before each commit

## Compliance

This project follows security best practices including:

- No hardcoded secrets or credentials
- Ephemeral test certificates only
- Automated secret detection
- Protected branch policies
- Regular security audits
