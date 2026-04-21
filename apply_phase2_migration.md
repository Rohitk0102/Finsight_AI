# Apply Phase 2 Database Migration

## Quick Guide

### Step 1: Open Supabase Dashboard
1. Go to https://supabase.com/dashboard
2. Select your Finsight AI project
3. Click on "SQL Editor" in the left sidebar

### Step 2: Check if Migration is Already Applied
Run this query first to check:

```sql
-- Check if phase 2 columns exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'predictions' 
AND column_name IN ('predicted_price', 'actual_price', 'resolved_at', 'horizon_days');
```

**If you get 4 rows:** Migration is already applied ✅ (skip to Step 4)
**If you get 0 rows:** Continue to Step 3

### Step 3: Apply the Migration
Copy and paste the entire content of `supabase/migrations/003_phase2_schema.sql` into the SQL Editor and click "Run".

The migration will:
- Add new columns to `predictions` table for backtesting
- Create `ticker_sentiment` table for FinBERT scores
- Create `model_accuracy` table for ML performance tracking
- Add indexes for faster queries

### Step 4: Verify Migration Success
Run these verification queries:

```sql
-- 1. Check predictions table structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'predictions'
ORDER BY ordinal_position;

-- 2. Check new tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('ticker_sentiment', 'model_accuracy');

-- 3. Check indexes
SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'public' 
AND tablename IN ('predictions', 'model_accuracy');
```

**Expected Results:**
- Query 1: Should show columns including `predicted_price`, `actual_price`, `resolved_at`, `horizon_days`, `model_version`, `direction_correct`, `mape`
- Query 2: Should return 2 rows (ticker_sentiment, model_accuracy)
- Query 3: Should show indexes including `idx_predictions_unresolved` and `idx_model_accuracy_ticker`

### Step 5: Test with Sample Data (Optional)
```sql
-- Insert a test prediction
INSERT INTO predictions (
  user_id, 
  ticker, 
  signal, 
  confidence, 
  risk_score,
  predicted_price,
  current_price_at_pred,
  horizon_days
) VALUES (
  (SELECT id FROM auth.users LIMIT 1),
  'TEST.NS',
  'BUY',
  0.85,
  3.5,
  1000.00,
  950.00,
  7
);

-- Verify it was inserted
SELECT * FROM predictions WHERE ticker = 'TEST.NS';

-- Clean up test data
DELETE FROM predictions WHERE ticker = 'TEST.NS';
```

## What This Migration Enables

### 1. Backtesting Resolution
The Celery task `resolve_predictions` (runs daily at 6 AM IST) will:
- Find unresolved predictions where `resolved_at IS NULL`
- Fetch actual prices after the horizon period
- Calculate if direction was correct
- Compute MAPE (Mean Absolute Percentage Error)
- Update the prediction record

### 2. Sentiment Caching
The `ticker_sentiment` table stores pre-computed FinBERT scores:
- Updated nightly by `compute_sentiment_all` task
- Reduces API calls during prediction
- Provides historical sentiment tracking

### 3. Model Accuracy Tracking
The `model_accuracy` table aggregates performance:
- Per-ticker, per-horizon accuracy metrics
- Hit rate (% correct direction predictions)
- Average MAPE across predictions
- Refreshed daily by Celery task

## Troubleshooting

### Error: "relation already exists"
**Cause:** Migration was partially applied before
**Solution:** Check which tables/columns exist and manually add missing ones

### Error: "permission denied"
**Cause:** Using anon key instead of service role key
**Solution:** Ensure you're logged into Supabase Dashboard (not using API)

### Error: "syntax error near..."
**Cause:** SQL was not copied completely
**Solution:** Copy the entire file content, including all comments

## Next Steps After Migration

1. **Restart Backend Services** (if running):
   ```bash
   # Stop and restart to pick up new schema
   docker-compose restart backend
   # OR if running manually:
   # Ctrl+C the uvicorn process and restart it
   ```

2. **Verify Celery Tasks**:
   ```bash
   # Check that resolve_predictions task is scheduled
   cd backend
   source .venv/bin/activate
   python -c "from app.tasks.celery_app import celery_app; print(celery_app.conf.beat_schedule)"
   ```

3. **Monitor First Backtest Resolution**:
   - Wait for 6 AM IST or manually trigger:
   ```python
   from app.tasks.backtest_resolver import resolve_predictions
   resolve_predictions.delay()
   ```

4. **Check Model Accuracy Table**:
   ```sql
   SELECT * FROM model_accuracy ORDER BY computed_at DESC LIMIT 10;
   ```

## Migration Rollback (If Needed)

If you need to undo this migration:

```sql
-- Remove new columns from predictions
ALTER TABLE predictions 
  DROP COLUMN IF EXISTS predicted_price,
  DROP COLUMN IF EXISTS current_price_at_pred,
  DROP COLUMN IF EXISTS horizon_days,
  DROP COLUMN IF EXISTS model_version,
  DROP COLUMN IF EXISTS actual_price,
  DROP COLUMN IF EXISTS direction_correct,
  DROP COLUMN IF EXISTS mape,
  DROP COLUMN IF EXISTS resolved_at;

-- Drop new tables
DROP TABLE IF EXISTS ticker_sentiment;
DROP TABLE IF EXISTS model_accuracy;

-- Drop indexes
DROP INDEX IF EXISTS idx_predictions_unresolved;
DROP INDEX IF EXISTS idx_model_accuracy_ticker;
```

**⚠️ Warning:** This will delete all backtesting data and sentiment cache!
