from PyQt5.QtWidgets import QListWidgetItem, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpinBox, QDoubleSpinBox, QListWidget, QGridLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl
import os
from utils.kml_manager import save_temp_and_show_map_html_territorio
from utils.logging_custom import logging_custom


def setup_territorio_tab(self):
    # Inizializza i dati e variabili
    self.kml_loaded = False
    self.coordinates = []
    self.extended_data = []
    self.extended_data_locality_number = []
    self.html_content_territorio = ""
    self.center_lat = None
    self.center_lon = None
    self.save_map = False

    # Crea il widget principale per il tab
    self.territorio_tab = QWidget()
    
    # Layout verticale principale
    vertical_layout = QVBoxLayout(self.territorio_tab)

    # Layout per i pulsanti
    button_layout = QHBoxLayout()
    button_layout.setAlignment(Qt.AlignCenter)
    
    select_kml_button = QPushButton("Seleziona file KML", self.territorio_tab)
    select_kml_button.clicked.connect(self.openKML)
    button_layout.addWidget(select_kml_button)
    
    self.save_map_button = QPushButton("Salva Cartolina", self.territorio_tab)
    self.save_map_button.setEnabled(False)
    self.save_map_button.clicked.connect(self.call_save_map_to_folder)
    button_layout.addWidget(self.save_map_button)
    
    vertical_layout.addLayout(button_layout)

    # Layout per rotazione e zoom
    button_operazione_layout = QHBoxLayout()
    button_operazione_layout.setAlignment(Qt.AlignCenter)
    
    rotation_layout = QHBoxLayout()
    rotation_label = QLabel("Rotazione:", self.territorio_tab)
    rotation_layout.addWidget(rotation_label)
    self.rotation_spinner = QSpinBox(self.territorio_tab)
    self.rotation_spinner.setRange(-360, 360)
    self.rotation_spinner.setValue(0)
    self.rotation_spinner.valueChanged.connect(self.call_update_map)
    self.rotation_spinner.setEnabled(False)
    rotation_layout.addWidget(self.rotation_spinner)
    button_operazione_layout.addLayout(rotation_layout)
    
    zoom_layout = QHBoxLayout()
    zoom_label = QLabel("Zoom:", self.territorio_tab)
    zoom_layout.addWidget(zoom_label)
    self.zoom_spinner = QDoubleSpinBox(self.territorio_tab)
    self.zoom_spinner.setRange(1.0, 25.0)
    self.zoom_spinner.setValue(18.0)
    self.zoom_spinner.setSingleStep(0.1)
    self.zoom_spinner.valueChanged.connect(self.call_update_map)
    self.zoom_spinner.setEnabled(False)
    zoom_layout.addWidget(self.zoom_spinner)
    button_operazione_layout.addLayout(zoom_layout)
    
    # Layout per le frecce direzionali
    arrow_layout = QGridLayout()
    self.up_button = QPushButton("↑", self.territorio_tab)
    self.up_button.setEnabled(False)
    self.up_button.clicked.connect(lambda: move_map(self, "up"))
    self.down_button = QPushButton("↓", self.territorio_tab)
    self.down_button.setEnabled(False)
    self.down_button.clicked.connect(lambda: move_map(self, "down"))
    self.left_button = QPushButton("←", self.territorio_tab)
    self.left_button.setEnabled(False)
    self.left_button.clicked.connect(lambda: move_map(self, "left"))
    self.right_button = QPushButton("→", self.territorio_tab)
    self.right_button.setEnabled(False)
    self.right_button.clicked.connect(lambda: move_map(self, "right"))
    
    arrow_layout.addWidget(self.up_button, 0, 1)
    arrow_layout.addWidget(self.left_button, 1, 0)
    arrow_layout.addWidget(self.right_button, 1, 2)
    arrow_layout.addWidget(self.down_button, 2, 1)
    
    button_operazione_layout.addLayout(arrow_layout)
    vertical_layout.addLayout(button_operazione_layout)

    # Label per il percorso del file KML
    self.kml_file_path_label = QLabel("Nessun file KML selezionato", self.territorio_tab)
    vertical_layout.addWidget(self.kml_file_path_label)

    # Layout principale orizzontale per QWebEngineView e QListWidget
    main_layout = QHBoxLayout()

    # Inizializzazione del QWebEngineView
    self.web_view_territorio = QWebEngineView(self.territorio_tab)
    window_size = self.size()
    self.web_view_territorio.setFixedSize(int(window_size.width() * 0.75), int(window_size.height() * 0.75))
    main_layout.addWidget(self.web_view_territorio)

    # Lista dei file HTML
    self.html_file_list = QListWidget(self.territorio_tab)
    self.html_file_list.setFixedSize(int(window_size.width() * 0.25), int(window_size.height() * 0.75))
    self.html_file_list.itemClicked.connect(self.call_load_html_file_from_list)
    populate_html_file_list(self)
    main_layout.addWidget(self.html_file_list)

    # Aggiungi layout principale al layout verticale
    vertical_layout.addLayout(main_layout)

    # Imposta il widget del tab
    self.tabs.addTab(self.territorio_tab, "Cartoline per Territori")

def toggle_spinners_territorio(self, enabled):
    """Abilita o disabilita i controlli della mappa (rotazione, zoom, frecce)."""
    self.rotation_spinner.setEnabled(enabled)
    self.zoom_spinner.setEnabled(enabled)
    self.save_map_button.setEnabled(enabled)
    self.up_button.setEnabled(enabled)
    self.down_button.setEnabled(enabled)
    self.left_button.setEnabled(enabled)
    self.right_button.setEnabled(enabled)

def populate_html_file_list(self):
    """Popola la lista dei file HTML nella cartella 'territori'."""
    appdata_folder = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp', 'territori')
    if os.path.exists(appdata_folder):
        html_files = [f for f in os.listdir(appdata_folder) if f.endswith('.html')]
        self.html_file_list.clear()
        for file_name in html_files:
            item = QListWidgetItem(file_name)
            self.html_file_list.addItem(item)
    else:
        os.makedirs(appdata_folder)

def load_html_file_from_list(self, item):
    """Carica un file HTML dalla lista e disabilita i controlli se non è la mappa corrente."""
    self.save_map = False
    file_name = item.text()
    appdata_folder = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp', 'territori')
    file_path = os.path.join(appdata_folder, file_name)
    self.web_view_territorio.setUrl(QUrl.fromLocalFile(file_path))
    toggle_spinners_territorio(self, file_name == "territorio_map.html")

def move_map(self, direction):

    move_distance = 10  # Distance to move in map units (OpenLayers uses EPSG:3857)

    # JavaScript code to move the map and get the new center in EPSG:3857
    js_code = f"""
    var view = map.getView();
    var current_center = view.getCenter();
    var move_distance = {move_distance};

    // Calculate new center based on direction
    var new_center;
    if ("{direction}" === "up") {{
        new_center = [current_center[0], current_center[1] - move_distance];
    }} else if ("{direction}" === "down") {{
        new_center = [current_center[0], current_center[1] + move_distance];
    }} else if ("{direction}" === "left") {{
        new_center = [current_center[0] + move_distance, current_center[1]];
    }} else if ("{direction}" === "right") {{
        new_center = [current_center[0] - move_distance, current_center[1]];
    }}

    // Convert new center to EPSG:4326
    var new_center_wgs84 = ol.proj.transform(new_center, 'EPSG:3857', 'EPSG:4326');

    // Return the new center in EPSG:4326 as a comma-separated string
    new_center_wgs84.join(',');
    """

    # Callback function to handle the new center coordinates
    def handle_new_center(result):
        if result:  # Check if result is not None
            # result contains the new center coordinates in EPSG:4326 as a comma-separated string
            try:
                center_lat, center_lon = map(float, result.split(','))
                # Update the map with the new center
                angle = self.rotation_spinner.value()
                zoom = self.zoom_spinner.value()
                save_temp_and_show_map_html_territorio(self, self.coordinates, self.extended_data, self.extended_data_locality_number, angle, zoom, center_lat, center_lon)
            except ValueError as e:
                logging_custom(self, "debug", f"Error parsing coordinates: {e}")
        else:
            logging_custom(self, "debug", "No result returned from JavaScript.")

    # Execute JavaScript and get the result
    self.web_view_territorio.page().runJavaScript(js_code, handle_new_center)

        