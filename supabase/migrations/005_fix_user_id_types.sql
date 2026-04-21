-- ============================================================
-- Finsight AI — Fix user_id columns: UUID → TEXT (Clerk IDs)
--
-- Root cause: tables created with user_id UUID cannot accept
-- Clerk text IDs like "user_xxx".  RLS policies block ALTER
-- COLUMN TYPE, so they must be dropped first.
--
-- FK constraints are dropped and NOT recreated here because
-- user_profiles may still have its PK as UUID (id).  The app
-- uses the service-role key which bypasses RLS; auth is enforced
-- in FastAPI.  Run 001_initial_schema.sql on a fresh DB to get
-- proper FKs from the start.
--
-- Idempotent — safe to run multiple times.
-- ============================================================

-- ── Step 1: convert user_profiles PK to text if still UUID ──────────────────
-- If user_profiles.id is UUID and clerk_id doesn't exist yet,
-- add clerk_id as a separate unique text column so future FK
-- references can point to it.  Existing rows will have NULL
-- clerk_id until a user logs in and triggers profile upsert.
DO $$
BEGIN
  -- Case A: id is already text → just rename to clerk_id
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'user_profiles'
      AND column_name = 'id'
      AND data_type = 'text'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'user_profiles' AND column_name = 'clerk_id'
  ) THEN
    ALTER TABLE user_profiles RENAME COLUMN id TO clerk_id;

  -- Case B: id is UUID, no clerk_id yet → add clerk_id text column
  ELSIF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'user_profiles'
      AND column_name = 'id'
      AND data_type IN ('uuid', 'character varying', 'varchar')
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'user_profiles' AND column_name = 'clerk_id'
  ) THEN
    ALTER TABLE user_profiles ADD COLUMN clerk_id TEXT UNIQUE;
  END IF;
END $$;

-- ── Step 2: generic helper — drop all policies, alter type, no FK re-add ─────
-- We skip FK re-add because the referenced column (clerk_id) may not yet
-- be the PK of user_profiles. The application enforces ownership in code.

-- watchlists
DO $$
DECLARE pol RECORD;
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'watchlists'
      AND column_name = 'user_id'
      AND data_type = 'uuid'
  ) THEN
    FOR pol IN SELECT policyname FROM pg_policies WHERE tablename = 'watchlists' LOOP
      EXECUTE format('DROP POLICY IF EXISTS %I ON watchlists', pol.policyname);
    END LOOP;
    ALTER TABLE watchlists DROP CONSTRAINT IF EXISTS watchlists_user_id_fkey;
    ALTER TABLE watchlists ALTER COLUMN user_id TYPE TEXT USING user_id::TEXT;
  END IF;
END $$;

-- broker_accounts
DO $$
DECLARE pol RECORD;
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'broker_accounts'
      AND column_name = 'user_id'
      AND data_type = 'uuid'
  ) THEN
    FOR pol IN SELECT policyname FROM pg_policies WHERE tablename = 'broker_accounts' LOOP
      EXECUTE format('DROP POLICY IF EXISTS %I ON broker_accounts', pol.policyname);
    END LOOP;
    ALTER TABLE broker_accounts DROP CONSTRAINT IF EXISTS broker_accounts_user_id_fkey;
    ALTER TABLE broker_accounts ALTER COLUMN user_id TYPE TEXT USING user_id::TEXT;
  END IF;
END $$;

-- holdings
DO $$
DECLARE pol RECORD;
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'holdings'
      AND column_name = 'user_id'
      AND data_type = 'uuid'
  ) THEN
    FOR pol IN SELECT policyname FROM pg_policies WHERE tablename = 'holdings' LOOP
      EXECUTE format('DROP POLICY IF EXISTS %I ON holdings', pol.policyname);
    END LOOP;
    ALTER TABLE holdings DROP CONSTRAINT IF EXISTS holdings_user_id_fkey;
    ALTER TABLE holdings ALTER COLUMN user_id TYPE TEXT USING user_id::TEXT;
  END IF;
END $$;

-- transactions
DO $$
DECLARE pol RECORD;
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'transactions'
      AND column_name = 'user_id'
      AND data_type = 'uuid'
  ) THEN
    FOR pol IN SELECT policyname FROM pg_policies WHERE tablename = 'transactions' LOOP
      EXECUTE format('DROP POLICY IF EXISTS %I ON transactions', pol.policyname);
    END LOOP;
    ALTER TABLE transactions DROP CONSTRAINT IF EXISTS transactions_user_id_fkey;
    ALTER TABLE transactions ALTER COLUMN user_id TYPE TEXT USING user_id::TEXT;
  END IF;
END $$;

-- predictions
DO $$
DECLARE pol RECORD;
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'predictions'
      AND column_name = 'user_id'
      AND data_type = 'uuid'
  ) THEN
    FOR pol IN SELECT policyname FROM pg_policies WHERE tablename = 'predictions' LOOP
      EXECUTE format('DROP POLICY IF EXISTS %I ON predictions', pol.policyname);
    END LOOP;
    ALTER TABLE predictions DROP CONSTRAINT IF EXISTS predictions_user_id_fkey;
    ALTER TABLE predictions ALTER COLUMN user_id TYPE TEXT USING user_id::TEXT;
  END IF;
END $$;

-- alert_configurations
DO $$
DECLARE pol RECORD;
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'alert_configurations'
      AND column_name = 'user_id'
      AND data_type = 'uuid'
  ) THEN
    FOR pol IN SELECT policyname FROM pg_policies WHERE tablename = 'alert_configurations' LOOP
      EXECUTE format('DROP POLICY IF EXISTS %I ON alert_configurations', pol.policyname);
    END LOOP;
    ALTER TABLE alert_configurations DROP CONSTRAINT IF EXISTS alert_configurations_user_id_fkey;
    ALTER TABLE alert_configurations ALTER COLUMN user_id TYPE TEXT USING user_id::TEXT;
  END IF;
END $$;

-- ── Step 3: ensure user_profiles itself accepts clerk text IDs ───────────────
-- If user_profiles has no clerk_id column at all (schema was never migrated),
-- the backend upsert will use clerk_id key.  Make sure that column exists.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'user_profiles' AND column_name = 'clerk_id'
  ) THEN
    ALTER TABLE user_profiles ADD COLUMN clerk_id TEXT UNIQUE;
  END IF;
END $$;
