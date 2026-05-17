use rusqlite::Connection;

pub fn create_tables(conn: &Connection) -> rusqlite::Result<()> {
    conn.execute_batch(
        "
        CREATE TABLE IF NOT EXISTS presets (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS preset_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            preset_id TEXT NOT NULL,
            gpu_type TEXT DEFAULT '',
            max_price REAL DEFAULT 0.0,
            instance_count INTEGER DEFAULT 1,
            inter_instance_delay_seconds INTEGER DEFAULT 0,
            commands TEXT NOT NULL,
            FOREIGN KEY (preset_id) REFERENCES presets(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS executions (
            id TEXT PRIMARY KEY,
            preset_id TEXT NOT NULL,
            preset_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            instance_id TEXT DEFAULT '',
            error_message TEXT DEFAULT '',
            started_at TEXT NOT NULL,
            completed_at TEXT,
            FOREIGN KEY (preset_id) REFERENCES presets(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS instance_statuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            instance_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            gpu_type TEXT DEFAULT '',
            price_per_hour REAL DEFAULT 0.0,
            details TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_executions_preset ON executions(preset_id);
        CREATE INDEX IF NOT EXISTS idx_executions_status ON executions(status);
        CREATE INDEX IF NOT EXISTS idx_instance_statuses_execution ON instance_statuses(execution_id);
        "
    )?;
    Ok(())
}
