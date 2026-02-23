-- ============================================================
-- CAREER ARCHITECT PRO — Enterprise Database Schema
-- Run sequentially in Supabase SQL Editor
-- ============================================================

-- ── USER ROLES ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_roles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    email       TEXT,
    role        TEXT NOT NULL DEFAULT 'User'
                    CHECK (role IN ('User','Coach','Admin','SystemAdmin')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT  user_roles_user_id_key UNIQUE (user_id)
);

ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "users_read_own_role"     ON user_roles;
DROP POLICY IF EXISTS "elevated_read_all_roles"  ON user_roles;
DROP POLICY IF EXISTS "sysadmin_manage_roles"    ON user_roles;

CREATE POLICY "users_read_own_role" ON user_roles
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "elevated_read_all_roles" ON user_roles
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            WHERE ur.user_id = auth.uid()
              AND ur.role IN ('Coach','Admin','SystemAdmin')
        )
    );

CREATE POLICY "sysadmin_manage_roles" ON user_roles
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            WHERE ur.user_id = auth.uid()
              AND ur.role = 'SystemAdmin'
        )
    );

CREATE POLICY "admins_update_roles" ON user_roles
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            WHERE ur.user_id = auth.uid()
              AND ur.role IN ('Admin','SystemAdmin')
        )
    );

-- Auto-insert User role on new signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    INSERT INTO public.user_roles (user_id, email, role)
    VALUES (NEW.id, NEW.email, 'User')
    ON CONFLICT (user_id) DO UPDATE SET email = EXCLUDED.email;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS user_roles_updated_at ON user_roles;
CREATE TRIGGER user_roles_updated_at
    BEFORE UPDATE ON user_roles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ── FEATURE FLAGS ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS feature_flags (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_name   TEXT NOT NULL UNIQUE,
    enabled     BOOLEAN NOT NULL DEFAULT TRUE,
    min_role    TEXT NOT NULL DEFAULT 'User'
                    CHECK (min_role IN ('User','Coach','Admin','SystemAdmin')),
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE feature_flags ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "authenticated_read_flags"  ON feature_flags;
DROP POLICY IF EXISTS "sysadmin_manage_flags"     ON feature_flags;

CREATE POLICY "authenticated_read_flags" ON feature_flags
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "sysadmin_manage_flags" ON feature_flags
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            WHERE ur.user_id = auth.uid()
              AND ur.role = 'SystemAdmin'
        )
    );

INSERT INTO feature_flags (flag_name, enabled, min_role, description) VALUES
    ('cv_builder',         TRUE, 'User',        'CV Builder module'),
    ('ats_level1',         TRUE, 'User',        'ATS Level 1 keyword scoring'),
    ('ats_level2',         TRUE, 'User',        'ATS Level 2 advanced scoring'),
    ('gap_analysis',       TRUE, 'User',        'Employment gap analysis engine'),
    ('linkedin_generator', TRUE, 'User',        'LinkedIn profile generator'),
    ('reflection',         TRUE, 'User',        'Reflection and journaling'),
    ('cv_export',          TRUE, 'User',        'CV export and encrypted packaging'),
    ('coach_console',      TRUE, 'Coach',       'Coach management console'),
    ('admin_dashboard',    TRUE, 'Admin',       'Admin management console'),
    ('system_config',      TRUE, 'SystemAdmin', 'System configuration console')
ON CONFLICT (flag_name) DO NOTHING;


-- ── USER FEATURE OVERRIDES ────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_feature_overrides (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    flag_name   TEXT NOT NULL,
    enabled     BOOLEAN NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT  user_feature_overrides_user_flag_key UNIQUE (user_id, flag_name)
);

ALTER TABLE user_feature_overrides ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "users_read_own_overrides"   ON user_feature_overrides;
DROP POLICY IF EXISTS "admins_manage_overrides"    ON user_feature_overrides;

CREATE POLICY "users_read_own_overrides" ON user_feature_overrides
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "admins_manage_overrides" ON user_feature_overrides
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            WHERE ur.user_id = auth.uid()
              AND ur.role IN ('Admin','SystemAdmin')
        )
    );


-- ── CVS ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cvs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    encrypted_data  TEXT NOT NULL,
    checksum        TEXT NOT NULL,
    version         INTEGER NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT      cvs_user_id_key UNIQUE (user_id)
);

ALTER TABLE cvs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "users_manage_own_cv"  ON cvs;
DROP POLICY IF EXISTS "elevated_read_cvs"    ON cvs;

CREATE POLICY "users_manage_own_cv" ON cvs
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "elevated_read_cvs" ON cvs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            WHERE ur.user_id = auth.uid()
              AND ur.role IN ('Coach','Admin','SystemAdmin')
        )
    );

DROP TRIGGER IF EXISTS cvs_updated_at ON cvs;
CREATE TRIGGER cvs_updated_at
    BEFORE UPDATE ON cvs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ── REFLECTIONS ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reflections (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    entry_date  DATE NOT NULL DEFAULT CURRENT_DATE,
    mood        TEXT CHECK (mood IN ('Excellent','Good','Neutral','Difficult','Challenging')),
    content     TEXT NOT NULL,
    goals       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE reflections ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "users_manage_own_reflections"  ON reflections;
DROP POLICY IF EXISTS "elevated_read_reflections"     ON reflections;

CREATE POLICY "users_manage_own_reflections" ON reflections
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "elevated_read_reflections" ON reflections
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            WHERE ur.user_id = auth.uid()
              AND ur.role IN ('Coach','Admin','SystemAdmin')
        )
    );


-- ── ATS RESULTS ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ats_results (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    level       INTEGER NOT NULL CHECK (level IN (1, 2)),
    job_title   TEXT,
    score       NUMERIC(5,2) NOT NULL,
    breakdown   JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE ats_results ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "users_manage_own_ats"  ON ats_results;
DROP POLICY IF EXISTS "elevated_read_ats"     ON ats_results;

CREATE POLICY "users_manage_own_ats" ON ats_results
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "elevated_read_ats" ON ats_results
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            WHERE ur.user_id = auth.uid()
              AND ur.role IN ('Coach','Admin','SystemAdmin')
        )
    );


-- ── EXPORT AUDIT LOG ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS export_audit (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    export_type     TEXT NOT NULL,
    file_checksum   TEXT,
    exported_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE export_audit ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "users_own_audit"      ON export_audit;
DROP POLICY IF EXISTS "elevated_read_audit"  ON export_audit;

CREATE POLICY "users_own_audit" ON export_audit
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "elevated_read_audit" ON export_audit
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            WHERE ur.user_id = auth.uid()
              AND ur.role IN ('Admin','SystemAdmin')
        )
    );


-- ── COACH ASSIGNMENTS ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS coach_assignments (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT  coach_assignments_unique UNIQUE (coach_id, user_id)
);

ALTER TABLE coach_assignments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "coaches_read_own_assignments"  ON coach_assignments;
DROP POLICY IF EXISTS "admins_manage_assignments"     ON coach_assignments;

CREATE POLICY "coaches_read_own_assignments" ON coach_assignments
    FOR SELECT USING (auth.uid() = coach_id OR auth.uid() = user_id);

CREATE POLICY "admins_manage_assignments" ON coach_assignments
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            WHERE ur.user_id = auth.uid()
              AND ur.role IN ('Admin','SystemAdmin')
        )
    );
