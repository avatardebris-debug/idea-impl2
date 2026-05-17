use serde::{Deserialize, Serialize};
use std::sync::Mutex;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiKeyStore {
    pub api_key: Mutex<Option<String>>,
}

impl ApiKeyStore {
    pub fn new() -> Self {
        ApiKeyStore {
            api_key: Mutex::new(None),
        }
    }

    pub fn set_key(&self, key: String) {
        let mut store = self.api_key.lock().unwrap();
        *store = Some(key);
    }

    pub fn get_key(&self) -> Option<String> {
        let store = self.api_key.lock().unwrap();
        store.clone()
    }

    pub fn is_set(&self) -> bool {
        let store = self.api_key.lock().unwrap();
        store.is_some()
    }
}
