use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Preset {
    pub id: String,
    pub name: String,
    pub description: String,
    pub created_at: String,
    pub updated_at: String,
    pub config: PresetConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct PresetConfig {
    pub gpu_type: String,
    pub max_price: f64,
    pub instance_count: u32,
    pub inter_instance_delay_seconds: u32,
    pub commands: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Execution {
    pub id: String,
    pub preset_id: String,
    pub preset_name: String,
    pub status: String,
    pub instance_id: String,
    pub error_message: String,
    pub started_at: String,
    pub completed_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InstanceStatus {
    pub execution_id: String,
    pub instance_id: String,
    pub status: String,
    pub gpu_type: String,
    pub price_per_hour: f64,
    pub details: String,
    pub created_at: String,
    pub updated_at: String,
}

// Frontend-facing types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreatePresetRequest {
    pub name: String,
    pub description: String,
    pub gpu_type: String,
    pub max_price: f64,
    pub instance_count: u32,
    pub inter_instance_delay_seconds: u32,
    pub commands: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
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

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunPresetRequest {
    pub preset_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiResponse<T> {
    pub success: bool,
    pub data: Option<T>,
    pub error: Option<String>,
}

impl ApiResponse<()> {
    pub fn ok() -> Self {
        ApiResponse {
            success: true,
            data: None,
            error: None,
        }
    }
}

impl<T: Serialize> ApiResponse<T> {
    pub fn ok_with_data(data: T) -> Self {
        ApiResponse {
            success: true,
            data: Some(data),
            error: None,
        }
    }

    pub fn err(msg: String) -> Self {
        ApiResponse {
            success: false,
            data: None,
            error: Some(msg),
        }
    }
}

pub fn generate_id() -> String {
    Uuid::new_v4().to_string()
}

pub fn now_rfc3339() -> String {
    chrono::Utc::now().to_rfc3339()
}
