import sys
import os
from cx_Freeze import setup, Executable

# Path to your script
script = "CongregationToolsApp.py"

# Get the absolute path to ensure correct file paths
def get_absolute_path(relative_path):
    return os.path.join(os.path.dirname(__file__), relative_path)

# Include additional files like icons, templates, etc.
include_files = [
    # ('source_path', 'destination_path_in_build')
    (get_absolute_path('template'), 'template'),  # Example of including a folder
    (get_absolute_path('ViGeo'), 'ViGeo'),  # Ensure ViGeo folder is included
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
    version="1.0.3",
    description="CongregationToolsApp, estensione e personalizzazione di alcune funzionalità di Hourglass",
    options={"build_exe": build_exe_options},
    executables=[Executable(script, base=base)],
)
