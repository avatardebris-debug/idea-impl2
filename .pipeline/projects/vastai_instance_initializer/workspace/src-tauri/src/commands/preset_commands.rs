use crate::config::AppConfig;
use serde::{Deserialize, Serialize};
use tauri::State;

#[derive(Serialize, Deserialize, Clone)]
pub struct CreatePresetRequest {
  pub name: String,
  pub description: String,
  pub gpu_type: String,
  pub max_price: f64,
  pub instance_count: u32,
  pub inter_instance_delay_seconds: u32,
  pub commands: String,
}

#[derive(Serialize, Deserialize, Clone)]
pub struct UpdatePresetRequest {
  pub id: String,
  pub name: String,
  pub description: String,
  pub gpu_type: String,
  pub max_price: f64,
  pub instance_count: u32,
  pub inter_instance_delay_seconds: u32,
  pub commands: String,
}

#[derive(Serialize, Deserialize, Clone)]
pub struct RunPresetRequest {
  pub preset_id: String,
}

#[tauri::command]
pub async fn create_preset(
  request: CreatePresetRequest,
  state: State<AppConfig>,
) -> Result<serde_json::Value, String> {
  let mut config = state.inner().clone();
  let preset = crate::config::Preset {
    id: uuid::Uuid::new_v4().to_string(),
    name: request.name,
    description: request.description,
    config: crate::config::PresetConfig {
      gpu_type: request.gpu_type,
      max_price: request.max_price,
      instance_count: request.instance_count,
      inter_instance_delay_seconds: request.inter_instance_delay_seconds,
      commands: request.commands,
    },
  };
  config.update_preset(preset.clone());
  config.save().map_err(|e| format!("Failed to save config: {}", e))?;
  Ok(serde_json::json!({ "data": preset }))
}

#[tauri::command]
pub async fn list_presets(
  state: State<AppConfig>,
) -> Result<serde_json::Value, String> {
  let config = state.inner().clone();
  Ok(serde_json::json!({ "data": config.presets }))
}

#[tauri::command]
pub async fn update_preset(
  request: UpdatePresetRequest,
  state: State<AppConfig>,
) -> Result<serde_json::Value, String> {
  let mut config = state.inner().clone();
  let preset = crate::config::Preset {
    id: request.id,
    name: request.name,
    description: request.description,
    config: crate::config::PresetConfig {
      gpu_type: request.gpu_type,
      max_price: request.max_price,
      instance_count: request.instance_count,
      inter_instance_delay_seconds: request.inter_instance_delay_seconds,
      commands: request.commands,
    },
  };
  config.update_preset(preset.clone());
  config.save().map_err(|e| format!("Failed to save config: {}", e))?;
  Ok(serde_json::json!({ "data": preset }))
}

#[tauri::command]
pub async fn delete_preset(
  id: String,
  state: State<AppConfig>,
) -> Result<(), String> {
  let mut config = state.inner().clone();
  config.remove_preset(&id);
  config.save().map_err(|e| format!("Failed to save config: {}", e))?;
  Ok(())
}

#[tauri::command]
pub async fn run_preset(
  request: RunPresetRequest,
  state: State<AppConfig>,
) -> Result<serde_json::Value, String> {
  let config = state.inner().clone();
  let preset = config.presets.iter().find(|p| p.id == request.preset_id)
    .ok_or_else(|| "Preset not found".to_string())?;

  let api_key = config.vastai_api_key.clone()
    .ok_or_else(|| "API key not configured".to_string())?;

  // TODO: Implement actual instance provisioning logic
  // For now, return a placeholder execution record
  let execution = crate::vastai_client::ExecutionRecord {
    id: uuid::Uuid::new_v4().to_string(),
    preset_id: preset.id.clone(),
    preset_name: preset.name.clone(),
    status: "running".to_string(),
    started_at: chrono::Utc::now().to_rfc3339(),
    completed_at: None,
    error_message: None,
    instances_created: vec![],
  };

  Ok(serde_json::json!({
    "data": execution
  }))
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
