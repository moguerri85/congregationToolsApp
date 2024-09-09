import os
import xml.etree.ElementTree as ET
from PyQt5.QtCore import QUrl, QTimer
from jinja2 import Template

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

def generate_leaflet_map_html(coordinates, extended_data):
    map_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mappa KML</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
        <style>
            #map { height: 100vh; }
            .custom-icon {
                background-color: yellow;
                border-radius: 3px;
                padding: 5px;
                display: block;
                text-align: center;
                line-height: 1.2;
                color: black;
                font-size: 12px;
                font-weight: bold;
                box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.5);
                max-width: 150px;
                width: 20px !important;
            }
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
        <script>
            var map = L.map('map').setView([{{ lat_center }}, {{ lon_center }}], 19);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19
            }).addTo(map);

            function createCustomIcon(text) {
                return L.divIcon({
                    className: 'custom-icon',
                    html: text
                });
            }

            // Aggiungi i poligoni alla mappa
            {% for polygon in polygons %}
                L.polygon({{ polygon }}, {color: 'blue', weight: 2}).addTo(map);
            {% endfor %}

            // Aggiungi solo le icone con il testo, senza marker visibili
            {% for coord, text in extended_data %}
                L.marker([{{ coord[0] }}, {{ coord[1] }}], {icon: createCustomIcon("{{ text }}")}).addTo(map);
            {% endfor %}
        </script>
    </body>
    </html>
    """

    # Calcola il centro della mappa
    if coordinates:
        lat_center = sum(float(coord[0].strip()) for coord in coordinates) / len(coordinates)
        lon_center = sum(float(coord[1].strip()) for coord in coordinates) / len(coordinates)
    else:
        lat_center = 0
        lon_center = 0

    # Converti i dati estesi in una lista di tuple per Jinja2
    extended_data_list = [((lat, lon), text) for (lat, lon), text in extended_data]

    # Converti le coordinate dei poligoni in formato GeoJSON
    # Assumiamo che ogni poligono sia una lista di coordinate
    polygons = []
    current_polygon = []
    for coord in coordinates:
        if len(current_polygon) > 0 and coord == coordinates[0]:  # Chiudi il poligono
            polygons.append(current_polygon)
            current_polygon = []
        current_polygon.append([float(coord[0]), float(coord[1])])
    if len(current_polygon) > 0:
        polygons.append(current_polygon)

    template = Template(map_template)
    html_content = template.render(coordinates=coordinates, lat_center=lat_center, lon_center=lon_center, extended_data=extended_data_list, polygons=polygons)
    return html_content


def save_and_show_map_html_territorio(main_window, coordinates, extended_data):
    html_content = generate_leaflet_map_html(coordinates, extended_data)
    appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp', 'territorio_map.html')

    def save_file_and_load():
        with open(appdata_path, 'w') as file:
            file.write(html_content)
        main_window.web_view_territorio.setUrl(QUrl.fromLocalFile(appdata_path))
        main_window.kml_file_path_label.setText(f"File KML elaborato con successo: {appdata_path}")

    QTimer.singleShot(0, save_file_and_load)
