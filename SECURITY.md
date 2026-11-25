# Security Policy

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Report privately by email to the maintainer (`jds068888@gmail.com`) with:

- a description of the issue and its impact,
- the affected commit or file,
- steps to reproduce, and
- any suggested mitigation.

You can expect an acknowledgement within 7 days.

## Scope notes

This repository runs a monitoring pipeline and does not ship credentials.
API keys or tokens are read from environment variables or GitHub Actions
secrets and must never be committed to the repository.

Vulnerabilities in third-party dependencies should be reported to those
projects first.
