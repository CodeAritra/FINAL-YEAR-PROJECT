# Rule 02: Git Workflow & Commit Standards

To maintain clean repository history and smooth collaboration:

## 1. Conventional Commits
All commit messages must follow the Conventional Commits specification:
```
<type>(<scope>): <short description>

[optional body explaining motivation and trade-offs]

[optional footer(s), e.g. Closes #123]
```

### Allowed Types
- `feat`: A new user-facing or system feature.
- `fix`: A bug fix.
- `docs`: Documentation-only changes.
- `style`: Changes that do not affect the meaning of the code (white-space, formatting).
- `refactor`: A code change that neither fixes a bug nor adds a feature.
- `perf`: A code change that improves performance.
- `test`: Adding missing tests or correcting existing tests.
- `chore`: Changes to the build process, dependency updates, or auxiliary tools.

## 2. Commit Hygiene
- Keep commits atomic and logically separated. Do not mix unrelated refactors with new feature implementations.
- Never commit build artifacts (`node_modules/`, `dist/`, `.venv/`, `__pycache__/`, `.DS_Store`).
- Always verify `.gitignore` is in place before committing new asset trees.

