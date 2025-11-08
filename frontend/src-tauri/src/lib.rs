mod commands;

use commands::{start_backend, stop_backend, check_backend_status, BackendProcess};
use std::path::PathBuf;
use tauri::Manager;
use tauri_plugin_log::{Target, TargetKind};

fn resolve_log_dir() -> PathBuf {
  #[cfg(target_os = "windows")]
  {
    let base = std::env::var("APPDATA")
      .map(PathBuf::from)
      .or_else(|_| std::env::var("USERPROFILE").map(PathBuf::from))
      .unwrap_or_else(|_| PathBuf::from("."));
    return base.join("AI Tutor").join("logs");
  }

  #[cfg(target_os = "macos")]
  {
    return PathBuf::from(std::env::var("HOME").unwrap_or_default())
      .join("Library")
      .join("Application Support")
      .join("AI Tutor")
      .join("logs");
  }

  #[cfg(not(any(target_os = "windows", target_os = "macos")))]
  {
    return PathBuf::from(std::env::var("HOME").unwrap_or_default())
      .join(".local")
      .join("share")
      .join("AI Tutor")
      .join("logs");
  }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .setup(|app| {
      // Enable logging in both debug and release modes
      // Logs will be written to %APPDATA%\AI Tutor\logs\ on Windows
      let log_dir = resolve_log_dir();
      if let Err(e) = std::fs::create_dir_all(&log_dir) {
        eprintln!("Failed to create log directory {:?}: {}", log_dir, e);
      }
      let log_dir_display = log_dir.clone();

      let log_targets = [
        Target::new(TargetKind::Stdout),
        Target::new(TargetKind::Folder {
          path: log_dir,
          file_name: Some("app.log".into()),
        }),
        Target::new(TargetKind::Webview),
      ];

      app.handle().plugin(
        tauri_plugin_log::Builder::default()
          .clear_targets()
          .targets(log_targets)
          .level(log::LevelFilter::Info)
          .build(),
      )?;
      
      // Log startup message
      log::info!("AI Tutor application starting...");
      log::info!("Logging to {:?}", log_dir_display);

      // Initialize backend process state
      app.manage(BackendProcess::default());

      // Start backend on app startup if backend.exe exists
      let app_handle = app.handle().clone();
      tauri::async_runtime::spawn(async move {
        // Wait a moment for app to fully initialize
        tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
        
        // Try to start backend if backend.exe exists
        // Check common locations for the backend executable
        let backend_exe = if cfg!(windows) {
          let exe_path = std::env::current_exe()
            .ok()
            .and_then(|p| p.parent().map(|d| d.to_path_buf()));
          
          if let Some(exe_dir) = exe_path {
            let resource_path = exe_dir.join("resources").join("backend.exe");
            if resource_path.exists() {
              Some(resource_path)
            } else {
              let exe_path = exe_dir.join("backend.exe");
              if exe_path.exists() {
                Some(exe_path)
              } else {
                None
              }
            }
          } else {
            None
          }
        } else {
          None
        };
        
        if let Some(backend_exe) = backend_exe {
          log::info!("Found backend executable at: {:?}", backend_exe);
          // Backend executable exists, try to start it
          if let Some(state) = app_handle.try_state::<BackendProcess>() {
            match start_backend(app_handle.clone(), state).await {
              Ok(status) => {
                log::info!("Backend started automatically on port {}", status.port);
              }
              Err(e) => {
                log::error!("Failed to auto-start backend: {}", e);
              }
            }
          } else {
            log::error!("Could not access backend process state");
          }
        } else {
          log::warn!("Backend executable not found. Run 'python start_backend.py' separately for dev mode.");
        }
      });

      Ok(())
    })
    .invoke_handler(tauri::generate_handler![start_backend, stop_backend, check_backend_status])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
