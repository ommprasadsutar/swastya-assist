# Swastya Assist V11.0.3 — PostgreSQL migration hotfix

V11.0.3 is a compatibility hotfix for existing V10.x/V10.4.4 PostgreSQL databases.

The V11 model adds columns that `db.create_all()` cannot add to already-existing tables.
The previous V11.0.2 startup path attempted to backfill `User.facility_id` before that column existed, causing Vercel startup failure with `psycopg.errors.UndefinedColumn`.

This hotfix:
- Adds explicit PostgreSQL schema migration for the V11 facility/reviewer/referral columns.
- Quotes PostgreSQL table/column identifiers safely, including the reserved `case` table.
- Uses PostgreSQL-native types for JSON, timestamps, and encrypted binary text fields.
- Uses `ADD COLUMN IF NOT EXISTS` so concurrent Vercel cold starts do not race on the same migration.
- Keeps the existing SQLite compatibility migration.
- Does not delete or reset the existing database.
- Preserves the existing UI and Gemini GenerateContent REST transport.

Validation performed:
- Python compile check: PASS
- V10 -> V11 model diff checked: all newly introduced persistent columns are covered by migration
