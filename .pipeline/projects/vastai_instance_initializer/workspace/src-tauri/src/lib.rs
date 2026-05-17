pub mod config;
pub mod commands;
pub mod vastai_client;

use config::AppConfig;

pub fn run() {
  let config = AppConfig::load();
  println!("VAST AI Instance Manager started");
  println!("API Key configured: {}", config.vastai_api_key.is_some());
  println!("Presets: {}", config.presets.len());
}
