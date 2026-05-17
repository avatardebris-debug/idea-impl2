use crate::config::AppConfig;
use crate::vastai_client;
use serde::{Deserialize, Serialize};
use tauri::State;

#[tauri::command]
pub async fn get_api_key() -> Result<Option<String>, String> {
  let config = AppConfig::load();
  Ok(config.vastai_api_key)
}

#[tauri::command]
pub async fn set_api_key(
  api_key: String,
  state: tauri::State<AppConfig>,
) -> Result<(), String> {
  let mut config = state.inner().clone();
  if api_key.is_empty() {
    config.vastai_api_key = None;
  } else {
    config.vastai_api_key = Some(api_key);
  }
  config.save().map_err(|e| format!("Failed to save config: {}", e))?;
  Ok(())
}

#[tauri::command]
pub async fn list_available_gpus(
  state: tauri::State<AppConfig>,
) -> Result<Vec<vastai_client::AvailableGpu>, String> {
  let config = state.inner().clone();
  let api_key = config.vastai_api_key.clone()
    .ok_or_else(|| "API key not configured".to_string())?;
  vastai_client::list_available_gpus(&api_key).await
}

#[tauri::command]
pub async fn get_instance_status(
  instance_id: String,
  state: tauri::State<AppConfig>,
) -> Result<vastai_client::InstanceStatus, String> {
  let config = state.inner().clone();
  let api_key = config.vastai_api_key.clone()
    .ok_or_else(|| "API key not configured".to_string())?;
  vastai_client::get_instance_status(&api_key, &instance_id).await
}
