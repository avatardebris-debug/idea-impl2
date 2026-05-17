use serde::{Deserialize, Serialize};
use rusqlite::{Connection, Result as SqliteResult, params};
use uuid::Uuid;
use chrono;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Preset {
    pub id: String,
    pub name: String,
    pub description: String,
    pub created_at: String,
    pub updated_at: String,
    pub config: PresetConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct PresetConfig {
    pub gpu_type: String,
    pub max_price: f64,
    pub instance_count: u32,
    pub inter_instance_delay_seconds: u32,
    pub commands: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Execution {
    pub id: String,
    pub preset_id: String,
    pub preset_name: String,
    pub status: String,
    pub instance_id: String,
    pub error_message: String,
    pub started_at: String,
    pub completed_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InstanceStatus {
    pub execution_id: String,
    pub instance_id: String,
    pub status: String,
    pub gpu_type: String,
    pub price_per_hour: f64,
    pub details: String,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiResponse<T> {
    pub success: bool,
    pub data: Option<T>,
    pub error: Option<String>,
}

impl ApiResponse<()> {
    pub fn ok() -> Self {
        ApiResponse {
            success: true,
            data: None,
            error: None,
        }
    }
}

impl<T: Serialize> ApiResponse<T> {
    pub fn ok_with_data(data: T) -> Self {
        ApiResponse {
            success: true,
            data: Some(data),
            error: None,
        }
    }

    pub fn err(msg: String) -> Self {
        ApiResponse {
            success: false,
            data: None,
            error: Some(msg),
        }
    }
}

pub struct Database {
    conn: Connection,
}

impl Database {
    pub fn new() -> SqliteResult<Self> {
        let db_path = Self::get_db_path();
        let conn = Connection::open(db_path)?;
        
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS presets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                gpu_type TEXT NOT NULL,
                max_price REAL NOT NULL,
                instance_count INTEGER NOT NULL,
                inter_instance_delay_seconds INTEGER NOT NULL,
                commands TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS executions (
                id TEXT PRIMARY KEY,
                preset_id TEXT NOT NULL,
                preset_name TEXT NOT NULL,
                status TEXT NOT NULL,
                instance_id TEXT,
                error_message TEXT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (preset_id) REFERENCES presets(id)
            );
            
            CREATE TABLE IF NOT EXISTS instances (
                id TEXT PRIMARY KEY,
                execution_id TEXT NOT NULL,
                instance_id TEXT,
                status TEXT NOT NULL,
                gpu_type TEXT,
                price_per_hour REAL,
                details TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (execution_id) REFERENCES executions(id)
            );"
        )?;
        
        Ok(Database { conn })
    }

    fn get_db_path() -> String {
        let mut path = dirs::data_dir().unwrap_or_else(|| PathBuf::from("."));
        path.push("vastai-instance-manager");
        path.push("app.db");
        path.to_str().unwrap_or("app.db").to_string()
    }

    pub fn create_preset(&self, name: &str, description: &str, gpu_type: &str, max_price: f64, instance_count: u32, inter_instance_delay: u32, commands: &str) -> SqliteResult<Preset> {
        let id = Uuid::new_v4().to_string();
        let now = chrono::Utc::now().to_rfc3339();
        
        self.conn.execute(
            "INSERT INTO presets (id, name, description, gpu_type, max_price, instance_count, inter_instance_delay_seconds, commands, created_at, updated_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)",
            params![&id, name, description, gpu_type, max_price, instance_count, inter_instance_delay, commands, &now, &now]
        )?;
        
        Ok(Preset {
            id,
            name: name.to_string(),
            description: description.to_string(),
            created_at: now.clone(),
            updated_at: now,
            config: PresetConfig {
                gpu_type: gpu_type.to_string(),
                max_price,
                instance_count,
                inter_instance_delay_seconds: inter_instance_delay,
                commands: commands.to_string(),
            },
        })
    }

    pub fn update_preset(&self, id: &str, name: &str, description: &str, gpu_type: &str, max_price: f64, instance_count: u32, inter_instance_delay: u32, commands: &str) -> SqliteResult<Preset> {
        let now = chrono::Utc::now().to_rfc3339();
        
        self.conn.execute(
            "UPDATE presets SET name=?2, description=?3, gpu_type=?4, max_price=?5, instance_count=?6, inter_instance_delay_seconds=?7, commands=?8, updated_at=?9 WHERE id=?1",
            params![id, name, description, gpu_type, max_price, instance_count, inter_instance_delay, commands, &now]
        )?;
        
        self.get_preset(id)
    }

    pub fn delete_preset(&self, id: &str) -> SqliteResult<()> {
        self.conn.execute("DELETE FROM presets WHERE id=?1", params![id])?;
        Ok(())
    }

    pub fn get_preset(&self, id: &str) -> SqliteResult<Preset> {
        self.conn.query_row(
            "SELECT id, name, description, gpu_type, max_price, instance_count, inter_instance_delay_seconds, commands, created_at, updated_at FROM presets WHERE id=?1",
            params![id],
            |row| {
                Ok(Preset {
                    id: row.get(0)?,
                    name: row.get(1)?,
                    description: row.get(2)?,
                    created_at: row.get(9)?,
                    updated_at: row.get(10)?,
                    config: PresetConfig {
                        gpu_type: row.get(3)?,
                        max_price: row.get(4)?,
                        instance_count: row.get(5)?,
                        inter_instance_delay_seconds: row.get(6)?,
                        commands: row.get(7)?,
                    },
                })
            }
        )
    }

    pub fn list_presets(&self) -> SqliteResult<Vec<Preset>> {
        let mut stmt = self.conn.prepare("SELECT id, name, description, gpu_type, max_price, instance_count, inter_instance_delay_seconds, commands, created_at, updated_at FROM presets ORDER BY updated_at DESC")?;
        let presets = stmt.query_map(params![], |row| {
            Ok(Preset {
                id: row.get(0)?,
                name: row.get(1)?,
                description: row.get(2)?,
                created_at: row.get(9)?,
                updated_at: row.get(10)?,
                config: PresetConfig {
                    gpu_type: row.get(3)?,
                    max_price: row.get(4)?,
                    instance_count: row.get(5)?,
                    inter_instance_delay_seconds: row.get(6)?,
                    commands: row.get(7)?,
                },
            })
        })?;
        
        presets.collect()
    }

    pub fn create_execution(&self, preset_id: &str, preset_name: &str) -> SqliteResult<Execution> {
        let id = Uuid::new_v4().to_string();
        let now = chrono::Utc::now().to_rfc3339();
        
        self.conn.execute(
            "INSERT INTO executions (id, preset_id, preset_name, status, started_at) VALUES (?1, ?2, ?3, ?4, ?5)",
            params![&id, preset_id, preset_name, "running", &now]
        )?;
        
        Ok(Execution {
            id,
            preset_id: preset_id.to_string(),
            preset_name: preset_name.to_string(),
            status: "running".to_string(),
            instance_id: String::new(),
            error_message: String::new(),
            started_at: now,
            completed_at: None,
        })
    }

    pub fn update_execution_status(&self, id: &str, status: &str, instance_id: Option<&str>, error_message: Option<&str>) -> SqliteResult<()> {
        let now = chrono::Utc::now().to_rfc3339();
        let completed_at = if status == "completed" || status == "failed" { Some(now.clone()) } else { None };
        
        self.conn.execute(
            "UPDATE executions SET status=?2, instance_id=?3, error_message=?4, completed_at=?5, updated_at=?6 WHERE id=?1",
            params![id, status, instance_id.unwrap_or(""), error_message.unwrap_or(""), &completed_at, &now]
        )?;
        
        Ok(())
    }

    pub fn get_execution_history(&self) -> SqliteResult<Vec<Execution>> {
        let mut stmt = self.conn.prepare("SELECT id, preset_id, preset_name, status, instance_id, error_message, started_at, completed_at FROM executions ORDER BY started_at DESC")?;
        let executions = stmt.query_map(params![], |row| {
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
        })?;
        
        executions.collect()
    }

    pub fn create_instance(&self, execution_id: &str, instance_id: &str, status: &str, gpu_type: &str, price_per_hour: f64, details: &str) -> SqliteResult<InstanceStatus> {
        let id = Uuid::new_v4().to_string();
        let now = chrono::Utc::now().to_rfc3339();
        
        self.conn.execute(
            "INSERT INTO instances (id, execution_id, instance_id, status, gpu_type, price_per_hour, details, created_at, updated_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
            params![&id, execution_id, instance_id, status, gpu_type, price_per_hour, details, &now, &now]
        )?;
        
        Ok(InstanceStatus {
            id,
            execution_id: execution_id.to_string(),
            instance_id: instance_id.to_string(),
            status: status.to_string(),
            gpu_type: gpu_type.to_string(),
            price_per_hour,
            details: details.to_string(),
            created_at: now.clone(),
            updated_at: now,
        })
    }

    pub fn update_instance_status(&self, execution_id: &str, instance_id: &str, status: &str, details: &str) -> SqliteResult<()> {
        let now = chrono::Utc::now().to_rfc3339();
        self.conn.execute(
            "UPDATE instances SET status=?3, details=?4, updated_at=?5 WHERE execution_id=?1 AND instance_id=?2",
            params![execution_id, instance_id, status, details, &now]
        )?;
        Ok(())
    }
}
