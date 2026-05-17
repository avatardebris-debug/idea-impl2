#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
  tauri::Builder::default()
    .manage(crate::config::AppConfig::load())
    .invoke_handler(tauri::generate_handler![
      // API commands
      crate::commands::api_commands::get_api_key,
      crate::commands::api_commands::set_api_key,
      crate::commands::api_commands::list_available_gpus,
      crate::commands::api_commands::get_instance_status,
      // Preset commands
      crate::commands::preset_commands::create_preset,
      crate::commands::preset_commands::list_presets,
      crate::commands::preset_commands::update_preset,
      crate::commands::preset_commands::delete_preset,
      crate::commands::preset_commands::run_preset,
      crate::commands::preset_commands::get_execution_history,
      crate::commands::preset_commands::get_execution_status,
      // Config commands
      crate::commands::config_commands::get_app_config,
      crate::commands::config_commands::update_app_config,
    ])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
