-- Operational tables (schema_migrations created by migrate.py)

CREATE TABLE IF NOT EXISTS job_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_name TEXT NOT NULL,
    ref_date TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('SUCCESS', 'FAILED', 'RUNNING', 'ERROR')),
    rows_processed INTEGER,
    error_message TEXT,
    UNIQUE (pipeline_name, ref_date)
);

CREATE INDEX IF NOT EXISTS idx_job_runs_pipeline_date ON job_runs (pipeline_name, ref_date);
CREATE INDEX IF NOT EXISTS idx_job_runs_status ON job_runs (status);
