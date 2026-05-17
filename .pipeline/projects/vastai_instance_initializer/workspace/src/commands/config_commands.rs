use tauri::State;
use crate::config::app_config::AppConfig;

#[tauri::command]
pub fn set_api_key(config: State<AppConfig>, api_key: String) -> crate::db::models::ApiResponse<()> {
    config.set_api_key(api_key);
    crate::db::models::ApiResponse::ok()
}

#[tauri::command]
pub fn get_api_key(config: State<AppConfig>) -> crate::db::models::ApiResponse<Option<String>> {
    let key = config.get_api_key();
    crate::db::models::ApiResponse::ok_with_data(key)
}
