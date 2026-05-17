use super::models::*;
use super::auth::ApiKeyStore;
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION};
use std::time::Duration;
use tokio::time::sleep;

const VASTAI_API_BASE: &str = "https://market.vast.ai/api/v0";

#[derive(Clone)]
pub struct VastAIClient {
    client: reqwest::Client,
}

impl VastAIClient {
    pub fn new() -> Self {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(30))
            .build()
            .expect("Failed to create HTTP client");
        VastAIClient { client }
    }

    async fn get(&self, path: &str, api_key: &str) -> Result<reqwest::Response, String> {
        let mut headers = HeaderMap::new();
        headers.insert(AUTHORIZATION, HeaderValue::from_str(&format!("Bearer {}", api_key)).map_err(|e| format!("Invalid API key format: {}", e))?);

        let url = format!("{}/{}", VASTAI_API_BASE, path);
        let response = self.client.get(&url)
            .headers(headers)
            .send()
            .await
            .map_err(|e| format!("Request failed: {}", e))?;

        if !response.status().is_success() {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            return Err(format!("API error (status {}): {}", status, body));
        }

        Ok(response)
    }

    pub async fn list_instances(&self, api_key: &str, filters: &InstanceFilters) -> Result<Vec<InstanceInfo>, String> {
        let mut query = String::from("type=open&order=pricePerHour&limit=100");

        if !filters.gpu_type.is_empty() {
            query.push_str(&format!("&q={}", urlencoding::encode(&filters.gpu_type)));
        }

        if filters.max_price > 0.0 {
            query.push_str(&format!("&maxPrice={}", filters.max_price));
        }

        if filters.instance_count > 0 {
            query.push_str(&format!("&numGpus={}", filters.instance_count));
        }

        let response = self.get(&format!("instances?{}", query), api_key).await?;
        let instances: Vec<InstanceInfo> = response.json().await
            .map_err(|e| format!("Failed to parse instances: {}", e))?;

        Ok(instances)
    }

    pub async fn get_instance_status(&self, api_key: &str, instance_id: &str) -> Result<InstanceInfo, String> {
        let response = self.get(&format!("instances/{}", instance_id), api_key).await?;
        let instance: InstanceInfo = response.json().await
            .map_err(|e| format!("Failed to parse instance: {}", e))?;

        Ok(instance)
    }

    pub async fn get_instance_status_with_retry(&self, api_key: &str, instance_id: &str, max_retries: u32, delay_secs: u64) -> Result<InstanceInfo, String> {
        let mut last_error = String::new();
        for _ in 0..max_retries {
            match self.get_instance_status(api_key, instance_id).await {
                Ok(instance) => return Ok(instance),
                Err(e) => {
                    last_error = e;
                    sleep(Duration::from_secs(delay_secs)).await;
                }
            }
        }
        Err(format!("Failed to get instance status after {} retries: {}", max_retries, last_error))
    }

    pub async fn create_instance(&self, api_key: &str, instance_id: &str) -> Result<CreateInstanceResponse, String> {
        // This is a simplified version - actual vast.ai API may differ
        let response = self.get(&format!("instances/{}/ssh", instance_id), api_key).await?;
        let ssh_info: CreateInstanceResponse = response.json().await
            .map_err(|e| format!("Failed to parse SSH info: {}", e))?;

        Ok(ssh_info)
    }
}
