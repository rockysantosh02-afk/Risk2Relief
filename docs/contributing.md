# Risk2Relief: Contribution Guidelines

Thank you for contributing to the Risk2Relief digital-twin platform. This repository enforces strict architectural standards, type safety, and system safety boundaries.

---

## 1. Safety Principles & Invariants

When submitting code to this repository:
1. **Never introduce hardware actuation interfaces**: The gravitational mitigation subsystem is strictly an in-silico simulation model. Pull requests attempting to connect physical actuation commands will be rejected.
2. **Layer Separation**: Adhere to the `API Route -> Domain Service -> Repository -> Database` flow. Do not place business or database logic directly inside route handlers.
3. **No Secret Commits**: Ensure `.env` or sensitive API keys are never committed. Use `.env.example` as the canonical template.
4. **Independent Architecture**: Do not import unrelated external frameworks (e.g. Flutter, Firebase, mobile-specific SDKs).

---

## 2. Git Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Follow Conventional Commits:
   - `feat: add telemetry stream parser`
   - `fix: correct stress calculation threshold`
   - `docs: update architecture diagram`
   - `test: add health check integration scenario`
3. Ensure all local verification scripts pass before opening a Pull Request:
   ```bash
   # Windows:
   .\scripts\run-checks.ps1

   # Linux / macOS:
   ./scripts/run-checks.sh
   ```

---

## 3. Code Quality Standards

- **Python**: PEP 8 compliance, full type annotations with Pydantic v2 and SQLAlchemy 2.0 typing. Formatted and linted using `ruff`.
- **TypeScript**: Strict mode enabled (`noImplicitAny: true`, `strict: true`). Zero type errors under `npm run lint`.
- **Testing**: Every new endpoint or service must have corresponding tests under `backend/tests/` or `tests/integration/`.
