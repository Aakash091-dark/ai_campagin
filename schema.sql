-- ============================================================================
-- NOTE: RBAC integration added (module/role/permissions) while preserving
-- existing multi-tenant & partitioning design.
-- ============================================================================
-- ============================================================================
-- FastAPI PostgreSQL Multi-Tenant Schema with Partitioning
-- ============================================================================
-- This schema includes:
-- - Multi-tenant architecture with workspace isolation
-- - Partitioned ad insight tables by workspace_id for performance
-- - Proper data types (NUMERIC for metrics, TIMESTAMP for dates)
-- - Foreign key constraints and cascading deletes
-- - Automatic timestamp management
-- ============================================================================


-- ============================================================================
-- DROP EXISTING TABLES (SAFE CLEANUP)
-- ============================================================================
DROP TABLE IF EXISTS permission_cache CASCADE;
DROP TABLE IF EXISTS user_permission_override CASCADE;
DROP TABLE IF EXISTS role_permission CASCADE;
DROP TABLE IF EXISTS role CASCADE;
DROP TABLE IF EXISTS module CASCADE;
DROP TABLE IF EXISTS task_activity_log CASCADE;
DROP TABLE IF EXISTS task_comment CASCADE;
DROP TABLE IF EXISTS task_watcher CASCADE;
DROP TABLE IF EXISTS task_tag_map CASCADE;
DROP TABLE IF EXISTS task CASCADE;
DROP TABLE IF EXISTS task_tag CASCADE;
DROP TABLE IF EXISTS task_category CASCADE;
DROP TABLE IF EXISTS feature_timezone CASCADE;
DROP TABLE IF EXISTS user_goals CASCADE;
DROP TABLE IF EXISTS user_slot_reports CASCADE;
DROP TABLE IF EXISTS reporting_config CASCADE;
DROP TABLE IF EXISTS namecheap_domain CASCADE;
DROP TABLE IF EXISTS namecheap_account CASCADE;
DROP TABLE IF EXISTS report_export_job CASCADE;
DROP TABLE IF EXISTS logs CASCADE;
DROP TABLE IF EXISTS campaign_realtime_history CASCADE;
DROP TABLE IF EXISTS user_relation CASCADE;
DROP TABLE IF EXISTS user_account_assignment CASCADE;
DROP TABLE IF EXISTS tracker CASCADE;
DROP TABLE IF EXISTS user_tab_permission CASCADE;
DROP TABLE IF EXISTS "user" CASCADE;
DROP TABLE IF EXISTS account CASCADE;
DROP TABLE IF EXISTS adlevel_performance CASCADE;
DROP TABLE IF EXISTS adlevel_structure CASCADE;
DROP TABLE IF EXISTS adlevel_tracker CASCADE;
DROP TABLE IF EXISTS adlevel CASCADE;
DROP TABLE IF EXISTS workspace CASCADE;
DROP TABLE IF EXISTS organization CASCADE;

-- Drop data_fetcher schema (and its tables) if it exists
DROP SCHEMA IF EXISTS data_fetcher CASCADE;

-- Drop functions if they exist
DROP FUNCTION IF EXISTS create_workspace_partition(BIGINT) CASCADE;
DROP FUNCTION IF EXISTS verify_partitioning() CASCADE;
DROP FUNCTION IF EXISTS update_updated_column() CASCADE;
DROP FUNCTION IF EXISTS invalidate_permission_cache() CASCADE;
DROP FUNCTION IF EXISTS get_user_permissions(BIGINT, BIGINT) CASCADE;
DROP FUNCTION IF EXISTS check_permission(BIGINT, BIGINT, VARCHAR) CASCADE;


-- ============================================================================
-- ORGANIZATION TABLE
-- ============================================================================
-- Root tenant organization with authentication credentials
CREATE TABLE organization (
    id BIGSERIAL PRIMARY KEY,
    organization_name VARCHAR(255) NOT NULL,
    created_by BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_organization_organization_name ON organization(organization_name);
CREATE INDEX IF NOT EXISTS idx_organization_id ON organization(id);
CREATE INDEX IF NOT EXISTS idx_organization_created_by ON organization(created_by) WHERE created_by IS NOT NULL;


-- ============================================================================
-- CAMPAIGN REALTIME HISTORY TABLE
-- ============================================================================
-- Stores short-term (2 hours) spend/revenue snapshots for live campaigns
-- to compute 30m/1h/2h deltas.
CREATE TABLE IF NOT EXISTS campaign_realtime_history (
    id BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    campaign_id VARCHAR(100) NOT NULL,
    spend NUMERIC(15, 2) DEFAULT 0,
    total_revenue NUMERIC(15, 2) DEFAULT 0,
    leads NUMERIC(15, 4) DEFAULT 0,
    platform_clicks NUMERIC(15, 4) DEFAULT 0,
    impressions NUMERIC(15, 4) DEFAULT 0,
    tracker_purchases NUMERIC(15, 4) DEFAULT 0,
    total_conversion NUMERIC(15, 4) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_campaign_realtime_history_cleanup 
    ON campaign_realtime_history(created_at);
CREATE INDEX IF NOT EXISTS idx_campaign_realtime_history_lookup 
    ON campaign_realtime_history(workspace_id, platform, campaign_id, created_at DESC);


-- ============================================================================
-- WORKSPACE TABLE
-- ============================================================================
-- Workspace (project/team) belongs to an organization
CREATE TABLE workspace (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    default_timezone VARCHAR(20),
    media_buyer_code_wise BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_favorite BOOLEAN DEFAULT FALSE,
    CONSTRAINT unique_workspace_per_org UNIQUE(organization_id, name)
);

CREATE INDEX IF NOT EXISTS idx_workspace_organization_id ON workspace(organization_id);
CREATE INDEX IF NOT EXISTS idx_workspace_name ON workspace(name);
CREATE INDEX IF NOT EXISTS idx_workspace_id ON workspace(id);
CREATE INDEX IF NOT EXISTS idx_workspace_created_by ON workspace(created_by) WHERE created_by IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_workspace_active ON workspace(organization_id, is_active) WHERE is_active = TRUE;
CREATE UNIQUE INDEX IF NOT EXISTS ux_workspace_org_favorite ON workspace(organization_id) WHERE is_favorite = TRUE;


-- ============================================================================
-- ACCOUNT TABLE
-- ============================================================================
-- Third-party advertising accounts (Facebook, TikTok, Google, etc.)
CREATE TABLE IF NOT EXISTS account (
    id BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    account_id VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    client_id VARCHAR(255) NOT NULL,
    client_secret VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    expiry_date TIMESTAMP WITH TIME ZONE,
    active BOOLEAN DEFAULT TRUE,
    timezone VARCHAR(50),
    currency VARCHAR(20),
    profile_name varchar(50),
    profile_id varchar(50),
    manager_id VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    auto_swap_rejected_ads BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT unique_account_per_workspace UNIQUE(workspace_id, account_id)
);

CREATE INDEX IF NOT EXISTS idx_account_workspace_id ON account(workspace_id);
CREATE INDEX IF NOT EXISTS idx_account_account_id ON account(account_id);
CREATE INDEX IF NOT EXISTS idx_account_active ON account(active) WHERE active = TRUE;
CREATE INDEX IF NOT EXISTS idx_account_id ON account(id);
CREATE INDEX IF NOT EXISTS idx_account_platform ON account(platform);
CREATE INDEX IF NOT EXISTS idx_account_workspace_lower_platform ON account(workspace_id, LOWER(platform));


-- =========================================================================
-- TRACKER TABLE
-- =========================================================================
CREATE TABLE tracker (
    id BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    tracker_name VARCHAR(50) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    traffic_channel_id VARCHAR(100),
    traffic_channel_name VARCHAR(255),
    campaign_sub VARCHAR(50),
    adset_sub VARCHAR(50),
    ad_sub VARCHAR(50),
    placement_sub VARCHAR(50),
    media_buyer_code VARCHAR(20),
    timezone VARCHAR(20),
    token TEXT NOT NULL,
    client_id VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_enterprise_level BOOLEAN NOT NULL DEFAULT FALSE,
    created_by BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_tracker_token_per_workspace UNIQUE(workspace_id, platform, token, traffic_channel_id)
);

CREATE INDEX IF NOT EXISTS idx_tracker_workspace_id ON tracker(workspace_id);
CREATE INDEX IF NOT EXISTS idx_tracker_platform ON tracker(platform);
CREATE INDEX IF NOT EXISTS idx_tracker_active ON tracker(workspace_id, is_active) WHERE is_active = TRUE;


-- ============================================================================
-- USER TABLE
-- ============================================================================
-- Team members who belong to a workspace
CREATE TABLE "user" (
    id BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT REFERENCES workspace(id) ON DELETE CASCADE,
    email VARCHAR(100) NOT NULL,
    name VARCHAR(100),
    number VARCHAR(20),
    password VARCHAR(255),
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    media_buyer_code VARCHAR(20),
    created_by BIGINT,
    social_id VARCHAR(255),
    google_id VARCHAR(255),
    profile_pic TEXT,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    camp_template JSONB,
    reporting_tempalat JSONB,
    notes JSONB DEFAULT '[]'::jsonb,   -- user notepad: array of note objects
    telegram_chat_id VARCHAR(50),       -- linked Telegram chat ID for notifications
    telegram_linked_at TIMESTAMP WITH TIME ZONE,  -- when Telegram was linked
    CONSTRAINT unique_user_email_per_workspace UNIQUE(workspace_id, email)
);

CREATE INDEX IF NOT EXISTS idx_user_workspace_id ON "user"(workspace_id);
CREATE INDEX IF NOT EXISTS idx_user_email ON "user"(email);
CREATE INDEX IF NOT EXISTS idx_user_lower_email ON "user"(LOWER(email));
CREATE INDEX IF NOT EXISTS idx_user_google_id ON "user"(google_id) WHERE google_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_user_social_id ON "user"(social_id) WHERE social_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_user_id ON "user"(id);
CREATE INDEX IF NOT EXISTS idx_user_role ON "user"(role);
CREATE INDEX IF NOT EXISTS idx_user_created_by ON "user"(created_by) WHERE created_by IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_user_active ON "user"(workspace_id, is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_telegram_chat_id ON "user"(telegram_chat_id) WHERE telegram_chat_id IS NOT NULL;


-- ============================================================================
-- USER ACCOUNT ASSIGNMENT TABLE
-- ============================================================================
-- Maps users to advertising accounts with time-based assignment
CREATE TABLE user_account_assignment (
    id BIGSERIAL PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    start_at TIMESTAMP WITH TIME ZONE NOT NULL,
    end_at TIMESTAMP WITH TIME ZONE,
    assigned_by BIGINT,
    is_out BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_account_assignment_account_id ON user_account_assignment(account_id);
CREATE INDEX IF NOT EXISTS idx_user_account_assignment_user_id ON user_account_assignment(user_id);
CREATE INDEX IF NOT EXISTS idx_user_account_assignment_active ON user_account_assignment(user_id, account_id) 
    WHERE is_out = FALSE AND end_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_user_account_assignment_id ON user_account_assignment(id);
CREATE INDEX IF NOT EXISTS idx_user_account_assignment_assigned_by ON user_account_assignment(assigned_by) WHERE assigned_by IS NOT NULL;


CREATE TABLE IF NOT EXISTS user_relation (
  id BIGSERIAL PRIMARY KEY,
  workspace_id BIGINT NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
  parent_id BIGINT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,  -- parent
  child_id BIGINT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,  -- child
  created_by BIGINT,    -- who created this assignment (optional)
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enforce single parent for each child -> single-owner semantics
CREATE UNIQUE INDEX IF NOT EXISTS ux_user_relation_child ON user_relation (workspace_id, child_id);

-- Index for quick parent lookups
CREATE INDEX IF NOT EXISTS idx_user_relation_parent ON user_relation (workspace_id, parent_id);
CREATE INDEX IF NOT EXISTS idx_user_relation_child_idx ON user_relation (workspace_id, child_id);
CREATE INDEX IF NOT EXISTS idx_user_relation_created_by ON user_relation (created_by) WHERE created_by IS NOT NULL;

-- Note: Trigger for user_relation will be created after the function is defined


-- =========================================================================
-- USER TAB PERMISSION TABLE - Per-user UI tab overrides
-- =========================================================================
CREATE TABLE user_tab_permission (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    tab_key VARCHAR(50) NOT NULL,
    enabled BOOLEAN NOT NULL,
    editable BOOLEAN NOT NULL,
    created_by BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT ux_user_tab_permission UNIQUE(user_id, tab_key)
);

CREATE INDEX IF NOT EXISTS idx_user_tab_permission_user_id ON user_tab_permission(user_id);
CREATE INDEX IF NOT EXISTS idx_user_tab_permission_tab_key ON user_tab_permission(tab_key);



-- ============================================================================
-- AD INSIGHT PARTITIONED TABLES (Base Tables)
-- ============================================================================
-- Each table is partitioned by workspace_id for performance and isolation

-- Performance / metrics table
CREATE TABLE adlevel_performance (
    id BIGSERIAL,
    workspace_id BIGINT NOT NULL,
    platform VARCHAR(20),
    account_id VARCHAR(20),
    campaign_id VARCHAR(20),
    adset_id VARCHAR(20),
    ad_id VARCHAR(20),
    material_id VARCHAR(100), -- ADDED COLUMN
    account_name VARCHAR(100),
    campaign_name VARCHAR(100),
    adset_name VARCHAR(100),
    ad_name VARCHAR(100),
    alldate VARCHAR(10),
    hour INTEGER,
    cpm NUMERIC(12, 2) DEFAULT 0,
    spend NUMERIC(15, 2) DEFAULT 0,
    impression NUMERIC(12, 0) DEFAULT 0,
    platform_clicks NUMERIC(12, 0) DEFAULT 0,
    user_id BIGINT,
    tl_id BIGINT,
    video_avg_play_time NUMERIC(10, 2) DEFAULT 0,
    video_p25 INTEGER DEFAULT 0,
    video_p50 INTEGER DEFAULT 0,
    video_p75 INTEGER DEFAULT 0,
    video_p95 INTEGER DEFAULT 0,
    video_p100 INTEGER DEFAULT 0,
    video_3s_plays INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (workspace_id, id)
) PARTITION BY LIST (workspace_id);

CREATE INDEX IF NOT EXISTS idx_adlevel_perf_workspace_date
    ON adlevel_performance(workspace_id, alldate);
CREATE INDEX IF NOT EXISTS idx_adlevel_perf_workspace_date_hour
    ON adlevel_performance(workspace_id, alldate, hour);
CREATE INDEX IF NOT EXISTS idx_adlevel_perf_workspace_ad
    ON adlevel_performance(workspace_id, ad_id);
CREATE INDEX IF NOT EXISTS idx_adlevel_perf_workspace_user
    ON adlevel_performance(workspace_id, user_id);
CREATE INDEX IF NOT EXISTS idx_adlevel_perf_workspace_tl
    ON adlevel_performance(workspace_id, tl_id) WHERE tl_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_adlevel_perf_workspace_platform
    ON adlevel_performance(workspace_id, platform);

-- Structure / creative & status table
CREATE TABLE adlevel_structure (
    id BIGSERIAL,
    workspace_id BIGINT NOT NULL,
    platform VARCHAR(20),
    category VARCHAR(20),
    ids VARCHAR(50),
    parent_id TEXT DEFAULT '', -- ADDED COLUMN
    status VARCHAR(20),
    budget NUMERIC(15, 2),
    type VARCHAR(50),
    bid_amount NUMERIC(12, 2),
    bid_strategy VARCHAR(50),
    creation_time VARCHAR(100),
    tag VARCHAR(50),
    media_type VARCHAR(50),
    media_url TEXT,
    thumbnail_url TEXT,
    video_url TEXT,
    headline TEXT,
    description TEXT,
    call_to_action VARCHAR(100),
    -- TikTok Smart+ only: the creative_ad_id (dimensions.ad_id in reporting,
    -- RedTrack sub4) that links this material (ad_material_id) to its tracker row.
    -- Populated by the fetcher via video_id cross-API matching.
    -- Migration: ALTER TABLE adlevel_structure ADD COLUMN sp_creative_id VARCHAR(100) DEFAULT '';
    sp_creative_id VARCHAR(100) DEFAULT '',
    -- TikTok Smart+ only: the adgroup_id (adset ID) that the material belongs to.
    -- Used to correctly place materials in the accounts→campaigns→adsets→ads→materials tree.
    -- Previously stored in the `description` column (repurposed). Now has its own dedicated column.
    -- Migration: ALTER TABLE adlevel_structure ADD COLUMN material_adset_id VARCHAR(50) DEFAULT '';
    material_adset_id VARCHAR(50) DEFAULT '',
    landing_page_url TEXT,
    video_avg_play_time NUMERIC(10, 2) DEFAULT 0,
    video_p25 INTEGER DEFAULT 0,
    video_p50 INTEGER DEFAULT 0,
    video_p75 INTEGER DEFAULT 0,
    video_p95 INTEGER DEFAULT 0,
    video_p100 INTEGER DEFAULT 0,
    video_3s_plays INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (workspace_id, id)
) PARTITION BY LIST (workspace_id);

CREATE INDEX IF NOT EXISTS idx_adlevel_struct_workspace_ids
    ON adlevel_structure(workspace_id, ids);
CREATE INDEX IF NOT EXISTS idx_adlevel_struct_workspace_platform
    ON adlevel_structure(workspace_id, platform);

CREATE UNIQUE INDEX IF NOT EXISTS ux_adlevel_struct_entity
    ON adlevel_structure(workspace_id, platform, category, ids);

-- Tracker / redtrack table
CREATE TABLE adlevel_tracker (
    id BIGSERIAL,
    workspace_id BIGINT NOT NULL,
    platform VARCHAR(20),
    campaign_id VARCHAR(100),
    adset_id VARCHAR(100),
    ad_id VARCHAR(100),
    alldate VARCHAR(10),
    hour INTEGER,
    tracker_clicks NUMERIC(12, 0) DEFAULT 0,
    lp_views NUMERIC(12, 0) DEFAULT 0,
    lp_clicks NUMERIC(12, 0) DEFAULT 0,
    total_revenue NUMERIC(15, 2) DEFAULT 0,
    total_conversion NUMERIC(12, 0) DEFAULT 0,
    purchases NUMERIC(12, 0) DEFAULT 0,
    mb_code VARCHAR(20),
    offer TEXT,
    offer_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (workspace_id, id)
) PARTITION BY LIST (workspace_id);

CREATE INDEX IF NOT EXISTS idx_adlevel_tracker_workspace_date
    ON adlevel_tracker(workspace_id, alldate);
CREATE INDEX IF NOT EXISTS idx_adlevel_tracker_workspace_date_hour
    ON adlevel_tracker(workspace_id, alldate, hour);
CREATE INDEX IF NOT EXISTS idx_adlevel_tracker_workspace_ad
    ON adlevel_tracker(workspace_id, ad_id);
CREATE INDEX IF NOT EXISTS idx_adlevel_tracker_workspace_platform
    ON adlevel_tracker(workspace_id, platform);

-- Composite indexes for common query patterns (CTE slicing)
CREATE INDEX IF NOT EXISTS idx_adlevel_perf_ws_plat_date_hour
    ON adlevel_performance(workspace_id, platform, alldate, hour);
CREATE INDEX IF NOT EXISTS idx_adlevel_tracker_ws_plat_date_hour
    ON adlevel_tracker(workspace_id, platform, alldate, hour);
CREATE INDEX IF NOT EXISTS idx_adlevel_perf_ws_plat_acct
    ON adlevel_performance(workspace_id, platform, account_id);


-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- ============================================================================
-- Function: create_workspace_partition
-- Purpose: Dynamically create a partition for a new workspace
-- Usage: SELECT create_workspace_partition(workspace_id);
-- ============================================================================
CREATE OR REPLACE FUNCTION create_workspace_partition(p_workspace_id BIGINT)
RETURNS TABLE(
    success BOOLEAN,
    message TEXT,
    partition_name TEXT
) AS $$
DECLARE
    v_partition_name TEXT;
    v_partition_exists BOOLEAN;
BEGIN
    -- Performance partitions
    v_partition_name := 'adlevel_performance_w_' || p_workspace_id;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
          AND table_name = v_partition_name
    ) INTO v_partition_exists;

    IF NOT v_partition_exists THEN
        EXECUTE format(
            'CREATE TABLE %I PARTITION OF adlevel_performance FOR VALUES IN (%L)',
            v_partition_name,
            p_workspace_id
        );

        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS idx_%I_workspace_date_hour ON %I(workspace_id, alldate, hour)',
            v_partition_name,
            v_partition_name
        );

        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS idx_%I_ad_id ON %I(ad_id)',
            v_partition_name,
            v_partition_name
        );

        RETURN QUERY SELECT 
            TRUE::BOOLEAN,
            format('Partition %I created successfully for adlevel_performance workspace %s', v_partition_name, p_workspace_id)::TEXT,
            v_partition_name::TEXT;
    ELSE
        RETURN QUERY SELECT 
            FALSE::BOOLEAN,
            format('Partition %I already exists for adlevel_performance workspace %s', v_partition_name, p_workspace_id)::TEXT,
            v_partition_name::TEXT;
    END IF;

    -- Structure partitions
    v_partition_name := 'adlevel_structure_w_' || p_workspace_id;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
          AND table_name = v_partition_name
    ) INTO v_partition_exists;

    IF NOT v_partition_exists THEN
        EXECUTE format(
            'CREATE TABLE %I PARTITION OF adlevel_structure FOR VALUES IN (%L)',
            v_partition_name,
            p_workspace_id
        );

        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS idx_%I_workspace_ids ON %I(workspace_id, ids)',
            v_partition_name,
            v_partition_name
        );

        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS idx_%I_workspace_platform ON %I(workspace_id, platform)',
            v_partition_name,
            v_partition_name
        );

        RETURN QUERY SELECT 
            TRUE::BOOLEAN,
            format('Partition %I created successfully for adlevel_structure workspace %s', v_partition_name, p_workspace_id)::TEXT,
            v_partition_name::TEXT;
    ELSE
        RETURN QUERY SELECT 
            FALSE::BOOLEAN,
            format('Partition %I already exists for adlevel_structure workspace %s', v_partition_name, p_workspace_id)::TEXT,
            v_partition_name::TEXT;
    END IF;

    -- Tracker partitions
    v_partition_name := 'adlevel_tracker_w_' || p_workspace_id;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
          AND table_name = v_partition_name
    ) INTO v_partition_exists;

    IF NOT v_partition_exists THEN
        EXECUTE format(
            'CREATE TABLE %I PARTITION OF adlevel_tracker FOR VALUES IN (%L)',
            v_partition_name,
            p_workspace_id
        );

        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS idx_%I_workspace_date_hour ON %I(workspace_id, alldate, hour)',
            v_partition_name,
            v_partition_name
        );

        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS idx_%I_workspace_ad ON %I(workspace_id, ad_id)',
            v_partition_name,
            v_partition_name
        );

        RETURN QUERY SELECT 
            TRUE::BOOLEAN,
            format('Partition %I created successfully for adlevel_tracker workspace %s', v_partition_name, p_workspace_id)::TEXT,
            v_partition_name::TEXT;
    ELSE
        RETURN QUERY SELECT 
            FALSE::BOOLEAN,
            format('Partition %I already exists for adlevel_tracker workspace %s', v_partition_name, p_workspace_id)::TEXT,
            v_partition_name::TEXT;
    END IF;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- Function: verify_partitioning
-- Purpose: Verify partitioning strategy and row distribution
-- Usage: SELECT * FROM verify_partitioning();
-- ============================================================================
CREATE OR REPLACE FUNCTION verify_partitioning()
RETURNS TABLE(
    parent_rows BIGINT,
    total_partition_rows BIGINT,
    partition_count INTEGER,
    partitions_info TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH parent_count AS (
        SELECT COUNT(*) as rows FROM ONLY adlevel_performance
    ),
    partition_data AS (
        SELECT 
            schemaname,
            tablename,
            COUNT(*) as rows
        FROM pg_tables
        WHERE tablename LIKE 'adlevel_performance_w_%' AND schemaname = 'public'
        GROUP BY schemaname, tablename
    ),
    partition_stats AS (
        SELECT 
            COUNT(*) as partition_count,
            SUM(rows) as total_rows,
            STRING_AGG(tablename || ': ' || rows::TEXT, ', ' ORDER BY tablename) as details
        FROM partition_data
    ),
    all_adlevel_rows AS (
        SELECT COUNT(*) as total_rows FROM adlevel_performance
    )
    SELECT 
        pc.rows::BIGINT,
        aar.total_rows::BIGINT,
        COALESCE(ps.partition_count, 0)::INTEGER,
        COALESCE(ps.details, 'No partitions created')::TEXT
    FROM parent_count pc, all_adlevel_rows aar, partition_stats ps;
END;
$$ LANGUAGE plpgsql;


-- =========================================================================
-- DATA FETCHER SUPPORT TABLES
-- =========================================================================

-- Create dedicated schema for data fetcher components
CREATE SCHEMA IF NOT EXISTS data_fetcher;

-- Table for data fetcher job logs
CREATE TABLE IF NOT EXISTS data_fetcher.job_logs (
    id BIGSERIAL PRIMARY KEY,
    workspace_id INT,
    platform VARCHAR(50),
    status VARCHAR(50),
    records_fetched INT DEFAULT 0,
    error_message TEXT,
    execution_time_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_job_logs_workspace_created
    ON data_fetcher.job_logs(workspace_id, created_at);
CREATE INDEX IF NOT EXISTS idx_job_logs_ws_status_platform_created
    ON data_fetcher.job_logs(workspace_id, status, platform, created_at DESC);

-- Log table for monitoring
CREATE TABLE IF NOT EXISTS data_fetcher.fetch_logs (
    id BIGSERIAL PRIMARY KEY,
    workspace_id INT,
    platform VARCHAR(50),
    status VARCHAR(20),
    records INT DEFAULT 0,
    execution_time_ms INT,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS data_fetcher.backfill_jobs (
    id BIGSERIAL PRIMARY KEY,
    workspace_id INT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_by BIGINT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_backfill_jobs_ws_status_created
    ON data_fetcher.backfill_jobs(workspace_id, status, created_at);


-- ============================================================================
-- Function: update_updated_column
-- Purpose: Automatically update 'updated_at' timestamp on record modification
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP MANAGEMENT
-- ============================================================================

DROP TRIGGER IF EXISTS update_organization_updated ON organization;
CREATE TRIGGER update_organization_updated 
    BEFORE UPDATE ON organization 
    FOR EACH ROW EXECUTE FUNCTION update_updated_column();

DROP TRIGGER IF EXISTS update_workspace_updated ON workspace;
CREATE TRIGGER update_workspace_updated 
    BEFORE UPDATE ON workspace 
    FOR EACH ROW EXECUTE FUNCTION update_updated_column();

DROP TRIGGER IF EXISTS update_account_updated ON account;
CREATE TRIGGER update_account_updated 
    BEFORE UPDATE ON account 
    FOR EACH ROW EXECUTE FUNCTION update_updated_column();

DROP TRIGGER IF EXISTS update_tracker_updated ON tracker;
CREATE TRIGGER update_tracker_updated 
    BEFORE UPDATE ON tracker 
    FOR EACH ROW EXECUTE FUNCTION update_updated_column();

DROP TRIGGER IF EXISTS update_user_updated ON "user";
CREATE TRIGGER update_user_updated 
    BEFORE UPDATE ON "user" 
    FOR EACH ROW EXECUTE FUNCTION update_updated_column();

DROP TRIGGER IF EXISTS update_adlevel_performance_updated ON adlevel_performance;
CREATE TRIGGER update_adlevel_performance_updated 
    BEFORE UPDATE ON adlevel_performance 
    FOR EACH ROW EXECUTE FUNCTION update_updated_column();

DROP TRIGGER IF EXISTS update_adlevel_structure_updated ON adlevel_structure;
CREATE TRIGGER update_adlevel_structure_updated 
    BEFORE UPDATE ON adlevel_structure 
    FOR EACH ROW EXECUTE FUNCTION update_updated_column();

DROP TRIGGER IF EXISTS update_adlevel_tracker_updated ON adlevel_tracker;
CREATE TRIGGER update_adlevel_tracker_updated 
    BEFORE UPDATE ON adlevel_tracker 
    FOR EACH ROW EXECUTE FUNCTION update_updated_column();

DROP TRIGGER IF EXISTS update_user_relation_updated ON user_relation;
CREATE TRIGGER update_user_relation_updated 
    BEFORE UPDATE ON user_relation 
    FOR EACH ROW EXECUTE FUNCTION update_updated_column();


-- ============================================================================
-- LOGS TABLE
-- ============================================================================
-- Stores all types of logs such as API actions, user actions, status changes, errors.
CREATE TABLE IF NOT EXISTS logs (
    id BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT REFERENCES workspace(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES "user"(id) ON DELETE SET NULL,
    category VARCHAR(50) NOT NULL, -- e.g., 'campaign_status', 'auth', 'system'
    action VARCHAR(100) NOT NULL,  -- e.g., 'bulk_update', 'login', 'error'
    status VARCHAR(20) NOT NULL,   -- 'success', 'error'
    details TEXT,                  -- Human readable details or summary
    metadata JSONB,                -- Structured data (e.g., changed fields, full payloads)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_logs_workspace_id ON logs(workspace_id);
CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_category ON logs(category);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_status ON logs(status);

-- ============================================================================
-- REPORT EXPORT JOBS (Excel/CSV queue)
-- ============================================================================
-- Stores per-user, per-workspace export jobs for large historical reports.
CREATE TABLE IF NOT EXISTS report_export_job (
    id BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending|running|completed|failed|downloaded
    is_full BOOLEAN NOT NULL DEFAULT FALSE,
    file_path TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    downloaded_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_report_export_job_ws_user_created
    ON report_export_job(workspace_id, user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_report_export_job_status_created
    ON report_export_job(status, created_at);


-- ============================================================================
-- NAMECHEAP DOMAIN MANAGEMENT SCHEMA
-- ============================================================================
-- Tables for managing Namecheap accounts and domain synchronization
-- ============================================================================

-- ============================================================================
-- NAMECHEAP ACCOUNT TABLE
-- ============================================================================
-- Stores Namecheap account credentials for domain fetching
CREATE TABLE IF NOT EXISTS namecheap_account (
    id BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    username VARCHAR(100) NOT NULL,
    api_user VARCHAR(100) NOT NULL,
    api_key VARCHAR(255) NOT NULL, -- Store encrypted in production
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_synced_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_namecheap_account_per_workspace UNIQUE(workspace_id, username)
);

CREATE INDEX IF NOT EXISTS idx_namecheap_account_workspace_id 
    ON namecheap_account(workspace_id);
CREATE INDEX IF NOT EXISTS idx_namecheap_account_active 
    ON namecheap_account(workspace_id, is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_namecheap_account_username 
    ON namecheap_account(username);

-- ============================================================================
-- NAMECHEAP DOMAIN TABLE
-- ============================================================================
-- Stores domain information synced from Namecheap API
CREATE TABLE IF NOT EXISTS namecheap_domain (
    id BIGSERIAL PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES namecheap_account(id) ON DELETE CASCADE,
    workspace_id BIGINT NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    namecheap_id VARCHAR(50) NOT NULL, -- Domain ID from Namecheap
    name VARCHAR(255) NOT NULL, -- Domain name (e.g., example.com)
    user_field VARCHAR(100), -- User field from Namecheap
    created DATE, -- Domain creation date
    expires DATE, -- Domain expiration date
    is_expired BOOLEAN DEFAULT FALSE,
    is_locked BOOLEAN DEFAULT FALSE,
    auto_renew BOOLEAN DEFAULT FALSE,
    whois_guard VARCHAR(50),
    is_premium BOOLEAN DEFAULT FALSE,
    is_our_dns BOOLEAN DEFAULT FALSE,
    ssl BOOLEAN DEFAULT FALSE, -- SSL certificate status
    ssl_expires_at TIMESTAMP WITH TIME ZONE, -- SSL certificate expiration date (auto-detected)
    tag VARCHAR(100), -- User-defined tag (never auto-updated)
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_namecheap_domain_per_account UNIQUE(account_id, namecheap_id)
);

CREATE INDEX IF NOT EXISTS idx_namecheap_domain_workspace_id 
    ON namecheap_domain(workspace_id);
CREATE INDEX IF NOT EXISTS idx_namecheap_domain_account_id 
    ON namecheap_domain(account_id);
CREATE INDEX IF NOT EXISTS idx_namecheap_domain_name 
    ON namecheap_domain(name);
CREATE INDEX IF NOT EXISTS idx_namecheap_domain_expires 
    ON namecheap_domain(expires);
CREATE INDEX IF NOT EXISTS idx_namecheap_domain_is_expired 
    ON namecheap_domain(is_expired) WHERE is_expired = TRUE;
CREATE INDEX IF NOT EXISTS idx_namecheap_domain_synced_at 
    ON namecheap_domain(synced_at DESC);
CREATE INDEX IF NOT EXISTS idx_namecheap_domain_tag 
    ON namecheap_domain(tag) WHERE tag IS NOT NULL;

-- ============================================================================
-- REPORTING CONFIGURATION TABLE
-- ============================================================================
-- Stores reporting time slots and buffer settings per workspace
CREATE TABLE IF NOT EXISTS reporting_config (
    id BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    slots_config JSONB, -- {"s1": "10:00", "s2": "12:00"}
    buffer_before_min INTEGER DEFAULT 0,
    buffer_after_min INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_reporting_config_per_workspace UNIQUE(workspace_id)
);

CREATE TABLE IF NOT EXISTS user_slot_reports (
    id BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    report_date DATE NOT NULL DEFAULT CURRENT_DATE,
    slot_id VARCHAR(50) NOT NULL,
    metrics_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_user_slot_report UNIQUE(user_id, report_date, slot_id)
);

CREATE INDEX IF NOT EXISTS idx_user_slot_reports_workspace_date 
    ON user_slot_reports(workspace_id, report_date);
CREATE INDEX IF NOT EXISTS idx_user_slot_reports_user_date 
    ON user_slot_reports(user_id, report_date);

-- Trigger for user_slot_reports updated_at
DROP TRIGGER IF EXISTS update_user_slot_reports_modtime ON user_slot_reports;
CREATE TRIGGER update_user_slot_reports_modtime
    BEFORE UPDATE ON user_slot_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_column();

CREATE INDEX IF NOT EXISTS idx_reporting_config_workspace_id 
    ON reporting_config(workspace_id);

DROP TRIGGER IF EXISTS update_reporting_config_updated ON reporting_config;
CREATE TRIGGER update_reporting_config_updated 
    BEFORE UPDATE ON reporting_config 
    FOR EACH ROW EXECUTE FUNCTION update_updated_column();


-- Migration for user_goals table
-- Tracks monthly profit targets per user

CREATE TABLE IF NOT EXISTS user_goals (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    workspace_id BIGINT NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    target_period VARCHAR(7) NOT NULL,  -- 'YYYY-MM' format
    target_profit DECIMAL(15, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_user_target_period UNIQUE(user_id, target_period)
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_user_goals_workspace 
    ON user_goals(workspace_id, target_period);
CREATE INDEX IF NOT EXISTS idx_user_goals_user 
    ON user_goals(user_id, target_period);

-- Trigger for updated_at
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_user_goals_modtime') THEN
        CREATE TRIGGER update_user_goals_modtime
            BEFORE UPDATE ON user_goals
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_column();
    END IF;
END $$;


-- ============================================================================
-- USER MONTHLY METRICS TABLE
-- ============================================================================
-- Stores finalized per-user monthly spend/revenue snapshots.
-- Populated by monthly_metrics_snapshot.py CronJob (3rd of each month).
-- UPSERT-safe: re-running for the same month overwrites existing data.
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_monthly_metrics (
    id             BIGSERIAL PRIMARY KEY,
    workspace_id   BIGINT       NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    user_id        BIGINT       NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    target_month   VARCHAR(7)   NOT NULL,   -- 'YYYY-MM' format (e.g. '2026-04')
    spend          DECIMAL(15, 2) NOT NULL DEFAULT 0,
    revenue        DECIMAL(15, 2) NOT NULL DEFAULT 0,
    created_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- One row per user per month per workspace — UPSERT target
    CONSTRAINT ux_user_monthly_metrics UNIQUE(workspace_id, user_id, target_month)
);

CREATE INDEX IF NOT EXISTS idx_user_monthly_metrics_ws_month
    ON user_monthly_metrics(workspace_id, target_month);
CREATE INDEX IF NOT EXISTS idx_user_monthly_metrics_user
    ON user_monthly_metrics(user_id, target_month);

-- Auto-update trigger
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_user_monthly_metrics_modtime') THEN
        CREATE TRIGGER update_user_monthly_metrics_modtime
            BEFORE UPDATE ON user_monthly_metrics
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_column();
    END IF;
END $$;


-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP MANAGEMENT
-- ============================================================================
DROP TRIGGER IF EXISTS update_namecheap_account_updated ON namecheap_account;
CREATE TRIGGER update_namecheap_account_updated 
    BEFORE UPDATE ON namecheap_account 
    FOR EACH ROW EXECUTE FUNCTION update_updated_column();

DROP TRIGGER IF EXISTS update_namecheap_domain_updated ON namecheap_domain;
CREATE TRIGGER update_namecheap_domain_updated 
    BEFORE UPDATE ON namecheap_domain 
    FOR EACH ROW EXECUTE FUNCTION update_updated_column();


-- ============================================================================
-- FEATURE TIMEZONE TABLE
-- ============================================================================
-- Centralized timezone for Reporting and Task Management features.
-- Separate from workspace.default_timezone which serves a different purpose.
CREATE TABLE IF NOT EXISTS feature_timezone (
    id            BIGSERIAL    PRIMARY KEY,
    workspace_id  BIGINT       NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    timezone      VARCHAR(50)  NOT NULL DEFAULT 'UTC',
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT ux_feature_timezone_ws UNIQUE(workspace_id)
);

CREATE INDEX IF NOT EXISTS idx_feature_timezone_ws
    ON feature_timezone(workspace_id);

DROP TRIGGER IF EXISTS update_feature_timezone_updated ON feature_timezone;
CREATE TRIGGER update_feature_timezone_updated
    BEFORE UPDATE ON feature_timezone
    FOR EACH ROW EXECUTE FUNCTION update_updated_column();


-- ============================================================================
-- TASK MANAGEMENT TABLES
-- ============================================================================

-- 1. Task Category
CREATE TABLE IF NOT EXISTS task_category (
    id          BIGSERIAL    PRIMARY KEY,
    workspace_id BIGINT      NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    created_by  BIGINT       REFERENCES "user"(id) ON DELETE SET NULL,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT ux_task_category_ws_name UNIQUE(workspace_id, name)
);

-- 2. Task Tag
CREATE TABLE IF NOT EXISTS task_tag (
    id          BIGSERIAL    PRIMARY KEY,
    workspace_id BIGINT      NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    created_by  BIGINT       REFERENCES "user"(id) ON DELETE SET NULL,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT ux_task_tag_ws_name UNIQUE(workspace_id, name)
);

-- 3. Task (core)
CREATE TABLE IF NOT EXISTS task (
    id             BIGSERIAL    PRIMARY KEY,
    workspace_id   BIGINT       NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,

    -- Core
    title          VARCHAR(500) NOT NULL,
    description    TEXT,
    remark         TEXT,
    category_id    BIGINT       REFERENCES task_category(id) ON DELETE SET NULL,
    priority       VARCHAR(10)  NOT NULL DEFAULT 'low'
                        CHECK (priority IN ('high', 'medium', 'low')),
    status         VARCHAR(20)  NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled', 'overdue', 'paused', 'resumed')),

    -- Assignment
    assigned_to    BIGINT       NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    created_by     BIGINT       NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,

    -- Due
    due_at         TIMESTAMP WITH TIME ZONE,

    -- Repeat config (template tasks only)
    is_repeat       BOOLEAN     DEFAULT FALSE,
    repeat_type     VARCHAR(10) CHECK (repeat_type IN ('daily', 'weekly', 'monthly')),
    repeat_start_at TIMESTAMP WITH TIME ZONE,
    repeat_time     TIME,
    repeat_due_days INTEGER     CHECK (repeat_due_days >= 1 AND repeat_due_days <= 365),
    repeat_on_days  INTEGER[],  -- Weekly: 1=Mon..7=Sun
    repeat_on_dates INTEGER[],  -- Monthly: 1..31

    -- Parent link for auto-generated child tasks
    repeat_parent_id BIGINT    REFERENCES task(id) ON DELETE SET NULL,

    -- Completion
    completed_at   TIMESTAMP WITH TIME ZONE,
    completed_by   BIGINT      REFERENCES "user"(id) ON DELETE SET NULL,

    created_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance indexes for task
CREATE INDEX IF NOT EXISTS idx_task_ws_status       ON task(workspace_id, status);
CREATE INDEX IF NOT EXISTS idx_task_ws_assigned     ON task(workspace_id, assigned_to);
CREATE INDEX IF NOT EXISTS idx_task_ws_created_by   ON task(workspace_id, created_by);
CREATE INDEX IF NOT EXISTS idx_task_ws_due          ON task(workspace_id, due_at) WHERE due_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_task_ws_priority     ON task(workspace_id, priority);
CREATE INDEX IF NOT EXISTS idx_task_repeat_parent   ON task(repeat_parent_id) WHERE repeat_parent_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_task_repeat_active   ON task(workspace_id, is_repeat, status)
    WHERE is_repeat = TRUE AND status != 'cancelled';
CREATE INDEX IF NOT EXISTS idx_task_ws_created      ON task(workspace_id, created_at DESC);

-- 4. Task-Tag Map (many-to-many)
CREATE TABLE IF NOT EXISTS task_tag_map (
    task_id BIGINT NOT NULL REFERENCES task(id) ON DELETE CASCADE,
    tag_id  BIGINT NOT NULL REFERENCES task_tag(id) ON DELETE CASCADE,
    PRIMARY KEY (task_id, tag_id)
);

-- 5. Task Watcher
CREATE TABLE IF NOT EXISTS task_watcher (
    task_id    BIGINT NOT NULL REFERENCES task(id) ON DELETE CASCADE,
    user_id    BIGINT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (task_id, user_id)
);

-- 6. Task Comment
CREATE TABLE IF NOT EXISTS task_comment (
    id         BIGSERIAL   PRIMARY KEY,
    task_id    BIGINT      NOT NULL REFERENCES task(id) ON DELETE CASCADE,
    user_id    BIGINT      NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    content    TEXT        NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_task_comment_task ON task_comment(task_id, created_at DESC);

-- 7. Task Activity Log
CREATE TABLE IF NOT EXISTS task_activity_log (
    id         BIGSERIAL   PRIMARY KEY,
    task_id    BIGINT      NOT NULL REFERENCES task(id) ON DELETE CASCADE,
    user_id    BIGINT      REFERENCES "user"(id) ON DELETE SET NULL,
    action     VARCHAR(50) NOT NULL,
    old_value  TEXT,
    new_value  TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_task_activity_task ON task_activity_log(task_id, created_at DESC);

-- Triggers for task tables
CREATE OR REPLACE FUNCTION update_task_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_task_updated_at ON task;
CREATE TRIGGER trg_task_updated_at
    BEFORE UPDATE ON task
    FOR EACH ROW
    EXECUTE FUNCTION update_task_updated_at();

DROP TRIGGER IF EXISTS trg_task_comment_updated_at ON task_comment;
CREATE TRIGGER trg_task_comment_updated_at
    BEFORE UPDATE ON task_comment
    FOR EACH ROW
    EXECUTE FUNCTION update_task_updated_at();


-- ═══════════════════════════════════════════════════════════════════════════════
-- Performance indexes for common query patterns
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_uaa_user_acct_dates
    ON user_account_assignment(user_id, account_id, start_at, end_at);

CREATE INDEX IF NOT EXISTS idx_adlevel_perf_acct_date_hour
    ON adlevel_performance(workspace_id, account_id, alldate, hour DESC);

CREATE INDEX IF NOT EXISTS idx_adlevel_tracker_campaign_date
    ON adlevel_tracker(workspace_id, campaign_id, alldate, hour DESC);


-- ============================================================================
-- AUTOMATION ENGINE SCHEMA
-- ============================================================================
-- Isolated schema for automation rules, conditions, and execution audit logs.
-- Automation workers in the 'automation' K8s namespace read/write ONLY here.
-- ============================================================================

DROP SCHEMA IF EXISTS automation CASCADE;
CREATE SCHEMA automation;

-- ── automation_rule ──────────────────────────────────────────────────────────
CREATE TABLE automation.automation_rule (
    id                    BIGSERIAL PRIMARY KEY,
    workspace_id          BIGINT       NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    name                  VARCHAR(255) NOT NULL,

    -- Action (what to do when conditions are met)
    action_type           VARCHAR(50)  NOT NULL,
    -- start|pause|delete|increase_budget|decrease_budget|increase_bid|decrease_bid|notify|smart_alert

    platform              VARCHAR(50)  NOT NULL,  -- facebook|google|tiktok|newsbreak|bigo
    entity_level          VARCHAR(20)  NOT NULL,  -- campaign|adset|ad
    entity_ids            JSONB        NOT NULL DEFAULT '[]',  -- list of platform entity IDs

    -- Scheduling / trigger
    trigger_type          VARCHAR(20)  NOT NULL DEFAULT 'interval',
    -- 'interval'         → repeated every frequency_minutes
    -- 'on_snapshot'      → fires whenever data-fetcher refreshes snapshot for this platform
    -- 'scheduled_daily'  → fires daily at scheduled_time (workspace timezone)
    -- 'scheduled_weekly' → fires weekly on scheduled_day_of_week + scheduled_time
    -- 'one_time'         → fires once at scheduled_at (UTC), then auto-deactivates

    frequency_minutes     INT,                               -- required for 'interval'
    scheduled_time        TIME,                              -- required for daily/weekly (HH:MM in workspace tz)
    scheduled_day_of_week SMALLINT,                         -- 0=Sun..6=Sat, required for weekly
    scheduled_at          TIMESTAMP WITH TIME ZONE,         -- required for one_time (stored in UTC)

    validate_until        TIMESTAMP WITH TIME ZONE,         -- NULL = run forever; auto-deactivates when passed
    timezone              VARCHAR(50)  NOT NULL DEFAULT 'UTC', -- user display timezone (conversion only)

    -- Action parameters (required for budget/bid actions)
    action_value          NUMERIC(15, 4),                   -- amount to change by
    action_value_type     VARCHAR(10)  DEFAULT '$',         -- '$' (fixed) or '%' (percentage)
    max_cap               NUMERIC(15, 4),                   -- safety ceiling, required for budget/bid

    -- Repetition control
    repetitions_max       SMALLINT     NOT NULL DEFAULT 0,  -- 0 = unlimited
    repetitions_done      SMALLINT     NOT NULL DEFAULT 0,

    -- State (Postgres is the source of truth on pod restart)
    is_active             BOOLEAN      NOT NULL DEFAULT TRUE,
    last_run_at           TIMESTAMP WITH TIME ZONE,
    next_run_at           TIMESTAMP WITH TIME ZONE,

    -- Notification channels
    notify_in_app         BOOLEAN      NOT NULL DEFAULT TRUE,
    notify_email          BOOLEAN      NOT NULL DEFAULT FALSE,
    last_email_at         TIMESTAMP WITH TIME ZONE,

    -- Why the rule was deactivated (NULL if still active or manually toggled)
    deactivation_reason   VARCHAR(50),  -- expired|completed|one_time_completed|manual

    -- Tracks how many times the rule has been activated (1 = first run, 2 = re-activated, etc.)
    run_cycle             INT          NOT NULL DEFAULT 1,

    created_by            BIGINT       NOT NULL REFERENCES "user"(id) ON DELETE SET NULL,
    created_at            TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at            TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_automation_rule_ws_active_next
    ON automation.automation_rule(workspace_id, is_active, next_run_at);
CREATE INDEX idx_automation_rule_ws_platform_trigger
    ON automation.automation_rule(workspace_id, platform, trigger_type);
CREATE INDEX idx_automation_rule_ws_active_only
    ON automation.automation_rule(workspace_id)
    WHERE is_active = TRUE;


-- ── automation_rule_condition ─────────────────────────────────────────────────
-- Each condition can be joined with AND or OR to the previous condition.
-- The first condition's conjunction is ignored (it's always the start).
CREATE TABLE automation.automation_rule_condition (
    id          BIGSERIAL PRIMARY KEY,
    rule_id     BIGINT        NOT NULL REFERENCES automation.automation_rule(id) ON DELETE CASCADE,
    metric      VARCHAR(50)   NOT NULL,  -- spend|impressions|clicks|CPM|CPC|...
    operator    VARCHAR(10)   NOT NULL,  -- >|<|>=|<=|=
    value       NUMERIC(18,6) NOT NULL,
    unit        VARCHAR(10)   NOT NULL DEFAULT '$',  -- '$' or '%' (display only)
    conjunction VARCHAR(3)    NOT NULL DEFAULT 'AND', -- 'AND' or 'OR'
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_automation_condition_rule_id ON automation.automation_rule_condition(rule_id);


-- ── automation_rule_execution_log ─────────────────────────────────────────────
-- Immutable audit trail. Written BEFORE calling the platform API.
-- One row per entity per rule evaluation run.
CREATE TABLE automation.automation_rule_execution_log (
    id                BIGSERIAL PRIMARY KEY,
    rule_id           BIGINT      REFERENCES automation.automation_rule(id) ON DELETE SET NULL,
    workspace_id      BIGINT      NOT NULL,
    platform          VARCHAR(50),
    entity_level      VARCHAR(20),
    entity_id         VARCHAR(100),
    entity_name       VARCHAR(255),

    -- Snapshot of raw metrics used for evaluation (aids debugging)
    metrics_snapshot  JSONB,

    -- Evaluation result
    conditions_met    BOOLEAN     NOT NULL,
    conditions_detail JSONB,  -- per-condition pass/fail breakdown

    -- What action was taken (only present when conditions_met = TRUE)
    action_type       VARCHAR(50),
    action_payload    JSONB,   -- payload sent to platform API
    action_success    BOOLEAN,
    action_error      TEXT,

    email_sent        BOOLEAN     NOT NULL DEFAULT FALSE,
    triggered_by      VARCHAR(20) NOT NULL DEFAULT 'timer',  -- 'timer'|'snapshot'|'catchup'
    run_cycle         INT         NOT NULL DEFAULT 1,         -- which activation round this log belongs to
    evaluated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_automation_log_rule_time
    ON automation.automation_rule_execution_log(rule_id, evaluated_at DESC);
CREATE INDEX idx_automation_log_ws_time
    ON automation.automation_rule_execution_log(workspace_id, evaluated_at DESC);
CREATE INDEX idx_automation_log_rule_entity_time
    ON automation.automation_rule_execution_log(rule_id, entity_id, evaluated_at DESC);


-- ── updated_at trigger ────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION automation.trg_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_automation_rule_updated_at ON automation.automation_rule;
CREATE TRIGGER trg_automation_rule_updated_at
    BEFORE UPDATE ON automation.automation_rule
    FOR EACH ROW EXECUTE FUNCTION automation.trg_set_updated_at();


-- ============================================================================
-- SMART ALERT SCHEMA
-- ============================================================================
-- Separate from the Automation Engine. Smart Alerts are event-driven,
-- notification-only rules that fire on every data_updated snapshot.
-- ============================================================================

DROP SCHEMA IF EXISTS smart_alert CASCADE;
CREATE SCHEMA smart_alert;

-- ── smart_alert.rule ────────────────────────────────────────────────────────
CREATE TABLE smart_alert.rule (
    id                    BIGSERIAL PRIMARY KEY,
    workspace_id          BIGINT       NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    name                  VARCHAR(255) NOT NULL,

    -- Targeting Layer 1: Scope
    scope                 VARCHAR(20)  NOT NULL DEFAULT 'campaign',

    -- Targeting Layer 2: Platform
    target                VARCHAR(20)  NOT NULL DEFAULT 'all',
    platform_tags         TEXT[]       NOT NULL DEFAULT '{}',

    -- Targeting Layer 3: Entity scope
    entity_target         VARCHAR(20),
    entity_ids            JSONB        NOT NULL DEFAULT '[]',
    entity_names          JSONB        NOT NULL DEFAULT '[]',

    -- Notification channels
    notify_in_app         BOOLEAN      NOT NULL DEFAULT TRUE,
    notify_email          BOOLEAN      NOT NULL DEFAULT FALSE,

    -- Timezone (IANA)
    timezone              VARCHAR(50)  NOT NULL DEFAULT 'America/New_York',

    -- State
    is_active             BOOLEAN      NOT NULL DEFAULT TRUE,
    last_run_at           TIMESTAMP WITH TIME ZONE,

    -- Run counters
    total_runs            INT          NOT NULL DEFAULT 0,
    total_runs_matched    INT          NOT NULL DEFAULT 0,

    -- Creator
    created_by            BIGINT       NOT NULL REFERENCES "user"(id) ON DELETE SET NULL,
    created_at            TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at            TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sa_rule_ws_active
    ON smart_alert.rule(workspace_id) WHERE is_active = TRUE;
CREATE INDEX idx_sa_rule_ws_all
    ON smart_alert.rule(workspace_id, created_at DESC);


-- ── smart_alert.condition ───────────────────────────────────────────────────
CREATE TABLE smart_alert.condition (
    id          BIGSERIAL PRIMARY KEY,
    rule_id     BIGINT        NOT NULL REFERENCES smart_alert.rule(id) ON DELETE CASCADE,
    metric      VARCHAR(50)   NOT NULL,
    condition   VARCHAR(30)   NOT NULL,
    value       NUMERIC(18,6) NOT NULL,
    unit        VARCHAR(10),
    period      TEXT,
    conjunction VARCHAR(3)    NOT NULL DEFAULT 'AND',
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sa_cond_rule
    ON smart_alert.condition(rule_id);


-- ── smart_alert.evaluation_run ──────────────────────────────────────────────
-- Only written when total_matched > 0 (lean logging).
CREATE TABLE smart_alert.evaluation_run (
    id               BIGSERIAL PRIMARY KEY,
    rule_id          BIGINT       REFERENCES smart_alert.rule(id) ON DELETE SET NULL,
    workspace_id     BIGINT       NOT NULL,
    platform         VARCHAR(50),
    total_evaluated  INT          NOT NULL DEFAULT 0,
    total_matched    INT          NOT NULL DEFAULT 0,
    triggered_by     VARCHAR(20)  NOT NULL DEFAULT 'snapshot',
    evaluated_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sa_run_rule_time
    ON smart_alert.evaluation_run(rule_id, evaluated_at DESC);
CREATE INDEX idx_sa_run_ws_time
    ON smart_alert.evaluation_run(workspace_id, evaluated_at DESC);


-- ── smart_alert.triggered_entity ────────────────────────────────────────────
-- Only entities where conditions were met (sparse).
CREATE TABLE smart_alert.triggered_entity (
    id                 BIGSERIAL PRIMARY KEY,
    run_id             BIGINT       NOT NULL REFERENCES smart_alert.evaluation_run(id) ON DELETE CASCADE,
    entity_id          VARCHAR(100) NOT NULL,
    entity_name        VARCHAR(255),
    scope              VARCHAR(20),
    metrics_snapshot   JSONB,
    notified_user_id   BIGINT,
    notification_sent  BOOLEAN      NOT NULL DEFAULT FALSE,
    notification_error TEXT,
    created_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sa_triggered_run
    ON smart_alert.triggered_entity(run_id);
CREATE INDEX idx_sa_triggered_entity
    ON smart_alert.triggered_entity(entity_id);


-- ── smart_alert updated_at trigger ──────────────────────────────────────────
CREATE OR REPLACE FUNCTION smart_alert.trg_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sa_rule_updated_at ON smart_alert.rule;
CREATE TRIGGER trg_sa_rule_updated_at
    BEFORE UPDATE ON smart_alert.rule
    FOR EACH ROW EXECUTE FUNCTION smart_alert.trg_set_updated_at();


-- ============================================================================
-- CAMPAIGN LAUNCHER SCHEMA
-- ============================================================================
-- Isolated schema for campaign launcher: campaign/adset/ad creation,
-- launch jobs, execution logs, and reusable templates.
-- ============================================================================

DROP SCHEMA IF EXISTS camp_launcher CASCADE;
CREATE SCHEMA IF NOT EXISTS camp_launcher;

-- ── cl_campaigns ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS camp_launcher.cl_campaigns (
    id               TEXT PRIMARY KEY,           -- local UUID (before Meta responds)
    meta_id          TEXT,                        -- real Facebook campaign ID
    workspace_id     BIGINT NOT NULL,
    user_id          BIGINT NOT NULL,
    account_id       TEXT NOT NULL,
    name             TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'PAUSED',
    creation_status  TEXT NOT NULL DEFAULT 'pending', -- pending | done | error
    error_detail     TEXT,
    payload          JSONB NOT NULL DEFAULT '{}',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cl_campaigns_workspace ON camp_launcher.cl_campaigns(workspace_id);
CREATE INDEX IF NOT EXISTS idx_cl_campaigns_user ON camp_launcher.cl_campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_cl_campaigns_account ON camp_launcher.cl_campaigns(account_id);
CREATE INDEX IF NOT EXISTS idx_cl_campaigns_meta ON camp_launcher.cl_campaigns(meta_id) WHERE meta_id IS NOT NULL;

-- ── cl_adsets ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS camp_launcher.cl_adsets (
    id                TEXT PRIMARY KEY,
    meta_id           TEXT,
    workspace_id      BIGINT NOT NULL,
    user_id           BIGINT NOT NULL,
    account_id        TEXT NOT NULL,
    local_campaign_id TEXT NOT NULL,
    meta_campaign_id  TEXT,
    name              TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'PAUSED',
    creation_status   TEXT NOT NULL DEFAULT 'pending',
    error_detail      TEXT,
    payload           JSONB NOT NULL DEFAULT '{}',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cl_adsets_workspace ON camp_launcher.cl_adsets(workspace_id);
CREATE INDEX IF NOT EXISTS idx_cl_adsets_campaign ON camp_launcher.cl_adsets(local_campaign_id);
CREATE INDEX IF NOT EXISTS idx_cl_adsets_meta_campaign ON camp_launcher.cl_adsets(meta_campaign_id) WHERE meta_campaign_id IS NOT NULL;

-- ── cl_ads ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS camp_launcher.cl_ads (
    id                TEXT PRIMARY KEY,
    meta_id           TEXT,
    workspace_id      BIGINT NOT NULL,
    user_id           BIGINT NOT NULL,
    account_id        TEXT NOT NULL,
    local_adset_id    TEXT NOT NULL,
    meta_adset_id     TEXT,
    local_campaign_id TEXT NOT NULL,
    meta_campaign_id  TEXT,
    name              TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'PAUSED',
    creation_status   TEXT NOT NULL DEFAULT 'pending',
    error_detail      TEXT,
    payload           JSONB NOT NULL DEFAULT '{}',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cl_ads_workspace ON camp_launcher.cl_ads(workspace_id);
CREATE INDEX IF NOT EXISTS idx_cl_ads_adset ON camp_launcher.cl_ads(local_adset_id);
CREATE INDEX IF NOT EXISTS idx_cl_ads_meta_adset ON camp_launcher.cl_ads(meta_adset_id) WHERE meta_adset_id IS NOT NULL;

-- ── cl_launches ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS camp_launcher.cl_launches (
    id                BIGSERIAL PRIMARY KEY,
    job_id            TEXT,                        -- links to parent cl_launch_jobs batch
    launched_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    workspace_id      BIGINT NOT NULL,
    user_id           BIGINT NOT NULL,
    account_id        TEXT NOT NULL,
    local_campaign_id TEXT,
    local_adset_id    TEXT,
    local_ad_id       TEXT,
    meta_campaign_id  TEXT,
    meta_adset_id     TEXT,
    meta_ad_id        TEXT,
    campaign_name     TEXT,
    adset_name        TEXT,
    ad_name           TEXT,
    status            TEXT NOT NULL DEFAULT 'pending', -- pending | done | error
    error_detail      TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cl_launches_workspace ON camp_launcher.cl_launches(workspace_id);
CREATE INDEX IF NOT EXISTS idx_cl_launches_user ON camp_launcher.cl_launches(user_id);
CREATE INDEX IF NOT EXISTS idx_cl_launches_account ON camp_launcher.cl_launches(account_id);
CREATE INDEX IF NOT EXISTS idx_cl_launches_status ON camp_launcher.cl_launches(status);
CREATE INDEX IF NOT EXISTS idx_cl_launches_job ON camp_launcher.cl_launches(job_id) WHERE job_id IS NOT NULL;

-- ── cl_launch_jobs ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS camp_launcher.cl_launch_jobs (
    id           TEXT PRIMARY KEY,            -- uuid hex
    workspace_id BIGINT NOT NULL,
    user_id      BIGINT NOT NULL,
    account_id   TEXT NOT NULL,
    account_name TEXT,
    status       TEXT NOT NULL DEFAULT 'queued', -- queued | running | done | error | partial
    total        INTEGER NOT NULL DEFAULT 0,
    completed    INTEGER NOT NULL DEFAULT 0,
    failed_count INTEGER NOT NULL DEFAULT 0,
    campaigns    JSONB NOT NULL DEFAULT '[]',
    results      JSONB NOT NULL DEFAULT '[]',
    errors       JSONB NOT NULL DEFAULT '[]',
    error_detail TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cl_launch_jobs_workspace ON camp_launcher.cl_launch_jobs(workspace_id);
CREATE INDEX IF NOT EXISTS idx_cl_launch_jobs_user ON camp_launcher.cl_launch_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_cl_launch_jobs_status ON camp_launcher.cl_launch_jobs(status);

-- ── cl_logs ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS camp_launcher.cl_logs (
    id           BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT NOT NULL,
    user_id      BIGINT,
    timestamp    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    level        TEXT NOT NULL DEFAULT 'info', -- info | warning | error
    message      TEXT NOT NULL,
    detail       JSONB,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cl_logs_workspace ON camp_launcher.cl_logs(workspace_id);
CREATE INDEX IF NOT EXISTS idx_cl_logs_level ON camp_launcher.cl_logs(workspace_id, level);
CREATE INDEX IF NOT EXISTS idx_cl_logs_created ON camp_launcher.cl_logs(created_at DESC);

-- ── cl_templates ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS camp_launcher.cl_templates (
    id           BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT NOT NULL,
    user_id      BIGINT NOT NULL,
    template_name TEXT NOT NULL,
    description  TEXT,
    data         JSONB NOT NULL DEFAULT '{}',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cl_templates_workspace ON camp_launcher.cl_templates(workspace_id);
CREATE INDEX IF NOT EXISTS idx_cl_templates_user ON camp_launcher.cl_templates(user_id);


-- ============================================================================
-- DOMAIN-USER ASSIGNMENT TABLE (many-to-many)
-- ============================================================================
-- Maps domains to users.  A single domain can be assigned to multiple users
-- and a single user can have multiple domains.
CREATE TABLE IF NOT EXISTS domain_user_assignment (
    id          BIGSERIAL PRIMARY KEY,
    domain_id   BIGINT NOT NULL REFERENCES namecheap_domain(id) ON DELETE CASCADE,
    user_id     BIGINT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    workspace_id BIGINT NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    assigned_by BIGINT REFERENCES "user"(id) ON DELETE SET NULL,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT ux_domain_user UNIQUE(domain_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_domain_user_assignment_domain
    ON domain_user_assignment(domain_id);
CREATE INDEX IF NOT EXISTS idx_domain_user_assignment_user
    ON domain_user_assignment(user_id);
CREATE INDEX IF NOT EXISTS idx_domain_user_assignment_workspace
    ON domain_user_assignment(workspace_id);


-- ============================================================================
-- DOMAIN BUY REQUEST TABLE
-- ============================================================================
-- Tracks domain purchase requests from workspace members.
-- Admins review and update status: pending → bought | rejected.
CREATE TABLE IF NOT EXISTS domain_buy_request (
    id            BIGSERIAL PRIMARY KEY,
    workspace_id  BIGINT NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    user_id       BIGINT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    domain_name   VARCHAR(255) NOT NULL,
    remark        TEXT,
    status        VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending | bought | rejected
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_domain_buy_request_workspace
    ON domain_buy_request(workspace_id);
CREATE INDEX IF NOT EXISTS idx_domain_buy_request_user
    ON domain_buy_request(user_id);
CREATE INDEX IF NOT EXISTS idx_domain_buy_request_status
    ON domain_buy_request(status);

DROP TRIGGER IF EXISTS update_domain_buy_request_updated ON domain_buy_request;
CREATE TRIGGER update_domain_buy_request_updated
    BEFORE UPDATE ON domain_buy_request
    FOR EACH ROW EXECUTE FUNCTION update_updated_column();


-- =========================================================================
-- AUTO-SWAP REJECTED ADS
-- =========================================================================

-- Per-account toggle: when TRUE the auto-swap worker will replace creatives
-- on rejected ads belonging to this account.
ALTER TABLE account
    ADD COLUMN IF NOT EXISTS auto_swap_rejected_ads BOOLEAN NOT NULL DEFAULT FALSE;

-- Tracks every auto-swap attempt so we can enforce a MAX_ATTEMPTS cap (default 5)
-- and provide an audit trail for debugging.
CREATE TABLE IF NOT EXISTS ad_auto_swap_log (
    id              BIGSERIAL PRIMARY KEY,
    workspace_id    BIGINT NOT NULL,
    account_id      VARCHAR(50) NOT NULL,
    ad_id           VARCHAR(50) NOT NULL,
    attempt_number  INT NOT NULL DEFAULT 1,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending | success | failed
    old_creative_id VARCHAR(50),
    new_creative_id VARCHAR(50),
    image_hash      VARCHAR(100),
    error_message   TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Fast lookup: "how many times have we tried to swap this ad?"
CREATE INDEX IF NOT EXISTS idx_ad_auto_swap_log_ad_id
    ON ad_auto_swap_log(ad_id);

-- Workspace-scoped listing for dashboards
CREATE INDEX IF NOT EXISTS idx_ad_auto_swap_log_workspace
    ON ad_auto_swap_log(workspace_id, created_at DESC);

-- Efficient count check per ad
CREATE INDEX IF NOT EXISTS idx_ad_auto_swap_log_ad_status
    ON ad_auto_swap_log(ad_id, status);

-- Date-based lookups for the auto-delete worker (yesterday's failed ads)
CREATE INDEX IF NOT EXISTS idx_ad_auto_swap_log_created_date
    ON ad_auto_swap_log(created_at, status);


-- =========================================================================
-- AUTO-DELETE REJECTED ADS (after failed swap attempts)
-- =========================================================================

-- Per-account toggle: when TRUE the auto-delete worker will DELETE ads from
-- Facebook if they had >= 2 failed swap attempts on the previous day.
ALTER TABLE account
    ADD COLUMN IF NOT EXISTS delete_auto_swap_rejected_ads BOOLEAN NOT NULL DEFAULT FALSE;

-- Tracks every auto-delete action for audit trail
CREATE TABLE IF NOT EXISTS ad_auto_delete_log (
    id              BIGSERIAL PRIMARY KEY,
    workspace_id    BIGINT NOT NULL,
    account_id      VARCHAR(50) NOT NULL,
    ad_id           VARCHAR(50) NOT NULL,
    swap_attempts   INT NOT NULL DEFAULT 0,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',  -- success | failed
    error_message   TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ad_auto_delete_log_workspace
    ON ad_auto_delete_log(workspace_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ad_auto_delete_log_ad_id
    ON ad_auto_delete_log(ad_id);
    
-- ════════════════════════════════════════════════════════════════════════════════
-- AI Semantic Memory — pgvector Embeddings
-- ════════════════════════════════════════════════════════════════════════════════

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS ai_memory_embedding (
    id              BIGSERIAL PRIMARY KEY,
    workspace_id    BIGINT NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    user_id         BIGINT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    content         TEXT NOT NULL,
    summary         TEXT,
    category        VARCHAR(30) DEFAULT 'insight',
    embedding       vector(384) NOT NULL,
    conversation_id VARCHAR(64),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_memory_embedding_vector
    ON ai_memory_embedding USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_ai_memory_embedding_ws_user
    ON ai_memory_embedding (workspace_id, user_id);

CREATE INDEX IF NOT EXISTS idx_ai_memory_embedding_category
    ON ai_memory_embedding (workspace_id, category);

-- ════════════════════════════════════════════════════════════════════════════════
-- AI Chat History (permanent, replaces Redis-based chat storage)
-- ════════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS ai_conversation (
    id              VARCHAR(64) PRIMARY KEY,
    workspace_id    BIGINT NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    user_id         BIGINT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    title           TEXT DEFAULT '',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_conversation_user
    ON ai_conversation(workspace_id, user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS ai_message (
    id              BIGSERIAL PRIMARY KEY,
    conversation_id VARCHAR(64) NOT NULL REFERENCES ai_conversation(id) ON DELETE CASCADE,
    workspace_id    BIGINT NOT NULL,
    user_id         BIGINT NOT NULL,
    role            VARCHAR(10) NOT NULL,
    content         TEXT NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(conversation_id, role, created_at)
);

CREATE INDEX IF NOT EXISTS idx_ai_message_conv
    ON ai_message(conversation_id, created_at);

-- ════════════════════════════════════════════════════════════════════════════════
-- AI Custom System Prompts
-- ════════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS ai_prompts (
    id              SERIAL PRIMARY KEY,
    workspace_id    INTEGER NOT NULL,
    user_id         INTEGER NOT NULL,
    name            TEXT NOT NULL,
    content         TEXT NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_prompts_user
    ON ai_prompts(workspace_id, user_id);
