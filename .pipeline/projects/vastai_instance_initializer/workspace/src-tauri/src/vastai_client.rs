use reqwest::Client;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct AvailableGpu {
  pub id: String,
  pub name: String,
  pub price: f64,
  pub storage: u64,
  pub ram: u64,
  pub cpu_cores: u32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct InstanceStatus {
  pub id: String,
  pub state: String,
  pub gpu_name: String,
  pub price: f64,
  pub storage_used: u64,
  pub uptime_seconds: u64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ExecutionRecord {
  pub id: String,
  pub preset_id: String,
  pub preset_name: String,
  pub status: String,
  pub started_at: String,
  pub completed_at: Option<String>,
  pub error_message: Option<String>,
  pub instances_created: Vec<InstanceInfo>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct InstanceInfo {
  pub instance_id: String,
  pub ip_address: String,
  pub port: u32,
  pub status: String,
  pub error_message: Option<String>,
}

pub async fn get_api_key() -> Result<Option<String>, String> {
  let config = crate::config::AppConfig::load();
  Ok(config.vastai_api_key)
}

pub async fn set_api_key(api_key: String) -> Result<(), String> {
  let mut config = crate::config::AppConfig::load();
  if api_key.is_empty() {
    config.vastai_api_key = None;
  } else {
    config.vastai_api_key = Some(api_key);
  }
  config.save()?;
  Ok(())
}

pub async fn list_available_gpus(api_key: &str) -> Result<Vec<AvailableGpu>, String> {
  let client = Client::new();
  let response = client
    .get("https://cloud.vast.ai/api/v0/offers/")
    .header("Authorization", format!("Token {}", api_key))
    .header("Content-Type", "application/json")
    .send()
    .await
    .map_err(|e| format!("Failed to fetch GPU list: {}", e))?;

  if !response.status().is_success() {
    return Err(format!("API error: {}", response.status()));
  }

  let gpus: Vec<serde_json::Value> = response
    .json()
    .await
    .map_err(|e| format!("Failed to parse GPU list: {}", e))?;

  let result: Vec<AvailableGpu> = gpus
    .iter()
    .filter(|gpu| {
      gpu.get("unavail").map_or(false, |v| v.as_bool() == Some(false))
        && gpu.get("disk").map_or(false, |v| v.as_u64().map_or(false, |d| d > 0))
    })
    .map(|gpu| AvailableGpu {
      id: gpu["id"].as_u64().unwrap_or(0).to_string(),
      name: gpu["gpu"]["name"].as_str().unwrap_or("Unknown").to_string(),
      price: gpu["price_str"].as_f64().unwrap_or(0.0),
      storage: gpu["disk"].as_u64().unwrap_or(0),
      ram: gpu["ram"].as_u64().unwrap_or(0),
      cpu_cores: gpu["cpu"].as_object().map_or(0, |o| o.len() as u32),
    })
    .collect();

  Ok(result)
}

pub async fn get_instance_status(api_key: &str, instance_id: &str) -> Result<InstanceStatus, String> {
  let client = Client::new();
  let response = client
    .get(&format!("https://cloud.vast.ai/api/v0/instances/{}", instance_id))
    .header("Authorization", format!("Token {}", api_key))
    .header("Content-Type", "application/json")
    .send()
    .await
    .map_err(|e| format!("Failed to fetch instance status: {}", e))?;

  if !response.status().is_success() {
    return Err(format!("API error: {}", response.status()));
  }

  let instance: serde_json::Value = response
    .json()
    .await
    .map_err(|e| format!("Failed to parse instance status: {}", e))?;

  Ok(InstanceStatus {
    id: instance["id"].as_u64().unwrap_or(0).to_string(),
    state: instance["state"].as_str().unwrap_or("unknown").to_string(),
    gpu_name: instance["gpu"]["name"].as_str().unwrap_or("Unknown").to_string(),
    price: instance["price_str"].as_f64().unwrap_or(0.0),
    storage_used: instance["disk_used"].as_u64().unwrap_or(0),
    uptime_seconds: instance["uptime"].as_u64().unwrap_or(0),
  })
}
