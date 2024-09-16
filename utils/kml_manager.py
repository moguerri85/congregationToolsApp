import os
import xml.etree.ElementTree as ET
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QTimer, QUrl
from PyQt5.QtWidgets import QFileDialog
from jinja2 import Environment, FileSystemLoader

def open_kml_file_dialog_territorio(self):
    from utils.ui_territorio import toggle_spinners_territorio
    file_path, _ = QFileDialog.getOpenFileName(
        self,                # 'self' è l'istanza della finestra principale (QWidget)
        "Seleziona file KML", # Titolo della finestra di dialogo
        "",                  # Directory predefinita (può essere lasciato vuoto)
        "KML Files (*.kml)"  # Filtro per i file
    )
    
    if file_path:
        # Aggiorna il percorso del file KML selezionato nella QLabel
        self.kml_file_path_label.setText(f"File KML selezionato: {file_path}")

        # Inizializza le variabili
        self.coordinates = []
        self.extended_data = []
        self.extended_data_locality_number = []
        self.center_lat = None
        self.center_lon = None
        
        # Processa il file KML e genera la mappa
        self.coordinates = process_kml_file_territorio_coordinates(file_path)
        self.extended_data = process_kml_file_territorio_ext_data(file_path)
        self.extended_data_locality_number = process_kml_file_territorio_locality_number(file_path)
        rotation_angle = 0  # Lo inizializzo a 0
        zoom = 18
        if self.coordinates:
            save_temp_and_show_map_html_territorio(
                self,
                self.coordinates,
                self.extended_data,
                self.extended_data_locality_number,
                rotation_angle,
                zoom,
                self.center_lat,
                self.center_lon
            )
        self.kml_loaded = True  # Imposta il flag come caricato
        toggle_spinners_territorio(self, True)  # Abilita gli spinner
    else:
        self.kml_loaded = False  # In caso di fallimento o annullamento
        toggle_spinners_territorio(self, False)  # Disabilita gli spinner


def process_kml_file_territorio_coordinates(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Namespace del KML
    namespace = {'kml': 'http://www.opengis.net/kml/2.2'}

    coordinates = []

    for placemark in root.findall('.//kml:Placemark', namespace):
        polygon = placemark.find('.//kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates', namespace)
        if polygon is not None:
            coords_text = polygon.text.strip()
            coords_list = coords_text.split()  # Dividi per spazi
            for coord in coords_list:
                parts = coord.split(',')  # Dividi per virgole
                if len(parts) >= 2:
                    lon, lat = parts[:2]
                    coordinates.append([lat.strip(), lon.strip()])

    return coordinates

def process_kml_file_territorio_ext_data(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Namespace del KML
    namespace = {'kml': 'http://www.opengis.net/kml/2.2'}

    extended_data = []

    for placemark in root.findall('.//kml:Placemark', namespace):
        extended_data_node = placemark.find('.//kml:ExtendedData', namespace)
        if extended_data_node is not None:
            text_data = None
            for data in extended_data_node.findall('.//kml:Data', namespace):
                name = data.get('name')
                value = data.find('.//kml:value', namespace)
                if name == 'text' and value is not None:
                    text_data = value.text.strip()  # Assicurati che il testo sia ben formattato
                    break
            if text_data is not None:
                coord_node = placemark.find('.//kml:coordinates', namespace)
                if coord_node is not None:
                    coords = coord_node.text.strip().split()
                    for coord in coords:
                        parts = coord.split(',')
                        if len(parts) >= 2:
                            lon, lat = parts[:2]
                            extended_data.append(((lat.strip(), lon.strip()), text_data))

    return extended_data

def process_kml_file_territorio_locality_number(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Namespace del KML
    namespace = {'kml': 'http://www.opengis.net/kml/2.2'}

    extended_data_locality_number = []

    for placemark in root.findall('.//kml:Placemark', namespace):
        extended_data_node = placemark.find('.//kml:ExtendedData', namespace)
        if extended_data_node is not None:
            text_data = None
            for data in extended_data_node.findall('.//kml:Data', namespace):
                name = data.get('name')
                value = data.find('.//kml:value', namespace)
                if name == 'number' and value is not None:
                    text_data = value.text.strip()  # Assicurati che il testo sia ben formattato
                    extended_data_locality_number.append(text_data)
                if name == 'locality' and value is not None:
                    text_data = value.text.strip()  # Assicurati che il testo sia ben formattato
                    extended_data_locality_number.append(text_data)

    return extended_data_locality_number
        
def save_map_to_folder(self):
    """Salva la mappa HTML e convertila in PDF."""
    if not self.save_map:
        return

    default_folder = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp', 'territori')
    if not os.path.exists(default_folder):
        os.makedirs(default_folder)

    if not self.html_content_territorio:
        QMessageBox.warning(self, "Attenzione", "Nessun contenuto HTML da salvare.")
        return

    file_name = self.extended_data_locality_number[1] + "_" + self.extended_data_locality_number[0] + ".html"
    file_path = os.path.join(default_folder, file_name)

    if file_name:
        try:
            pdf_path, _ = QFileDialog.getSaveFileName(self, "Salva Mappa come PDF", default_folder, "PDF Files (*.pdf)")

            if pdf_path:
                with open(file_path, 'w') as file:
                    file.write(self.html_content_territorio)

                def save_pdf_to_file(data):
                    try:
                        with open(pdf_path, 'wb') as f:
                            f.write(data)
                    except Exception as e:
                        QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio del PDF: {e}")

                def on_load_finished():
                    QTimer.singleShot(1000, lambda: page.printToPdf(save_pdf_to_file))

                page = self.web_view_territorio.page()
                page.loadFinished.connect(on_load_finished)
                self.web_view_territorio.setUrl(QUrl.fromLocalFile(file_path))
                update_html_file_list(self)
                handle_print_result(self, True, pdf_path)  # Chiamata alla funzione di successo
                self.save_map = False
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio del file HTML: {e}")

def handle_print_result(self, success, pdf_path):
    if self.save_map:
        if success:
            QMessageBox.information(self, "Salvataggio Completato", f"File PDF salvato con successo in: {pdf_path}")
        else:
            QMessageBox.critical(self, "Errore", "Impossibile salvare il file PDF.")

def update_map(self):
    angle = self.rotation_spinner.value()
    zoom = self.zoom_spinner.value()
    # Carica e aggiorna la mappa con la rotazione
    save_temp_and_show_map_html_territorio(self, self.coordinates, self.extended_data, self.extended_data_locality_number, angle, zoom, self.center_lat, self.center_lon)

def save_temp_and_show_map_html_territorio(self, coordinates, extended_data, extended_data_locality_number, rotation_angle, zoom, center_lat, center_lon):
    # Genera il contenuto HTML della mappa
    try:
        self.html_content_territorio = generate_leaflet_map_html(coordinates, extended_data, extended_data_locality_number, rotation_angle, zoom, center_lat, center_lon)
    except Exception as e:
        QMessageBox.critical(self, "Errore", f"Errore nella generazione della mappa: {e}")
        return

    # Calcola il centro della mappa se non fornito
    if center_lat is None and center_lon is None:
        if coordinates:
            lat_center = sum(float(coord[1].strip()) for coord in coordinates) / len(coordinates)
            lon_center = sum(float(coord[0].strip()) for coord in coordinates) / len(coordinates)
        else:
            lat_center = 0
            lon_center = 0
    else:
        lat_center = center_lat
        lon_center = center_lon

    # Salva il contenuto HTML temporaneamente
    appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp', 'territori', 'territorio_map.html')

    def save_file_and_load():
        try:
            with open(appdata_path, 'w') as file:
                file.write(self.html_content_territorio)
            self.web_view_territorio.setUrl(QUrl.fromLocalFile(appdata_path))
            self.kml_file_path_label.setText("File KML elaborato con successo")
            update_html_file_list(self)
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante il caricamento della mappa: {e}")

    QTimer.singleShot(0, save_file_and_load)

def update_html_file_list(self):
    # Percorso della cartella 'territori'
    territori_folder = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp', 'territori')

    # Recupera la lista dei file HTML nella cartella
    try:
        html_files = [f for f in os.listdir(territori_folder) if f.endswith('.html')]

        # Supponendo che tu abbia un QListWidget chiamato `html_file_list`
        self.html_file_list.clear()
        self.html_file_list.addItems(html_files)
    except Exception as e:
        QMessageBox.critical(self, "Errore", f"Errore durante l'aggiornamento della lista dei file: {e}")

def generate_leaflet_map_html(coordinates, extended_data, extended_data_locality_number, rotation_angle, zoom, center_lat, center_lon):
     # Percorso del template nella directory template di AppData
    template_dir = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp', 'template')
    
    if not os.path.isdir(template_dir):
        raise FileNotFoundError(f"La directory dei template non è stata trovata: {template_dir}")

    env = Environment(loader=FileSystemLoader(template_dir, encoding='utf-8'))
    
    # Nome del template
    template_name = 'template_territorio.html'
    
    try:
        template = env.get_template(template_name)
    except Exception as e:
        raise FileNotFoundError(f"Impossibile caricare il template: {template_name}. Errore: {e}")

    if center_lat  is None and center_lon is None:
        if coordinates:
            lat_center = sum(float(coord[1].strip()) for coord in coordinates) / len(coordinates)
            lon_center = sum(float(coord[0].strip()) for coord in coordinates) / len(coordinates)
        else:
            lat_center = 0
            lon_center = 0
    else:
            lat_center = center_lat
            lon_center = center_lon


    extended_data_list = [((lon, lat), text) for (lat, lon), text in extended_data]

    # Converti le coordinate dei poligoni in formato GeoJSON
    polygons = []
    current_polygon = []
    for coord in coordinates:
        if len(current_polygon) > 0 and coord == coordinates[0]:  # Chiudi il poligono
            polygons.append(current_polygon)
            current_polygon = []
        current_polygon.append([float(coord[1]), float(coord[0])])
    if len(current_polygon) > 0:
        polygons.append(current_polygon)

    html_content_territorio = template.render(
        coordinates=coordinates,
        lat_center=lat_center,
        lon_center=lon_center,
        extended_data=extended_data_list,
        extended_data_locality_number = extended_data_locality_number,
        polygons=polygons,
        rotation_angle=rotation_angle,
        zoom=zoom
    )
    return html_content_territorio
