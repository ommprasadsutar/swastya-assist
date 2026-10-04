# Swastya Assist V11.0.1 Hotfix

## Fixed
- SQLite startup migration crash caused by the `case` table name being parsed as a reserved keyword.
- Legacy migration now quotes the `case` table identifier for SQLite ALTER statements.
- Legacy risk/consent backfills now use SQLAlchemy ORM updates instead of raw `UPDATE case ...` SQL.

## Compatibility
- Existing SQLite databases are preserved and migrated in place.
- Gemini API transport is unchanged.
- UI/layout is unchanged.

## Verified
- Python syntax check: PASS
- JavaScript syntax check: PASS
- Legacy SQLite migration simulation: PASS
