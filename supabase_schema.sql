-- ==============================================================================
-- SUPABASE SCHEMA: ZERO TOPIC REPETITION & 4-SLOT CONTENT ENGINE
-- ==============================================================================

-- 1. Table for tracking all published video reels & loop reels
CREATE TABLE IF NOT EXISTS used_islamic_video (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source TEXT NOT NULL, -- e.g. 'loop_slot_1_fajr', 'loop_slot_2_midday', 'video_daily_life'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Create unique index on normalized title to prevent identical topic repeats
CREATE UNIQUE INDEX IF NOT EXISTS idx_used_islamic_video_title ON used_islamic_video(title);

-- 3. Table for Facebook Photo Reflection Cards (if used)
CREATE TABLE IF NOT EXISTS facebook_posts (
    id SERIAL PRIMARY KEY,
    category TEXT,
    title TEXT,
    quote TEXT,
    reference TEXT,
    caption TEXT,
    image_path TEXT,
    status TEXT DEFAULT 'POSTED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable Row Level Security (RLS) & allow anon read/insert
ALTER TABLE used_islamic_video ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow anonymous read" ON used_islamic_video FOR SELECT USING (true);
CREATE POLICY "Allow anonymous insert" ON used_islamic_video FOR INSERT WITH CHECK (true);
