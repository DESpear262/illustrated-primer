# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for building the Python backend executable.

This bundles the FastAPI backend server and all dependencies into a single
executable that can be distributed with the Tauri app.
"""

import sys
import os
from pathlib import Path

# Get project root - PyInstaller runs from the directory where it's invoked
# Since we run from project root, cwd is the project root
project_root = Path.cwd()

a = Analysis(
    [str(project_root / 'start_backend.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(project_root / 'src'), 'src'),
        (str(project_root / 'backend'), 'backend'),
    ],
    hiddenimports=[
        'uvicorn',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'fastapi.middleware',
        'fastapi.middleware.cors',
        'rich',
        'rich.console',
        'rich.table',
        'rich.panel',
        'rich.prompt',
        'rich.progress',
        'typer',
        'multipart',
        'pydantic',
        'openai',
        'faiss',
        'numpy',
        'networkx',
        'apscheduler',
        'tiktoken',
        'websockets',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='backend',
)

