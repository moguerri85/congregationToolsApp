import os
import xml.etree.ElementTree as ET
from PyQt5.QtCore import QUrl, QTimer
from jinja2 import Environment, FileSystemLoader
import json
from PyQt5.QtWidgets import QMessageBox


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


def save_temp_and_show_map_html_territorio(self, coordinates, extended_data, extended_data_locality_number, rotation_angle, zoom, center_lat, center_lon):    
    # Genera il contenuto HTML della mappa
    self.html_content_territorio = generate_leaflet_map_html(coordinates, extended_data, extended_data_locality_number, rotation_angle, zoom, center_lat, center_lon)
    
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

    
    # Salva il contenuto HTML temporaneamente
    appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp', 'territori', 'territorio_map.html')
    
    def save_file_and_load():
        try:
            with open(appdata_path, 'w') as file:
                file.write(self.html_content_territorio)
            self.web_view_territorio.setUrl(QUrl.fromLocalFile(appdata_path))
            self.kml_file_path_label.setText(f"File KML elaborato con successo")
            update_html_file_list(self)

        except Exception as e:
            print(f"Errore durante il caricamento della mappa: {e}")

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
        
def handle_print_result(self, success, pdf_path):
    if self.save_map:
        if success:
            QMessageBox.information(self, "Salvataggio Completato", f"File PDF salvato con successo in: {pdf_path}")
        else:
            QMessageBox.critical(self, "Errore", "Impossibile salvare il file PDF.")

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
                print(f"Error parsing coordinates: {e}")
        else:
            print("No result returned from JavaScript.")

    # Execute JavaScript and get the result
    self.web_view_territorio.page().runJavaScript(js_code, handle_new_center)

    