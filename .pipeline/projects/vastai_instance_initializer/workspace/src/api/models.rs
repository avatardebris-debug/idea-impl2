use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InstanceInfo {
    pub id: String,
    pub dclass: String,
    pub gpu_name: String,
    pub price: f64,
    pub speed: f64,
    pub rentable: bool,
    pub rented: bool,
    pub renters_count: u32,
    pub storage: f64,
    pub ram: f64,
    pub uptime: u32,
    pub trust: f64,
    pub verified: bool,
    pub id_str: String,
    pub ssh_host: String,
    pub ssh_port: u32,
    pub details: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InstanceFilters {
    pub gpu_type: String,
    pub max_price: f64,
    pub instance_count: u32,
}

impl Default for InstanceFilters {
    fn default() -> Self {
        InstanceFilters {
            gpu_type: String::new(),
            max_price: 0.0,
            instance_count: 1,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateInstanceResponse {
    pub id: String,
    pub ssh_host: String,
    pub ssh_port: u32,
    pub ssh_key: String,
    pub username: String,
    pub password: String,
}
