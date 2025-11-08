/**
 * Tauri commands for managing the Python backend server.
 * 
 * Provides functions to start and stop the backend process,
 * and check its status.
 */

use serde::{Deserialize, Serialize};
use std::io::{BufRead, BufReader};
use std::process::{Command, Stdio};
use std::sync::{Arc, Mutex};
use std::path::PathBuf;
use tauri::{AppHandle, State};

/// Backend process state stored in app
pub type BackendProcess = Arc<Mutex<Option<std::process::Child>>>;

#[derive(Debug, Serialize, Deserialize)]
pub struct BackendStatus {
    pub running: bool,
    pub port: u16,
}

/// Start the Python backend server
#[tauri::command]
pub async fn start_backend(
    _app_handle: AppHandle,
    state: State<'_, BackendProcess>,
) -> Result<BackendStatus, String> {
    // Check if already running
    {
        let process = state.lock().unwrap();
        if process.is_some() {
            return Ok(BackendStatus {
                running: true,
                port: 8000,
            });
        }
    }

    // Get backend executable path from resources
    // In bundled mode, resources are next to the executable
    // In dev mode, backend.exe should be in src-tauri/backend.exe
    let backend_exe = if cfg!(windows) {
        // Try to get the executable's directory
        let exe_path = std::env::current_exe()
            .ok()
            .and_then(|p| p.parent().map(|d| d.to_path_buf()));
        
        if let Some(exe_dir) = exe_path {
            // In bundled mode, resources are in a resources subdirectory
            let resource_path = exe_dir.join("resources").join("backend.exe");
            if resource_path.exists() {
                resource_path
            } else {
                // Fallback: try next to executable
                exe_dir.join("backend.exe")
            }
        } else {
            return Err("Could not determine executable directory".to_string());
        }
    } else {
        return Err("Non-Windows platforms not yet supported".to_string());
    };

    if !backend_exe.exists() {
        return Err(format!(
            "Backend executable not found at: {:?}. Make sure backend.exe is in the resources directory.",
            backend_exe
        ));
    }

    // Get app data directory - use standard OS app data locations
    let data_dir = if cfg!(windows) {
        let app_data = std::env::var("APPDATA")
            .map(PathBuf::from)
            .unwrap_or_else(|_| {
                std::env::var("USERPROFILE")
                    .map(PathBuf::from)
                    .unwrap_or_default()
            });
        app_data.join("AI Tutor").join("data")
    } else if cfg!(target_os = "macos") {
        PathBuf::from(std::env::var("HOME").unwrap_or_default())
            .join("Library")
            .join("Application Support")
            .join("AI Tutor")
            .join("data")
    } else {
        PathBuf::from(std::env::var("HOME").unwrap_or_default())
            .join(".local")
            .join("share")
            .join("AI Tutor")
            .join("data")
    };
    std::fs::create_dir_all(&data_dir)
        .map_err(|e| format!("Failed to create data dir: {}", e))?;

    log::info!("Starting backend from: {:?}", backend_exe);
    log::info!("Data directory: {:?}", data_dir);

    // Start backend process
    let mut child = Command::new(&backend_exe)
        .env("AI_TUTOR_DATA_DIR", data_dir.to_string_lossy().to_string())
        .env("TAURI_FAMILY", "1") // Signal that we're in Tauri
        .env("AI_TUTOR_BACKEND_RELOAD", "0") // Explicitly disable reload in bundle
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| {
            let err_msg = format!("Failed to start backend: {}", e);
            log::error!("{}", err_msg);
            err_msg
        })?;

    // Spawn tasks to capture and log backend output
    // Note: We'll read output in a background task
    let stdout = child.stdout.take();
    let stderr = child.stderr.take();
    
    if let Some(stdout) = stdout {
        let reader = BufReader::new(stdout);
        tokio::task::spawn_blocking(move || {
            for line in reader.lines() {
                match line {
                    Ok(line) => {
                        let trimmed = line.trim();
                        if !trimmed.is_empty() {
                            log::info!("[Backend] {}", trimmed);
                        }
                    }
                    Err(e) => {
                        log::error!("Error reading backend stdout: {}", e);
                        break;
                    }
                }
            }
        });
    }
    
    if let Some(stderr) = stderr {
        let reader = BufReader::new(stderr);
        tokio::task::spawn_blocking(move || {
            for line in reader.lines() {
                match line {
                    Ok(line) => {
                        let trimmed = line.trim();
                        if !trimmed.is_empty() {
                            // Check if it's an error or just info/warning
                            let upper = trimmed.to_uppercase();
                            if upper.contains("ERROR") || upper.contains("CRITICAL") || upper.contains("EXCEPTION") {
                                log::error!("[Backend] {}", trimmed);
                            } else if upper.contains("WARNING") || upper.contains("WARN") {
                                log::warn!("[Backend] {}", trimmed);
                            } else {
                                log::info!("[Backend] {}", trimmed);
                            }
                        }
                    }
                    Err(e) => {
                        log::error!("Error reading backend stderr: {}", e);
                        break;
                    }
                }
            }
        });
    }

    // Store process handle in app state
    {
        let mut process = state.lock().unwrap();
        *process = Some(child);
    }

    // Wait a moment for server to start, then check if it's still running
    tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;
    
    // Check if process is still alive
    {
        let mut process = state.lock().unwrap();
        if let Some(ref mut child) = *process {
            if let Ok(Some(status)) = child.try_wait() {
                return Err(format!("Backend process exited immediately with status: {:?}", status));
            }
        }
    }
    
    log::info!("Backend process started successfully");

    Ok(BackendStatus {
        running: true,
        port: 8000,
    })
}

/// Stop the Python backend server
#[tauri::command]
pub async fn stop_backend(state: State<'_, BackendProcess>) -> Result<(), String> {
    let mut process = state.lock().unwrap();
    if let Some(mut child) = process.take() {
        child.kill().map_err(|e| format!("Failed to stop backend: {}", e))?;
    }
    Ok(())
}

/// Check backend status
#[tauri::command]
pub async fn check_backend_status(state: State<'_, BackendProcess>) -> Result<BackendStatus, String> {
    let mut process = state.lock().unwrap();
    if let Some(ref mut child) = *process {
        // Check if process is still running
        match child.try_wait() {
            Ok(Some(status)) => {
                log::warn!("Backend process has exited with status: {:?}", status);
                Ok(BackendStatus {
                    running: false,
                    port: 8000,
                })
            }
            Ok(None) => {
                Ok(BackendStatus {
                    running: true,
                    port: 8000,
                })
            }
            Err(e) => {
                let err_msg = format!("Error checking backend status: {}", e);
                log::error!("{}", err_msg);
                Err(err_msg)
            }
        }
    } else {
        Ok(BackendStatus {
            running: false,
            port: 8000,
        })
    }
}

