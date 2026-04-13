-- Run this in your Supabase SQL Editor

-- 1. Predictions Tracking Table
CREATE TABLE predictions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  symbol TEXT NOT NULL,
  predicted_price FLOAT NOT NULL,
  predicted_direction TEXT NOT NULL, -- 'UP' or 'DOWN'
  actual_price FLOAT,
  actual_direction TEXT,
  result TEXT, -- 'WIN', 'LOSS', 'PENDING'
  timeframe TEXT NOT NULL, -- '5m', '15m', '1h', '1d'
  created_at TIMESTAMPTZ DEFAULT now(),
  check_at TIMESTAMPTZ NOT NULL
);

-- Note: Enable Row Level Security (RLS) if you want users to only see their own predictions
-- ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Users can insert their own predictions." ON predictions FOR INSERT WITH CHECK (auth.uid() = user_id);
-- CREATE POLICY "Users can view their own predictions." ON predictions FOR SELECT USING (auth.uid() = user_id);

-- 2. Search History Table
CREATE TABLE search_history (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  symbol TEXT NOT NULL,
  analysis_type TEXT NOT NULL,
  result_summary JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ALTER TABLE search_history ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Users can insert their own history." ON search_history FOR INSERT WITH CHECK (auth.uid() = user_id);
-- CREATE POLICY "Users can view their own history." ON search_history FOR SELECT USING (auth.uid() = user_id);
