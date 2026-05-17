use super::models::*;
use super::AppState;
use rusqlite::params;
use tauri::State;

pub fn insert_execution(state: &State<AppState>, execution: Execution) -> Result<Execution, String> {
    let conn = state.conn.lock().map_err(|e| e.to_string())?;
    conn.execute(
        "INSERT INTO executions (id, preset_id, preset_name, status, instance_id, error_message, started_at, completed_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
        params![
            execution.id,
            execution.preset_id,
            execution.preset_name,
            execution.status,
            execution.instance_id,
            execution.error_message,
            execution.started_at,
            execution.completed_at,
        ],
    )
    .map_err(|e| format!("Failed to insert execution: {}", e))?;
    Ok(execution)
}

pub fn update_execution_status(state: &State<AppState>, execution_id: &str, status: &str, error_message: Option<&str>) -> Result<(), String> {
    let conn = state.conn.lock().map_err(|e| e.to_string())?;
    let now = chrono::Utc::now().to_rfc3339();
    if status == "completed" || status == "failed" {
        conn.execute(
            "UPDATE executions SET status = ?2, error_message = ?3, completed_at = ?4 WHERE id = ?1",
            params![execution_id, status, error_message.unwrap_or(""), now],
        )
        .map_err(|e| format!("Failed to update execution status: {}", e))?;
    } else {
        conn.execute(
            "UPDATE executions SET status = ?2, error_message = ?3 WHERE id = ?1",
            params![execution_id, status, error_message.unwrap_or("")],
        )
        .map_err(|e| format!("Failed to update execution status: {}", e))?;
    }
    Ok(())
}

pub fn get_execution_history(state: &State<AppState>) -> Result<Vec<Execution>, String> {
    let conn = state.conn.lock().map_err(|e| e.to_string())?;

    let mut stmt = conn.prepare(
        "SELECT id, preset_id, preset_name, status, instance_id, error_message, started_at, completed_at FROM executions ORDER BY started_at DESC"
    ).map_err(|e| format!("Failed to prepare query: {}", e))?;

    let exec_iter = stmt.query_map([], |row| {
        Ok(Execution {
            id: row.get(0)?,
            preset_id: row.get(1)?,
            preset_name: row.get(2)?,
            status: row.get(3)?,
            instance_id: row.get(4)?,
            error_message: row.get(5)?,
            started_at: row.get(6)?,
            completed_at: row.get(7)?,
        })
    }).map_err(|e| format!("Failed to query executions: {}", e))?;

    let mut executions: Vec<Execution> = Vec::new();
    for exec_result in exec_iter {
        match exec_result {
            Ok(exec) => executions.push(exec),
            Err(e) => eprintln!("Error reading execution: {}", e),
        }
    }

    Ok(executions)
}

pub fn get_execution_by_id(state: &State<AppState>, id: &str) -> Result<Option<Execution>, String> {
    let conn = state.conn.lock().map_err(|e| e.to_string())?;

    conn.query_row(
        "SELECT id, preset_id, preset_name, status, instance_id, error_message, started_at, completed_at FROM executions WHERE id = ?1",
        params![id],
        |row| {
            Ok(Execution {
                id: row.get(0)?,
                preset_id: row.get(1)?,
                preset_name: row.get(2)?,
                status: row.get(3)?,
                instance_id: row.get(4)?,
                error_message: row.get(5)?,
                started_at: row.get(6)?,
                completed_at: row.get(7)?,
            })
        },
    ).optional()
    .map_err(|e| format!("Failed to query execution: {}", e))
}
