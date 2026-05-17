use crate::config::AppConfig;
use serde::{Deserialize, Serialize};
use tauri::State;

#[derive(Serialize, Deserialize, Clone)]
pub struct ExecutionRecord {
  pub id: String,
  pub preset_id: String,
  pub preset_name: String,
  pub status: String,
  pub started_at: String,
  pub completed_at: Option<String>,
  pub error_message: Option<String>,
  pub instances_created: Vec<crate::vastai_client::InstanceInfo>,
}

#[tauri::command]
pub async fn get_execution_history(
  state: State<AppConfig>,
) -> Result<serde_json::Value, String> {
  // TODO: Store execution history in config or separate file
  Ok(serde_json::json!({ "data": vec![] }))
}

#[tauri::command]
pub async fn get_execution_status(
  execution_id: String,
  state: State<AppConfig>,
) -> Result<serde_json::Value, String> {
  // TODO: Implement execution status lookup
  Ok(serde_json::json!({ "data": null }))
}
