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

def generate_leaflet_map_html(coordinates, extended_data, extended_data_locality_number, rotation_angle, zoom):
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


    if coordinates:
        lat_center = sum(float(coord[1].strip()) for coord in coordinates) / len(coordinates)
        lon_center = sum(float(coord[0].strip()) for coord in coordinates) / len(coordinates)
    else:
        lat_center = 0
        lon_center = 0

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


def save_temp_and_show_map_html_territorio(main_window, coordinates, extended_data, extended_data_locality_number, rotation_angle, zoom):    
    # Genera il contenuto HTML della mappa
    main_window.html_content_territorio = generate_leaflet_map_html(coordinates, extended_data, extended_data_locality_number, rotation_angle, zoom)
    
    if coordinates:
        lat_center = sum(float(coord[1].strip()) for coord in coordinates) / len(coordinates)
        lon_center = sum(float(coord[0].strip()) for coord in coordinates) / len(coordinates)
    else:
        lat_center = 0
        lon_center = 0

    
    # Salva il contenuto HTML temporaneamente
    appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp', 'territori', 'territorio_map.html')
    
    def save_file_and_load():
        try:
            with open(appdata_path, 'w') as file:
                file.write(main_window.html_content_territorio)
            main_window.web_view_territorio.setUrl(QUrl.fromLocalFile(appdata_path))
            main_window.kml_file_path_label.setText(f"File KML elaborato con successo")
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
    if success:
        QMessageBox.information(self, "Salvataggio Completato", f"File PDF salvato con successo in: {pdf_path}")
    else:
        QMessageBox.critical(self, "Errore", "Impossibile salvare il file PDF.")

