# Operational Runbooks

This directory contains runbooks for common operational tasks and incident response procedures.

## Runbook Index

| Runbook | Purpose | When to Use |
|---------|---------|-------------|
| [Database Operations](./database.md) | Backup, restore, migrations | Regular maintenance, DR |
| [Deployment](./deployment.md) | Deploy, rollback procedures | Releases |
| [Incident Response](./incident-response.md) | Handle production incidents | P1/P2 incidents |
| [Cache Management](./cache.md) | Redis cache operations | Cache issues |
| [Log Analysis](./logs.md) | View and analyze logs | Debugging |

## General Guidelines

1. **Read the entire runbook** before executing any steps
2. **Document any deviations** from the runbook
3. **Notify the team** via Slack before major operations
4. **Test in staging first** when possible
5. **Have a rollback plan** before making changes

## Emergency Contacts

See [LAUNCH_CHECKLIST.md](../LAUNCH_CHECKLIST.md#appendix-emergency-contacts) for emergency contacts.
