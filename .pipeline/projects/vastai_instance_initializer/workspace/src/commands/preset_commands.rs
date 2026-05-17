use tauri::State;
use crate::api::ApiKeyStore;
use crate::db::models::*;
use crate::db::presets;

#[tauri::command]
pub fn create_preset(state: State<crate::db::AppState>, config: State<ApiKeyStore>, request: CreatePresetRequest) -> ApiResponse<Preset> {
    let api_key = config.get_key();
    if api_key.is_none() {
        return ApiResponse::err("API key not set. Please configure your VAST AI API key first.".to_string());
    }

    let id = crate::db::generate_id();
    let now = crate::db::now_rfc3339();

    let preset = Preset {
        id: id.clone(),
        name: request.name,
        description: request.description,
        created_at: now.clone(),
        updated_at: now.clone(),
        config: PresetConfig {
            gpu_type: request.gpu_type,
            max_price: request.max_price,
            instance_count: request.instance_count,
            inter_instance_delay_seconds: request.inter_instance_delay_seconds,
            commands: request.commands,
        },
    };

    match presets::create_preset(&state, preset.clone()) {
        Ok(preset) => ApiResponse::ok_with_data(preset),
        Err(e) => ApiResponse::err(e),
    }
}

#[tauri::command]
pub fn update_preset(state: State<crate::db::AppState>, config: State<ApiKeyStore>, request: UpdatePresetRequest) -> ApiResponse<Preset> {
    let api_key = config.get_key();
    if api_key.is_none() {
        return ApiResponse::err("API key not set. Please configure your VAST AI API key first.".to_string());
    }

    let preset = Preset {
        id: request.id,
        name: request.name,
        description: request.description,
        created_at: String::new(), // Will be preserved from DB
        updated_at: crate::db::now_rfc3339(),
        config: PresetConfig {
            gpu_type: request.gpu_type,
            max_price: request.max_price,
            instance_count: request.instance_count,
            inter_instance_delay_seconds: request.inter_instance_delay_seconds,
            commands: request.commands,
        },
    };

    match presets::update_preset(&state, preset.clone()) {
        Ok(preset) => ApiResponse::ok_with_data(preset),
        Err(e) => ApiResponse::err(e),
    }
}

#[tauri::command]
pub fn delete_preset(state: State<crate::db::AppState>, config: State<ApiKeyStore>, id: String) -> ApiResponse<()> {
    let api_key = config.get_key();
    if api_key.is_none() {
        return ApiResponse::err("API key not set. Please configure your VAST AI API key first.".to_string());
    }

    match presets::delete_preset(&state, &id) {
        Ok(()) => ApiResponse::ok(),
        Err(e) => ApiResponse::err(e),
    }
}

#[tauri::command]
pub fn list_presets(state: State<crate::db::AppState>, config: State<ApiKeyStore>) -> ApiResponse<Vec<Preset>> {
    let api_key = config.get_key();
    if api_key.is_none() {
        return ApiResponse::err("API key not set. Please configure your VAST AI API key first.".to_string());
    }

    match presets::list_presets(&state) {
        Ok(presets) => ApiResponse::ok_with_data(presets),
        Err(e) => ApiResponse::err(e),
    }
}

#[tauri::command]
pub fn get_preset(state: State<crate::db::AppState>, config: State<ApiKeyStore>, id: String) -> ApiResponse<Preset> {
    let api_key = config.get_key();
    if api_key.is_none() {
        return ApiResponse::err("API key not set. Please configure your VAST AI API key first.".to_string());
    }

    match presets::get_preset(&state, &id) {
        Ok(Some(preset)) => ApiResponse::ok_with_data(preset),
        Ok(None) => ApiResponse::err("Preset not found".to_string()),
        Err(e) => ApiResponse::err(e),
    }
}
