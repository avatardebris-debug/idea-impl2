use tauri::State;
use crate::api::ApiKeyStore;
use crate::db::models::*;
use crate::db::executions;
use crate::api::vastai_client::VastAIClient;
use crate::api::models::InstanceFilters;
use std::time::Duration;
use tokio::time::sleep;

#[tauri::command]
pub async fn run_preset(state: State<crate::db::AppState>, config: State<ApiKeyStore>, request: RunPresetRequest) -> ApiResponse<Execution> {
    let api_key = match config.get_key() {
        Some(key) => key,
        None => return ApiResponse::err("API key not set. Please configure your VAST AI API key first.".to_string()),
    };

    // Get preset
    let preset = match crate::db::presets::get_preset(&state, &request.preset_id) {
        Ok(Some(preset)) => preset,
        Ok(None) => return ApiResponse::err("Preset not found".to_string()),
        Err(e) => return ApiResponse::err(e),
    };

    let client = VastAIClient::new();

    // Find available instances
    let filters = InstanceFilters {
        gpu_type: preset.config.gpu_type.clone(),
        max_price: preset.config.max_price,
        instance_count: preset.config.instance_count,
    };

    let instances = match client.list_instances(&api_key, &filters).await {
        Ok(instances) => instances,
        Err(e) => return ApiResponse::err(format!("Failed to list instances: {}", e)),
    };

    if instances.is_empty() {
        return ApiResponse::err("No available instances found matching criteria".to_string());
    }

    // Create execution record
    let execution_id = crate::db::generate_id();
    let started_at = crate::db::now_rfc3339();

    let execution = Execution {
        id: execution_id.clone(),
        preset_id: request.preset_id.clone(),
        preset_name: preset.name.clone(),
        status: "running".to_string(),
        instance_id: String::new(),
        error_message: String::new(),
        started_at: started_at.clone(),
        completed_at: None,
    };

    // Insert execution
    match executions::insert_execution(&state, execution.clone()) {
        Ok(_) => {},
        Err(e) => return ApiResponse::err(format!("Failed to create execution record: {}", e)),
    }

    // Spawn background task to execute the preset
    let state_clone = state.clone();
    let config_clone = config.clone();
    let preset_clone = preset.clone();
    let execution_id_clone = execution_id.clone();

    tauri::async_runtime::spawn(async move {
        execute_preset_background(
            state_clone,
            config_clone,
            preset_clone,
            execution_id_clone,
            instances,
        ).await;
    });

    ApiResponse::ok_with_data(execution)
}

async fn execute_preset_background(
    state: State<crate::db::AppState>,
    config: State<ApiKeyStore>,
    preset: Preset,
    execution_id: String,
    available_instances: Vec<crate::api::models::InstanceInfo>,
) {
    let api_key = match config.get_key() {
        Some(key) => key,
        None => {
            let _ = executions::update_execution_status(&state, &execution_id, "failed", Some("API key not set"));
            return;
        }
    };

    let client = VastAIClient::new();
    let mut success_count = 0;
    let mut failed_count = 0;

    for (i, instance) in available_instances.iter().enumerate() {
        // Check if we've reached the instance count
        if i >= preset.config.instance_count as usize {
            break;
        }

        // Apply inter-instance delay
        if i > 0 && preset.config.inter_instance_delay_seconds > 0 {
            sleep(Duration::from_secs(preset.config.inter_instance_delay_seconds as u64)).await;
        }

        // Try to create instance
        match client.create_instance(&api_key, &instance.id).await {
            Ok(ssh_info) => {
                // Update execution with instance ID
                let _ = executions::update_execution_status(&state, &execution_id, "running", None);

                // Store instance status
                let status = crate::db::models::InstanceStatus {
                    execution_id: execution_id.clone(),
                    instance_id: ssh_info.id.clone(),
                    status: "running".to_string(),
                    gpu_type: instance.gpu_name.clone(),
                    price_per_hour: instance.price,
                    details: serde_json::to_string(&ssh_info).unwrap_or_default(),
                    created_at: crate::db::now_rfc3339(),
                    updated_at: crate::db::now_rfc3339(),
                };

                let _ = crate::db::instances::insert_instance_status(&state, status);

                success_count += 1;

                // Execute commands if provided
                if !preset.config.commands.is_empty() {
                    // In a real implementation, this would SSH into the instance and run commands
                    // For now, we'll just log it
                    eprintln!("Would execute commands on instance {}: {}", ssh_info.id, preset.config.commands);
                }
            }
            Err(e) => {
                failed_count += 1;
                eprintln!("Failed to create instance {}: {}", instance.id, e);
            }
        }
    }

    // Update execution status
    let final_status = if failed_count == 0 {
        "completed"
    } else if success_count == 0 {
        "failed"
    } else {
        "partial"
    };

    let error_message = if failed_count > 0 {
        format!("Successfully created {} instances, failed to create {} instances", success_count, failed_count)
    } else {
        String::new()
    };

    let _ = executions::update_execution_status(
        &state,
        &execution_id,
        final_status,
        if final_status == "failed" { Some(&error_message) } else { None },
    );
}

#[tauri::command]
pub fn get_execution_history(state: State<crate::db::AppState>, config: State<ApiKeyStore>) -> ApiResponse<Vec<Execution>> {
    let _api_key = config.get_key();
    // API key not strictly required for history

    match executions::get_execution_history(&state) {
        Ok(executions) => ApiResponse::ok_with_data(executions),
        Err(e) => ApiResponse::err(e),
    }
}

#[tauri::command]
pub fn get_execution_status(state: State<crate::db::AppState>, config: State<ApiKeyStore>, execution_id: String) -> ApiResponse<Execution> {
    let _api_key = config.get_key();

    match executions::get_execution_by_id(&state, &execution_id) {
        Ok(Some(execution)) => ApiResponse::ok_with_data(execution),
        Ok(None) => ApiResponse::err("Execution not found".to_string()),
        Err(e) => ApiResponse::err(e),
    }
}
