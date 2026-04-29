# Security Policy

## Supported Scope

Security checks cover the dashboard source, dependency files, CI workflow, and project documentation. The repository is an academic project and does not provide a formal production support SLA.

## Reporting a Vulnerability

Report suspected vulnerabilities privately to the maintainers through the repository owner's preferred contact path or Singapore Polytechnic course channels. Do not open public issues containing credentials, exploit steps, or sensitive student data.

Please include:

- A short description of the issue.
- Affected file, dependency, or workflow.
- Steps to reproduce, when safe to share.
- Suggested mitigation, if known.

## Baseline Controls

- `.env` files are ignored; `.env.example` documents safe defaults only.
- CI runs tests, syntax-focused Ruff checks, Bandit static security analysis, and `pip-audit`.
- The app reads processed data from a configurable directory instead of hard-coding local absolute paths.
- Assignment datasets should not be expanded with additional personally identifiable information.
