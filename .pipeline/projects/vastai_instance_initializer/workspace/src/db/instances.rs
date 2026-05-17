use super::models::*;
use super::AppState;
use rusqlite::params;
use tauri::State;

pub fn insert_instance_status(state: &State<AppState>, status: InstanceStatus) -> Result<InstanceStatus, String> {
    let conn = state.conn.lock().map_err(|e| e.to_string())?;
    conn.execute(
        "INSERT INTO instance_statuses (execution_id, instance_id, status, gpu_type, price_per_hour, details, created_at, updated_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
        params![
            status.execution_id,
            status.instance_id,
            status.status,
            status.gpu_type,
            status.price_per_hour,
            status.details,
            status.created_at,
            status.updated_at,
        ],
    )
    .map_err(|e| format!("Failed to insert instance status: {}", e))?;
    Ok(status)
}

pub fn update_instance_status(state: &State<AppState>, execution_id: &str, instance_id: &str, status: &str) -> Result<(), String> {
    let conn = state.conn.lock().map_err(|e| e.to_string())?;
    let now = chrono::Utc::now().to_rfc3339();
    conn.execute(
        "UPDATE instance_statuses SET status = ?3, updated_at = ?4 WHERE execution_id = ?1 AND instance_id = ?2",
        params![execution_id, instance_id, status, now],
    )
    .map_err(|e| format!("Failed to update instance status: {}", e))?;
    Ok(())
}

pub fn get_instance_statuses(state: &State<AppState>, execution_id: &str) -> Result<Vec<InstanceStatus>, String> {
    let conn = state.conn.lock().map_err(|e| e.to_string())?;

    let mut stmt = conn.prepare(
        "SELECT execution_id, instance_id, status, gpu_type, price_per_hour, details, created_at, updated_at FROM instance_statuses WHERE execution_id = ?1 ORDER BY created_at ASC"
    ).map_err(|e| format!("Failed to prepare query: {}", e))?;

    let iter = stmt.query_map(params![execution_id], |row| {
        Ok(InstanceStatus {
            execution_id: row.get(0)?,
            instance_id: row.get(1)?,
            status: row.get(2)?,
            gpu_type: row.get(3)?,
            price_per_hour: row.get(4)?,
            details: row.get(5)?,
            created_at: row.get(6)?,
            updated_at: row.get(7)?,
        })
    }).map_err(|e| format!("Failed to query instance statuses: {}", e))?;

    let mut statuses: Vec<InstanceStatus> = Vec::new();
    for status_result in iter {
        match status_result {
            Ok(s) => statuses.push(s),
            Err(e) => eprintln!("Error reading instance status: {}", e),
        }
    }

    Ok(statuses)
}
