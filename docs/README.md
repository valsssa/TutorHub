# Documentation Index

Complete documentation for TutorHub project.

---

## Quick Links

- **[Getting Started](../START_HERE.md)** - First-time setup guide
- **[Main README](../README.md)** - Project overview
- **[Quick Reference](../QUICK_REFERENCE.md)** - Command cheat sheet
- **[Claude AI Guide](../CLAUDE.md)** - AI assistant guidance
- **[Linting Guide](../LINTING.md)** - Code quality tools

---

## Documentation Structure

### 📋 API & Reference

- **[API Reference](./API_REFERENCE.md)** - Complete API endpoint documentation
- **[Frontend-Backend API Mapping](./FRONTEND_BACKEND_API_MAPPING.md)** - API integration mapping
- **[Avatar Reference](./AVATAR_REFERENCE.md)** - Avatar upload and management
- **[User Roles](./USER_ROLES.md)** - Role system and permissions

### 🏗️ Architecture

- **[Database Architecture](./architecture/DATABASE_ARCHITECTURE.md)** - Database design principles and schema
  - "No Logic in DB" principle
  - Performance indexes
  - Migration strategy

### 🔄 User Flows

**[Flows Directory](./flows/)** - Detailed user flow documentation

1. **[Authentication Flow](./flows/01_AUTHENTICATION_FLOW.md)** - Login, registration, password reset
2. **[Booking Flow](./flows/02_BOOKING_FLOW.md)** - Session booking and management
3. **[Messaging Flow](./flows/03_MESSAGING_FLOW.md)** - Real-time messaging system
4. **[Tutor Onboarding Flow](./flows/04_TUTOR_ONBOARDING_FLOW.md)** - Tutor profile setup
5. **[Student Profile Flow](./flows/05_STUDENT_PROFILE_FLOW.md)** - Student profile management
6. **[Admin Dashboard Flow](./flows/06_ADMIN_DASHBOARD_FLOW.md)** - Admin panel operations

### 🧪 Testing

**[Testing Directory](./testing/)** - Testing guides and documentation

- **[Testing Guide](./testing/TESTING_GUIDE.md)** - Comprehensive testing strategy
- **[Playwright Guide](./testing/PLAYWRIGHT_GUIDE.md)** - E2E testing with Playwright
- **[Playwright Quick Start](./testing/PLAYWRIGHT_QUICK_START.md)** - Quick setup guide
- **[Playwright README](./testing/PLAYWRIGHT_README.md)** - Detailed Playwright documentation

---

## Additional Resources

### Database

- **[Database Source of Truth](../database/SOURCE_OF_TRUTH.md)** - Canonical database documentation
- **[Migration System](../database/migrations/README.md)** - Database migration guide

### Frontend

- **[Integration Tests](../frontend/__tests__/integration/README.md)** - Frontend integration test guide
- **[E2E Tests](../frontend/e2e/README.md)** - End-to-end test documentation

### Backend

- **[Alembic Migrations](../backend/alembic/README.md)** - Alembic migration setup

---

## Documentation Standards

### File Naming
- Use `UPPERCASE_WITH_UNDERSCORES.md` for root-level guides
- Use `01_descriptive_name.md` for numbered sequences
- Use `README.md` for directory indexes

### Content Guidelines
- Start with a clear title and brief description
- Include table of contents for long documents
- Use code blocks with language syntax highlighting
- Add examples for all complex concepts
- Link to related documentation
- Keep documents focused and concise

### When to Create New Documentation
- New feature implementation
- Architectural decision changes
- Complex workflows added
- API endpoint additions

### Where to Place Documentation
- **Root level**: Project-wide guides (README, START_HERE, LINTING)
- **docs/**: All detailed documentation
- **docs/architecture/**: System design and architecture
- **docs/flows/**: User journey documentation
- **docs/testing/**: Testing strategies and guides
- **Component folders**: Component-specific README files

---

## Contributing to Documentation

When updating documentation:

1. Keep it current with code changes
2. Update this index when adding new docs
3. Follow conventional commit messages:
   ```bash
   docs(api): update booking endpoint documentation
   docs(testing): add E2E test examples
   ```
4. Run linting on markdown files:
   ```bash
   # Check for broken links
   ./scripts/check-docs-links.sh
   ```

---

## Need Help?

- **Setup Issues**: See [START_HERE.md](../START_HERE.md)
- **Development**: See [CLAUDE.md](../CLAUDE.md)
- **Commands**: See [QUICK_REFERENCE.md](../QUICK_REFERENCE.md)
- **Testing**: See [Testing Guide](./testing/TESTING_GUIDE.md)
- **API**: See [API Reference](./API_REFERENCE.md)

---

**Last Updated**: 2026-01-28
