use super::models::*;
use super::AppState;
use rusqlite::params;
use tauri::State;

pub fn create_preset(state: &State<AppState>, preset: Preset) -> Result<Preset, String> {
    let conn = state.conn.lock().map_err(|e| e.to_string())?;
    conn.execute(
        "INSERT INTO presets (id, name, description, created_at, updated_at) VALUES (?1, ?2, ?3, ?4, ?5)",
        params![
            preset.id,
            preset.name,
            preset.description,
            preset.created_at,
            preset.updated_at,
        ],
    )
    .map_err(|e| format!("Failed to insert preset: {}", e))?;

    // Insert preset config
    conn.execute(
        "INSERT INTO preset_configs (preset_id, gpu_type, max_price, instance_count, inter_instance_delay_seconds, commands) VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
        params![
            preset.id,
            preset.config.gpu_type,
            preset.config.max_price,
            preset.config.instance_count,
            preset.config.inter_instance_delay_seconds,
            preset.config.commands,
        ],
    )
    .map_err(|e| format!("Failed to insert preset config: {}", e))?;

    Ok(preset)
}

pub fn update_preset(state: &State<AppState>, preset: Preset) -> Result<Preset, String> {
    let conn = state.conn.lock().map_err(|e| e.to_string())?;

    // Update preset
    conn.execute(
        "UPDATE presets SET name = ?2, description = ?3, updated_at = ?4 WHERE id = ?1",
        params![
            preset.id,
            preset.name,
            preset.description,
            preset.updated_at,
        ],
    )
    .map_err(|e| format!("Failed to update preset: {}", e))?;

    // Update config
    conn.execute(
        "UPDATE preset_configs SET gpu_type = ?2, max_price = ?3, instance_count = ?4, inter_instance_delay_seconds = ?5, commands = ?6 WHERE preset_id = ?1",
        params![
            preset.id,
            preset.config.gpu_type,
            preset.config.max_price,
            preset.config.instance_count,
            preset.config.inter_instance_delay_seconds,
            preset.config.commands,
        ],
    )
    .map_err(|e| format!("Failed to update preset config: {}", e))?;

    Ok(preset)
}

pub fn delete_preset(state: &State<AppState>, id: &str) -> Result<(), String> {
    let conn = state.conn.lock().map_err(|e| e.to_string())?;
    conn.execute(
        "DELETE FROM presets WHERE id = ?1",
        params![id],
    )
    .map_err(|e| format!("Failed to delete preset: {}", e))?;
    Ok(())
}

pub fn get_preset(state: &State<AppState>, id: &str) -> Result<Option<Preset>, String> {
    let conn = state.conn.lock().map_err(|e| e.to_string())?;

    let preset = conn.query_row(
        "SELECT id, name, description, created_at, updated_at FROM presets WHERE id = ?1",
        params![id],
        |row| {
            Ok(Preset {
                id: row.get(0)?,
                name: row.get(1)?,
                description: row.get(2)?,
                created_at: row.get(3)?,
                updated_at: row.get(4)?,
                config: PresetConfig::default(),
            })
        },
    ).optional()
    .map_err(|e| format!("Failed to query preset: {}", e))?;

    if let Some(mut preset) = preset {
        let config = conn.query_row(
            "SELECT gpu_type, max_price, instance_count, inter_instance_delay_seconds, commands FROM preset_configs WHERE preset_id = ?1",
            params![id],
            |row| {
                Ok(PresetConfig {
                    gpu_type: row.get(0)?,
                    max_price: row.get(1)?,
                    instance_count: row.get(2)?,
                    inter_instance_delay_seconds: row.get(3)?,
                    commands: row.get(4)?,
                })
            },
        ).optional()
        .map_err(|e| format!("Failed to query preset config: {}", e))?;

        if let Some(config) = config {
            preset.config = config;
        }
        Ok(Some(preset))
    } else {
        Ok(None)
    }
}

pub fn list_presets(state: &State<AppState>) -> Result<Vec<Preset>, String> {
    let conn = state.conn.lock().map_err(|e| e.to_string())?;

    let mut stmt = conn.prepare(
        "SELECT id, name, description, created_at, updated_at FROM presets ORDER BY updated_at DESC"
    ).map_err(|e| format!("Failed to prepare query: {}", e))?;

    let preset_iter = stmt.query_map([], |row| {
        Ok(Preset {
            id: row.get(0)?,
            name: row.get(1)?,
            description: row.get(2)?,
            created_at: row.get(3)?,
            updated_at: row.get(4)?,
            config: PresetConfig::default(),
        })
    }).map_err(|e| format!("Failed to query presets: {}", e))?;

    let mut presets: Vec<Preset> = Vec::new();
    for preset_result in preset_iter {
        match preset_result {
            Ok(mut preset) => {
                // Load config for each preset
                let config = conn.query_row(
                    "SELECT gpu_type, max_price, instance_count, inter_instance_delay_seconds, commands FROM preset_configs WHERE preset_id = ?1",
                    params![&preset.id],
                    |row| {
                        Ok(PresetConfig {
                            gpu_type: row.get(0)?,
                            max_price: row.get(1)?,
                            instance_count: row.get(2)?,
                            inter_instance_delay_seconds: row.get(3)?,
                            commands: row.get(4)?,
                        })
                    },
                ).optional()
                .map_err(|e| format!("Failed to query config: {}", e))?;

                if let Some(config) = config {
                    preset.config = config;
                }
                presets.push(preset);
            }
            Err(e) => eprintln!("Error reading preset: {}", e),
        }
    }

    Ok(presets)
}
