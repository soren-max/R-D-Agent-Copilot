# Database Slow Query

## Slow Query After Release

Database slow query issues are commonly caused by missing indexes, changed query conditions, increased result set size, or transaction lock contention.

Recommended checks:

- Review slow query logs and execution plan.
- Check whether the release changed SQL predicates or sort fields.
- Confirm index coverage for filter and join columns.
- Inspect lock wait and transaction duration.

Risk note: avoid adding indexes directly in production without checking table size and migration impact.
