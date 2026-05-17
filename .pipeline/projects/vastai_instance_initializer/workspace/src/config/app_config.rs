use serde::{Deserialize, Serialize};
use std::sync::Mutex;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub api_key: Mutex<Option<String>>,
}

impl AppConfig {
    pub fn new() -> Self {
        AppConfig {
            api_key: Mutex::new(None),
        }
    }

    pub fn set_api_key(&self, key: String) {
        let mut store = self.api_key.lock().unwrap();
        *store = Some(key);
    }

    pub fn get_api_key(&self) -> Option<String> {
        let store = self.api_key.lock().unwrap();
        store.clone()
    }
}
