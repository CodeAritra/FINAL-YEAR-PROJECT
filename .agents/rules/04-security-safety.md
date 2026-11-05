# Rule 04: Security, Secrets & Sandbox Safety

Security is a non-negotiable prerequisite across all files and operations in this project.

## 1. Secrets Management
- NEVER hardcode secrets, API keys, database credentials, passwords, or private tokens in source code.
- Always load sensitive credentials from environment variables (`.env`).
- Always maintain an up-to-date `.env.example` displaying required variables without actual secrets.
- Ensure `.env` is listed in `.gitignore`.

## 2. Input Validation & Sanitization
- Never trust user input or third-party API outputs.
- Validate types, lengths, ranges, and formats at system boundaries.
- Sanitize inputs to prevent SQL Injection, Cross-Site Scripting (XSS), Command Injection, and Path Traversal attacks.

## 3. Dependency Safety
- Avoid introducing unvetted or abandoned third-party packages.
- Always use lockfiles (`package-lock.json`, `poetry.lock`, `requirements.txt` with hashes, `pnpm-lock.yaml`) to pin dependency versions.

