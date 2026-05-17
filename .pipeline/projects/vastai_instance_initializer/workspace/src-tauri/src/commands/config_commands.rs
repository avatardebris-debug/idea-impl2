use crate::config::AppConfig;
use serde::{Deserialize, Serialize};
use tauri::State;

#[derive(Serialize, Deserialize, Clone)]
pub struct AppConfigResponse {
  pub vastai_api_key: Option<String>,
  pub presets_count: usize,
  pub last_updated: String,
}

#[derive(Serialize, Deserialize, Clone)]
pub struct UpdateAppConfigRequest {
  pub vastai_api_key: Option<String>,
}

#[tauri::command]
pub async fn get_app_config(
  state: State<AppConfig>,
) -> Result<AppConfigResponse, String> {
  let config = state.inner().clone();
  Ok(AppConfigResponse {
    vastai_api_key: config.vastai_api_key.clone(),
    presets_count: config.presets.len(),
    last_updated: config.last_updated.clone(),
  })
}

#[tauri::command]
pub async fn update_app_config(
  request: UpdateAppConfigRequest,
  state: State<AppConfig>,
) -> Result<AppConfigResponse, String> {
  let mut config = state.inner().clone();
  config.vastai_api_key = request.vastai_api_key;
  config.save().map_err(|e| format!("Failed to save config: {}", e))?;
  Ok(AppConfigResponse {
    vastai_api_key: config.vastai_api_key.clone(),
    presets_count: config.presets.len(),
    last_updated: config.last_updated.clone(),
  })
}
