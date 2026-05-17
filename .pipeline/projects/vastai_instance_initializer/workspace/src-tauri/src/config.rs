use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub api_key: Option<String>,
    pub default_gpu_type: String,
    pub default_max_price: f64,
    pub default_instance_count: u32,
    pub default_inter_instance_delay: u64,
}

impl AppConfig {
    pub fn load() -> Self {
        let config_path = Self::get_config_path();
        if config_path.exists() {
            if let Ok(content) = fs::read_to_string(&config_path) {
                if let Ok(config) = serde_json::from_str::<Self>(&content) {
                    return config;
                }
            }
        }
        Self::default()
    }

    pub fn save(&self) -> Result<(), anyhow::Error> {
        let config_path = Self::get_config_path();
        if let Some(parent) = config_path.parent() {
            fs::create_dir_all(parent)?;
        }
        let content = serde_json::to_string_pretty(self)?;
        fs::write(&config_path, content)?;
        Ok(())
    }

    fn get_config_path() -> PathBuf {
        let mut path = dirs::config_dir().unwrap_or_else(|| PathBuf::from("."));
        path.push("vastai-instance-manager");
        path.push("config.json");
        path
    }
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            api_key: None,
            default_gpu_type: "A100".to_string(),
            default_max_price: 1.0,
            default_instance_count: 1,
            default_inter_instance_delay: 5,
        }
    }
}
