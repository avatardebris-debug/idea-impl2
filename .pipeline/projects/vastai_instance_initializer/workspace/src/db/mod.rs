pub mod models;
pub mod schema;
pub mod presets;
pub mod executions;
pub mod instances;

use rusqlite::{Connection, Result as SqliteResult};
use std::sync::Mutex;
use tauri::State;

#[derive(Clone)]
pub struct AppState {
    pub conn: Mutex<Connection>,
}

impl AppState {
    pub fn new() -> Self {
        // Create in-memory database for now, will be file-based in production
        let conn = Connection::open_in_memory().expect("Failed to open in-memory database");
        AppState {
            conn: Mutex::new(conn),
        }
    }

    pub fn open_file_db(path: &str) -> SqliteResult<Self> {
        let conn = Connection::open(path)?;
        Ok(AppState {
            conn: Mutex::new(conn),
        })
    }
}

pub fn init_db(state: &State<AppState>) -> SqliteResult<()> {
    let conn = state.conn.lock().unwrap();
    schema::create_tables(&conn)?;
    Ok(())
}
