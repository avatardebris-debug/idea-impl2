use tauri::Manager;

fn main() {
    env_logger::init();
    tauri::Builder::default()
        .setup(|app| {
            // Initialize database on startup
            let app_handle = app.handle();
            std::thread::spawn(move || {
                if let Err(e) = vastai_instance_initializer_lib::db::init_db(&app_handle.state::<vastai_instance_initializer_lib::db::AppState>()) {
                    eprintln!("Failed to initialize database: {}", e);
                }
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            // Preset commands
            vastai_instance_initializer_lib::commands::create_preset,
            vastai_instance_initializer_lib::commands::update_preset,
            vastai_instance_initializer_lib::commands::delete_preset,
            vastai_instance_initializer_lib::commands::list_presets,
            vastai_instance_initializer_lib::commands::get_preset,
            // Execution commands
            vastai_instance_initializer_lib::commands::run_preset,
            vastai_instance_initializer_lib::commands::get_execution_history,
            vastai_instance_initializer_lib::commands::get_execution_status,
            // Config commands
            vastai_instance_initializer_lib::commands::set_api_key,
            vastai_instance_initializer_lib::commands::get_api_key,
            // API commands
            vastai_instance_initializer_lib::commands::list_instances,
            vastai_instance_initializer_lib::commands::get_instance_status,
        ])
        .manage(vastai_instance_initializer_lib::db::AppState::new())
        .run(tauri::generate_context!())
        .expect("error while running vastai-instance-initializer");
}
