pub mod preset_commands;
pub mod execution_commands;
pub mod config_commands;

use tauri::State;
use crate::api::ApiKeyStore;
use crate::api::vastai_client::VastAIClient;
use crate::api::models::InstanceFilters;
use crate::db::models::*;

#[tauri::command]
pub async fn list_instances(state: State<crate::db::AppState>, config: State<ApiKeyStore>, filters: InstanceFilters) -> ApiResponse<Vec<crate::api::models::InstanceInfo>> {
    let api_key = match config.get_key() {
        Some(key) => key,
        None => return ApiResponse::err("API key not set. Please configure your VAST AI API key first.".to_string()),
    };

    let client = VastAIClient::new();
    match client.list_instances(&api_key, &filters).await {
        Ok(instances) => ApiResponse::ok_with_data(instances),
        Err(e) => ApiResponse::err(e),
    }
}

#[tauri::command]
pub async fn get_instance_status(state: State<crate::db::AppState>, config: State<ApiKeyStore>, instance_id: String) -> ApiResponse<crate::api::models::InstanceInfo> {
    let api_key = match config.get_key() {
        Some(key) => key,
        None => return ApiResponse::err("API key not set. Please configure your VAST AI API key first.".to_string()),
    };

    let client = VastAIClient::new();
    match client.get_instance_status(&api_key, &instance_id).await {
        Ok(instance) => ApiResponse::ok_with_data(instance),
        Err(e) => ApiResponse::err(e),
    }
}
