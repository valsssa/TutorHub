# Linting Setup - Quick Start ⚡

Get code quality tools running in **5 minutes**.

---

## Step 1: Install Pre-commit (One-Time Setup)

```bash
# Install pre-commit package
pip install pre-commit

# Install git hooks
pre-commit install

# Verify installation
pre-commit --version
```

**What happens**: Pre-commit hooks will now run automatically on every `git commit`.

---

## Step 2: Install Dependencies

### Backend

```bash
# Rebuild backend with linting tools
docker compose down
docker compose up -d --build backend
```

### Frontend

```bash
# Install Prettier and other tools
docker compose exec frontend npm install
```

---

## Step 3: Test the Setup

```bash
# Run linters on all code (check mode)
./scripts/lint-all.sh

# If you see errors, auto-fix them
./scripts/lint-all.sh --fix
```

Expected output:
```
🔍 Running backend linting checks...
📋 Running Ruff linter...
✅ Ruff check complete

📝 Running Ruff formatter...
✅ Format check complete

🔎 Running MyPy type checker...
✅ Type check complete

🔒 Running Bandit security scanner...
✅ Security scan complete

✨ Backend linting complete!

🔍 Running frontend linting checks...
📋 Running ESLint...
✅ ESLint check complete

📝 Running Prettier...
✅ Prettier check complete

🔎 Running TypeScript type checker...
✅ Type check complete

✨ Frontend linting complete!
```

---

## Step 4: Configure Your IDE (Optional but Recommended)

### Visual Studio Code

1. Install extensions:
   - Python (Microsoft)
   - Pylance
   - Ruff
   - ESLint
   - Prettier

2. Settings will be auto-detected from config files

### PyCharm

1. Go to **Settings → Tools → Python Integrated Tools**
2. Set Ruff as linter
3. Enable code inspections

---

## Step 5: Make Your First Linted Commit

```bash
# 1. Make code changes
echo "# Test file" > test.py

# 2. Stage changes
git add test.py

# 3. Commit (pre-commit hooks run automatically)
git commit -m "test: verify linting setup"

# If hooks fail, they'll auto-fix issues
# Just re-stage and commit again:
git add test.py
git commit -m "test: verify linting setup"
```

---

## Daily Usage

### Before Committing

```bash
# Quick check
./scripts/lint-all.sh --fix

# Run tests
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Commit
git add .
git commit -m "feat: your changes"
```

### If Pre-commit is Slow

```bash
# Skip specific hooks (emergency only)
SKIP=mypy,typescript git commit -m "message"

# Skip all hooks (NOT recommended)
git commit --no-verify -m "message"
```

---

## Common Commands

```bash
# Backend only
./scripts/lint-backend.sh          # Check
./scripts/lint-backend.sh --fix    # Fix

# Frontend only
./scripts/lint-frontend.sh          # Check
./scripts/lint-frontend.sh --fix    # Fix

# All checks
./scripts/lint-all.sh               # Check
./scripts/lint-all.sh --fix         # Fix

# Pre-commit manual run
pre-commit run --all-files          # All files
pre-commit run ruff --all-files     # Specific hook
```

---

## Tools Installed

| Tool | Purpose | Backend | Frontend |
|------|---------|---------|----------|
| **Ruff** | Linter & Formatter | ✅ | - |
| **MyPy** | Type Checker | ✅ | - |
| **Bandit** | Security Scanner | ✅ | - |
| **ESLint** | Linter | - | ✅ |
| **Prettier** | Formatter | - | ✅ |
| **TypeScript** | Type Checker | - | ✅ |

---

## What Gets Checked Automatically?

When you commit, these run automatically:
- ✅ Code formatting (Ruff, Prettier)
- ✅ Import sorting
- ✅ Type checking (MyPy, TypeScript)
- ✅ Security scanning (Bandit)
- ✅ Linting errors (Ruff, ESLint)
- ✅ Secret detection (no committed passwords)
- ✅ File checks (trailing whitespace, EOF)

---

## Troubleshooting

### Issue: "pre-commit: command not found"

```bash
# Solution: Install pre-commit
pip install pre-commit
pre-commit install
```

### Issue: "ruff: command not found" in Docker

```bash
# Solution: Rebuild backend
docker compose down
docker compose up -d --build backend
```

### Issue: Too many linting errors

```bash
# Solution: Auto-fix what you can
./scripts/lint-all.sh --fix

# Then fix remaining issues manually
```

### Issue: Pre-commit hooks are slow

```bash
# Temporary: Skip slow hooks
SKIP=mypy git commit -m "message"

# Permanent: Update .pre-commit-config.yaml
# Comment out slow hooks for local development
```

---

## Next Steps

1. ✅ **Done with setup?** Read full guide: [`LINTING.md`](LINTING.md)
2. 📚 **Learn best practices**: Check `CLAUDE.md` Code Quality section
3. 🔧 **Configure IDE**: See `LINTING.md` → IDE Integration
4. 🚀 **Add to CI/CD**: See `LINTING.md` → CI/CD Integration

---

## Quality Standards

**Before merging PRs**:
- ✅ All linters pass
- ✅ All tests pass
- ✅ Test coverage ≥80%
- ✅ No security issues
- ✅ Type checking passes

**Enforced by**:
- Pre-commit hooks (local)
- CI/CD pipeline (GitHub Actions)
- Code review (human)

---

## Help & Resources

- **Full guide**: [`LINTING.md`](LINTING.md)
- **Project guide**: [`CLAUDE.md`](CLAUDE.md)
- **Ruff docs**: https://docs.astral.sh/ruff/
- **Prettier docs**: https://prettier.io/docs/
- **Pre-commit docs**: https://pre-commit.com/

---

**Setup time**: ~5 minutes
**Benefit**: Catch bugs before they reach production
**Result**: Cleaner, safer, more maintainable code

✨ **You're all set!** Happy coding with automated quality checks.
