# Documentation Index

## 📚 Quick Links

- [README](../README.md) - Project overview and setup
- [CLAUDE.md](../CLAUDE.md) - AI assistant development guide  
- [AGENTS.md](../AGENTS.md) - Agent-specific rules and guidelines
- [START_HERE.md](../START_HERE.md) - First-time contributor guide
- [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) - Command cheat sheet

## 🏗️ Architecture Documentation

Located in `docs/architecture/`:

- **DATABASE_ARCHITECTURE.md** - Pure data storage principle, no DB logic
- Database schema design and migration strategy
- Application-side business logic patterns

## 📖 Guides

Located in `docs/guides/`:

- **APPLY_MIGRATION.md** - How to apply database migrations on remote servers
- Deployment procedures
- Development workflows

## 📊 Analysis & Reports

Located in `docs/analysis/`:

- **DDD_COMPLIANCE_ANALYSIS.md** - Domain-Driven Design implementation review
- **DDD_EXECUTIVE_SUMMARY.md** - High-level DDD compliance status
- **COMPREHENSIVE_CODEBASE_ANALYSIS.md** - Full codebase structure analysis
- **ANALYSIS_SUMMARY.md** - Key findings and recommendations
- **PROJECT_ANALYSIS_REPORT.md** - Project status and metrics

## 🎯 Domain-Specific Docs

Located in root directory:

- `booking.md` - Booking system business rules
- `messaging.md` - Messaging system architecture
- `settings.md` - Application settings and configuration
- `tutor-booking.md` - Tutor booking workflows
- `tutor_dash_rules.md` - Tutor dashboard rules

## 🔧 Frontend Documentation

- `frontend/USER_ROLES.md` - Frontend role-based access control

## 📦 Module Documentation

- `backend/alembic/README.md` - Alembic migration tool (legacy, not used)
- `database/migrations/README.md` - Active migration system (auto-applied)

## 🗄️ Archive

- `database/migrations_archive/` - Historical migrations (reference only)

---

## Documentation Philosophy

Following **DDD+KISS** principles:

✅ **Keep It Simple**: Minimal docs, maximum clarity  
✅ **Single Source of Truth**: Code is documentation when clear  
✅ **Auto-Generated**: Migrations, schemas, and APIs self-document  
✅ **Living Documents**: Update docs with code changes  

## Contributing to Docs

1. Keep docs close to the code they describe
2. Use Markdown for all documentation
3. Update INDEX.md when adding new docs
4. Follow existing structure and style
5. Delete outdated docs promptly

---

**Last Updated**: 2025-11-12  
**Documentation Version**: 2.0 (Cleaned & Organized)

