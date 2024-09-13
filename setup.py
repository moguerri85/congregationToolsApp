from cx_Freeze import setup, Executable
import sys
import os

# Path to your script
script = "CongregationToolsApp.py"

# Include additional files like icons, templates, etc.
include_files = [
    # ('source_path', 'destination_path_in_build')
    ('./template', 'template'),  # Example of including a folder
]

# Setup configuration
build_exe_options = {
    'packages': ['PyQt5', 'PyQt5.QtWebEngineWidgets', 'PyQt5.QtWebEngineCore'],  # Include additional packages if necessary
    'include_files': include_files,
    'excludes': [],
}

# Base is set to None for console applications; change to "Win32GUI" if it's a GUI application without a console
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="CongregationToolsApp",
    version="1.0.1",
    description="CongregationToolsApp, estensione e personalizzazione di alcune funzionalità di Hourglass",
    options={"build_exe": build_exe_options},
    executables=[Executable(script, base=base)],
)
