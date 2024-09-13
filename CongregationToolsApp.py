import sys
import platform
import os

from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QTabWidget, QPushButton, QMessageBox, QLineEdit, QProgressBar, QLabel, QFileDialog, QDoubleSpinBox, QSpinBox, QListWidget, QListWidgetItem, QGridLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PyQt5.QtCore import QUrl, QEventLoop, QTimer, Qt, QObject, QEvent
from PyQt5.QtGui import QPainter, QColor

from utils.av_uscieri import combine_html_av_uscieri, retrieve_content_av_uscieri
from utils.infra_settimanale import combine_html_infrasettimale, click_toggle_js_infraSettimanale, click_expand_js_infraSettimanale, retrieve_content_infraSettimanale
from utils.fine_settimana import combine_html_fine_settimana
from utils.update_software import check_for_updates
from utils.pulizie import combine_html_pulizie, retrieve_content_pulizie
from utils.testimonianza_pubblica import combine_html_testimonianza_pubbl, retrieve_content_testimonianza_pubbl, click_toggle_js_testimonianza_pubbl
from utils.utility import show_alert, save_html, addProgressbar, clear_existing_widgets, ensure_folder_appdata
from utils.territorio import handle_print_result, save_temp_and_show_map_html_territorio, process_kml_file_territorio_coordinates, process_kml_file_territorio_ext_data, process_kml_file_territorio_locality_number, update_html_file_list, move_map


CURRENT_VERSION = "1.0.1"  # Versione corrente dell'app
GITHUB_RELEASES_API_URL = "https://api.github.com/repos/moguerri85/congregationToolsApp/releases/latest"


class CustomWebEngineView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.page().profile().setRequestInterceptor(self)

    def interceptRequest(self, request):
        print("Richiesta intercettata:", request.requestUrl())
        
# Interceptor per le richieste
class RequestInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        url = info.requestUrl().toString()
        print(f"Intercepted request to: {url}")
        info.block(False)

# Widget di overlay
class OverlayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(255, 255, 255, 0.8);")
        self.setGeometry(parent.rect())
        self.setVisible(False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 255, 255, 128))

# Applicazione principale
class CongregationToolsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scra - ViGeo")
        self.setGeometry(100, 100, 800, 500)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Aggiungi l'overlay
        self.overlay = OverlayWidget(self)

        # Aggiungi QTabWidget per gestire i tab
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Tab per Hourglass
        self.web_tab = QWidget()
        self.web_layout = QVBoxLayout(self.web_tab)
        self.view = QWebEngineView()
        self.web_layout.addWidget(self.view)
        self.web_tab.setLayout(self.web_layout)  # Imposta il layout del tab
        self.tabs.addTab(self.web_tab, "Hourglass")
        
        self.load_page("https://app.hourglass-app.com/v2/page/app/scheduling/")
        # Connette i segnali di navigazione alla funzione di gestione
        self.view.urlChanged.connect(self.call_page)

        # Tab per Cartoline per Territori
        self.cartoline_tab = QWidget()
        self.cartoline_layout = QVBoxLayout(self.cartoline_tab)
        
        self.cartoline_tab.setLayout(self.cartoline_layout)  # Imposta il layout del tab
        self.tabs.addTab(self.cartoline_tab, "Cartoline per Territori")

        # Tab per ViGeo
        self.local_html_view = QWebEngineView()
        interceptor = RequestInterceptor()
        self.local_html_view.page().profile().setRequestInterceptor(interceptor)
        self.local_tab = QWidget()
        self.local_layout = QVBoxLayout(self.local_tab)
        self.local_layout.addWidget(self.local_html_view)
        self.local_tab.setLayout(self.local_layout)  # Imposta il layout del tab
        self.tabs.addTab(self.local_tab, "ViGeo")

        # Imposta l'interceptor per monitorare le richieste di rete
        interceptor = RequestInterceptor()
        QWebEngineProfile.defaultProfile().setRequestInterceptor(interceptor)

        self.load_local_ViGeo()
        self.setup_territorio()

        # Controlla aggiornamenti all'avvio
        message_update = ""
        message_update = check_for_updates(CURRENT_VERSION, GITHUB_RELEASES_API_URL)
        self.statusBar().showMessage(message_update)

        # Disable the ViGeo tab
        vigeo_index = self.tabs.indexOf(self.local_tab)
        if vigeo_index != -1:
            self.tabs.setTabEnabled(vigeo_index, False)

    def load_page(self, url):
        self.view.setUrl(QUrl(url))

    def call_page(self, url):
        self.__dict__.pop('content', None)
        url = self.view.url().toString() 
        
        clear_existing_widgets(self)
        
        if "/scheduling/wm" in url:
            self.setup_weekend()
        elif "/scheduling/mm" in url:
            self.setup_infra_week()
        elif "/scheduling/avattendant" in url:
            self.setup_av_attendant()
        elif "/scheduling/cleaning" in url:
            self.setup_cleaning()
        elif "/scheduling/manageGroups" in url:
            self.setup_groups()
        elif "/scheduling/publicWitnessing" in url:       
            self.setup_testimonianza_pubblica()           
        else:
            self.statusBar().showMessage("")

    def setup_territorio(self):        
        self.kml_loaded = False  # Indica se un file KML è stato caricato
        self.coordinates= []
        self.extended_data= []
        self.extended_data_locality_number= []

        self.kml_data = None
        self.html_content_territorio = ""

        # Inizializza il layout verticale principale
        self.vertical_layout = QVBoxLayout()

        # Inizializza la QLabel per la mappa
        self.map_view = QLabel("Cartolina qui")
        self.vertical_layout.addWidget(self.map_view)  # Aggiungi al layout verticale

        # Crea un layout orizzontale per i pulsanti
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)  # Center-align 

        # Aggiungi pulsante per selezionare file KML
        select_kml_button = QPushButton("Seleziona file KML", self)
        select_kml_button.clicked.connect(self.open_kml_file_dialog_territorio)
        button_layout.addWidget(select_kml_button)

        # Aggiungi pulsante per salvare la mappa
        self.save_map_button = QPushButton("Salva Cartolina", self)
        self.save_map_button.setEnabled(False)  # Disabilita all'inizio
        self.save_map_button.clicked.connect(self.save_map_to_folder)
        button_layout.addWidget(self.save_map_button)

        self.vertical_layout.addLayout(button_layout)

        # Layout per i controlli di rotazione e zoom
        button_operazione_layout = QHBoxLayout()
        button_operazione_layout.setAlignment(Qt.AlignCenter)  # Center-align 

        # Layout per il controllo di rotazione
        rotation_layout = QHBoxLayout()
        rotation_label = QLabel("Rotazione:")
        rotation_layout.addWidget(rotation_label)
        self.rotation_spinner = self.create_spinner_territorio(-360, 360, 0, self.update_map)
        self.rotation_spinner.setEnabled(False)  # Disabilita all'inizio
        rotation_layout.addWidget(self.rotation_spinner)
        button_operazione_layout.addLayout(rotation_layout)

        # Layout per il controllo di zoom
        zoom_layout = QHBoxLayout()
        zoom_label = QLabel("Zoom:")
        zoom_layout.addWidget(zoom_label)
        self.zoom_spinner = self.create_double_spinner_territorio(1.0, 25.0, 18.0, 0.1, self.update_map)
        self.zoom_spinner.setEnabled(False)  # Disabilita all'inizio
        zoom_layout.addWidget(self.zoom_spinner)
        button_operazione_layout.addLayout(zoom_layout)

        # Layout per le frecce direzionali
        arrow_layout = QGridLayout()
        
        # Frecce di spostamento
        self.up_button = QPushButton("↑", self)
        self.up_button.setEnabled(False)
        self.up_button.clicked.connect(lambda: move_map(self, "up"))
        
        self.down_button = QPushButton("↓", self)
        self.down_button.setEnabled(False)
        self.down_button.clicked.connect(lambda: move_map(self, "down"))
        
        self.left_button = QPushButton("←", self)
        self.left_button.setEnabled(False)
        self.left_button.clicked.connect(lambda: move_map(self, "left"))
        
        self.right_button = QPushButton("→", self)
        self.right_button.setEnabled(False)
        self.right_button.clicked.connect(lambda: move_map(self, "right"))
        
        # Posiziona i pulsanti nel layout a croce
        arrow_layout.addWidget(self.up_button, 0, 1)
        arrow_layout.addWidget(self.left_button, 1, 0)
        arrow_layout.addWidget(self.right_button, 1, 2)
        arrow_layout.addWidget(self.down_button, 2, 1)
        
        # Aggiungi il layout delle frecce al layout delle operazioni
        button_operazione_layout.addLayout(arrow_layout)
        
        self.vertical_layout.addLayout(button_operazione_layout)

        # Aggiungi una QLabel per mostrare il percorso del file KML selezionato
        self.kml_file_path_label = QLabel("Nessun file KML selezionato")
        self.vertical_layout.addWidget(self.kml_file_path_label)

        # Crea un layout orizzontale principale
        main_layout = QHBoxLayout()

        # Inizializzazione del QWebEngineView
        self.web_view_territorio = QWebEngineView()
        window_size = self.size()
        self.web_view_territorio.setFixedSize(int(window_size.width() * 0.75), int(window_size.height() * 0.75))
        
        main_layout.addWidget(self.web_view_territorio)

        
        # Crea una lista per visualizzare i file HTML nella cartella "territori"
        self.html_file_list = QListWidget()
        self.html_file_list.setFixedSize(int(window_size.width() * 0.25), int(window_size.height() * 0.75))
        self.html_file_list.itemClicked.connect(self.load_html_file_from_list)
        self.populate_html_file_list()  # Popola la lista con i file HTML
        main_layout.addWidget(self.html_file_list)

        # Aggiungi il layout orizzontale principale al layout verticale
        self.vertical_layout.addLayout(main_layout)

        # Assicurati che cartoline_layout sia inizializzato
        if not hasattr(self, 'cartoline_layout'):
            self.cartoline_layout = QVBoxLayout()
        
        # Aggiungi il layout verticale principale al layout principale
        self.cartoline_layout.addLayout(self.vertical_layout)

        # Imposta il layout principale della finestra
        self.setLayout(self.cartoline_layout)

    def setup_weekend(self):
        self.horizontal_layout = QHBoxLayout()
        self.add_button("Genera Stampa Fine Settimana", self.load_schedule_fineSettimana)
        # Aggiungi il layout orizzontale al layout principale
        self.web_layout.addLayout(self.horizontal_layout)

    def setup_infra_week(self):
        # Creiamo un layout orizzontale per contenere il QLineEdit e il QPushButton
        self.horizontal_layout = QHBoxLayout()
        self.add_text_field("Numero di settimane:")
        self.add_button("Genera Stampa Infrasettimanale", lambda: self.load_schedule_infraSettimanale(self.text_field))

        # Aggiungi il layout orizzontale al layout principale
        self.web_layout.addLayout(self.horizontal_layout)

    def setup_av_attendant(self):
        self.horizontal_layout = QHBoxLayout()
        self.add_text_field("Numero di mesi:")
        self.add_button("Genera Stampa Incarchi", lambda: self.load_schedule_av_uscieri(self.text_field))
        self.web_layout.addLayout(self.horizontal_layout)

    def setup_cleaning(self):
        self.horizontal_layout = QHBoxLayout()
        self.add_text_field("Numero di mesi:")
        self.add_button("Genera Stampa Pulizie", lambda: self.load_schedule_pulizie(self.text_field))
        self.web_layout.addLayout(self.horizontal_layout)

    def setup_groups(self):
        self.add_button("Genera Stampa Gruppo di Servizio", self.load_schedule_gruppi_servizio)

    def setup_testimonianza_pubblica(self):
        self.horizontal_layout = QHBoxLayout()
        self.add_text_field("Numero di mesi:")
        self.add_button("Genera Stampa Testimonianza Pubblica", lambda: self.load_schedule_testimonianza_pubblica(self.text_field))
        self.web_layout.addLayout(self.horizontal_layout)

    def create_spinner_territorio(self, min_value, max_value, initial_value, callback):
        spinner = QSpinBox()
        spinner.setRange(min_value, max_value)
        spinner.setValue(initial_value)
        spinner.valueChanged.connect(callback)
        return spinner

    def create_double_spinner_territorio(self, min_value, max_value, initial_value, step, callback):
        spinner = QDoubleSpinBox()
        spinner.setRange(min_value, max_value)
        spinner.setValue(initial_value)
        spinner.setSingleStep(step)
        spinner.valueChanged.connect(callback)
        return spinner
    
    def add_text_field(self, placeholder_text):
        # Crea un QLineEdit e aggiungilo al layout orizzontale
        self.text_field = QLineEdit()
        self.text_field.setPlaceholderText(placeholder_text)
        self.text_field.setFixedWidth(200)
        self.text_field.setFixedHeight(30)
        self.horizontal_layout.addWidget(self.text_field)  # Aggiungi al layout orizzontale

    def add_button(self, text, slot):
        # Crea un QPushButton e aggiungilo al layout orizzontale
        button = QPushButton(text)
        button.setFixedWidth(200)
        button.setFixedHeight(30)
        button.clicked.connect(slot)
        self.horizontal_layout.addWidget(button)  # Aggiungi al layout orizzontale

    def load_schedule_infraSettimanale(self, text_field):
        addProgressbar(self)
        self.progress_bar.setValue(10)  # Imposta il progresso al 10%

        # Array per memorizzare i contenuti
        self.content_array = []

        # Recupera il numero dal campo di testo
        try:
            numero_settimana = int(text_field.text())
            if numero_settimana <= 0:
                raise ValueError("Il numero deve essere positivo")
        except ValueError:
            show_alert("Inserisci un numero valido e positivo!")
            # Rimuovi tutti i QPushButton dal layout
            for widget_edit in self.central_widget.findChildren(QProgressBar):
                widget_edit.setParent(None)  # Rimuove il QProgressBar dal layout  
            return

        self.view.page().runJavaScript(click_expand_js_infraSettimanale)
        self.view.page().runJavaScript(click_toggle_js_infraSettimanale)

        self.progress_bar.setValue(20)  # Set progress to 20%

        # Imposta il timer per eseguire i clic
        self.current_click_index = 0
        self.num_clicks = numero_settimana
        self.timer = QTimer()
        self.timer.timeout.connect(self.handle_timeout_infraSettimanale)
        self.timer.start(2000)  # Intervallo di 2000 ms tra i clic
    
    def handle_timeout_infraSettimanale(self):
        """Gestisce il timeout del timer per eseguire i clic e recuperare il contenuto."""
        if self.current_click_index < self.num_clicks:
            QTimer.singleShot(1000, lambda: retrieve_content_infraSettimanale(self, self.current_click_index))
            self.current_click_index += 1
        else:
            combined_html = combine_html_infrasettimale(self.content_array)
            # Salva HTML
            save_html(self, combined_html)

            self.timer.stop()
                        
    def load_schedule_av_uscieri(self, text_field):
        addProgressbar(self)
        self.progress_bar.setValue(10)  # Imposta il progresso al 10%

        # Array per memorizzare i contenuti
        self.content_array = []

        # Recupera il numero dal campo di testo
        try:
            numero_mesi = int(text_field.text())
            if numero_mesi <= 0:
                raise ValueError("Il numero deve essere positivo")
        except ValueError:
            show_alert("Inserisci un numero valido e positivo!")
            # Rimuovi tutti i QPushButton dal layout
            for widget_edit in self.central_widget.findChildren(QProgressBar):
                widget_edit.setParent(None)  # Rimuove il QProgressBar dal layout  
            return

        self.progress_bar.setValue(20)  # Set progress to 20%

        # Imposta il timer per eseguire i clic
        self.current_click_index = 0
        self.num_clicks = numero_mesi
        self.timer = QTimer()
        self.timer.timeout.connect(self.handle_timeout_av_uscieri)
        self.timer.start(2000)  # Intervallo di 2000 ms tra i clic

    def handle_timeout_av_uscieri(self):
        """Gestisce il timeout del timer per eseguire i clic e recuperare il contenuto."""
        if self.current_click_index < self.num_clicks:
            QTimer.singleShot(1000, lambda: retrieve_content_av_uscieri(self, self.current_click_index))
            self.current_click_index += 1
        else:
            combined_html = combine_html_av_uscieri(self.content_array)
            # Salva HTML
            save_html(self, combined_html)

            self.timer.stop()      
      
    def load_schedule_pulizie(self, text_field):
        addProgressbar(self)
        self.progress_bar.setValue(10)  # Imposta il progresso al 10%

        # Array per memorizzare i contenuti
        self.content_array = []

        # Recupera il numero dal campo di testo
        try:
            numero_mesi = int(text_field.text())
            if numero_mesi <= 0:
                raise ValueError("Il numero deve essere positivo")
        except ValueError:
            show_alert("Inserisci un numero valido e positivo!")
            # Rimuovi tutti i QPushButton dal layout
            for widget_edit in self.central_widget.findChildren(QProgressBar):
                widget_edit.setParent(None)  # Rimuove il QProgressBar dal layout  
            return

        self.progress_bar.setValue(20)  # Set progress to 20%

        # Imposta il timer per eseguire i clic
        self.current_click_index = 0
        self.num_clicks = numero_mesi
        self.timer = QTimer()
        self.timer.timeout.connect(self.handle_timeout_pulizie)
        self.timer.start(2000)  # Intervallo di 2000 ms tra i clic

    def handle_timeout_pulizie(self):
        """Gestisce il timeout del timer per eseguire i clic e recuperare il contenuto."""
        if self.current_click_index < self.num_clicks:
            QTimer.singleShot(1000, lambda: retrieve_content_pulizie(self, self.current_click_index))
            self.current_click_index += 1
        else:
            combined_html = combine_html_pulizie(self.content_array)
            # Salva HTML
            save_html(self, combined_html)

            self.timer.stop()
             
    def load_schedule_gruppi_servizio(self):
        # Implementa la logica per caricare e gestire il tab dei gruppi di servizio
        pass

    def load_schedule_testimonianza_pubblica(self, text_field):
        addProgressbar(self)
        self.progress_bar.setValue(10)  # Imposta il progresso al 10%

        # Array per memorizzare i contenuti
        self.content_array = []

        # Recupera il numero dal campo di testo
        try:
            numero_mesi = int(text_field.text())
            if numero_mesi <= 0:
                raise ValueError("Il numero deve essere positivo")
        except ValueError:
            show_alert("Inserisci un numero valido e positivo!")
            # Rimuovi tutti i QPushButton dal layout
            for widget_edit in self.central_widget.findChildren(QProgressBar):
                widget_edit.setParent(None)  # Rimuove il QProgressBar dal layout  
            return

        self.view.page().runJavaScript(click_toggle_js_testimonianza_pubbl)

        self.progress_bar.setValue(20)  # Set progress to 20%

        # Imposta il timer per eseguire i clic
        self.current_click_index = 0
        self.num_clicks = numero_mesi
        self.timer = QTimer()
        self.timer.timeout.connect(self.handle_timeout_testimonianza_pubblica)
        self.timer.start(2000)  # Intervallo di 2000 ms tra i clic

    def handle_timeout_testimonianza_pubblica(self):

        if self.current_click_index < self.num_clicks:
            QTimer.singleShot(1000, lambda: retrieve_content_testimonianza_pubbl(self, self.current_click_index))
            self.current_click_index += 1
        else:
            combined_html = combine_html_testimonianza_pubbl(self.content_array)
            # Salva HTML
            save_html(self, combined_html)

            self.timer.stop()

    def load_schedule_fineSettimana(self):
        self.__dict__.pop('content', None)
        addProgressbar(self)
        self.progress_bar.setValue(10)  # Imposta il progresso al 10%

        self.view.page().runJavaScript("""
        document.querySelector('[data-rr-ui-event-key="schedule"]').click();
        """, self.check_content_fineSettimana)

    def load_crh_fineSettimana(self):
        self.progress_bar.setValue(50)  
        self.view.page().runJavaScript("""
        document.querySelector('[data-rr-ui-event-key="crh"]').click();
        """, self.check_content_fineSettimana)

    def check_content_fineSettimana(self, content):        
        loop = QEventLoop()
        QTimer.singleShot(2000, loop.quit)
        loop.exec_()
        self.scrape_content_fineSettimana()

    def scrape_content_fineSettimana(self):  
        self.progress_bar.setValue(20)  
        self.view.page().runJavaScript("""
        function getContent() {
                return document.getElementsByClassName('d-flex flex-column gap-4')[0].outerHTML;                      
        }
        getContent();
        """, self.handle_finesettimana_html)

    def handle_finesettimana_html(self, html):
        combined_html = ""
        if not hasattr(self, 'content'):
            self.progress_bar.setValue(40)  # Set progress to 40%
            self.content = html  # discorsi pubblici
            self.load_crh_fineSettimana()  # presidente e lettore
        else:
            self.progress_bar.setValue(60)  # Set progress to 60%
            combined_html = combine_html_fine_settimana(self, self.content, html)
            save_html(self, combined_html)

####################################################################
################## TERRITORIO

    def populate_html_file_list(self):
        # Ottieni il percorso della cartella "territori"
        appdata_folder = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp', 'territori')
        
        # Verifica se la cartella esiste
        if os.path.exists(appdata_folder):
            # Elenca tutti i file con estensione .html
            html_files = [f for f in os.listdir(appdata_folder) if f.endswith('.html')]
            
            # Aggiungi i file alla lista
            self.html_file_list.clear()
            for file_name in html_files:
                item = QListWidgetItem(file_name)
                self.html_file_list.addItem(item)
        else:
            # Se la cartella non esiste, creare e non aggiungere nulla alla lista
            os.makedirs(appdata_folder)

    def load_html_file_from_list(self, item):
        # Ottieni il nome del file cliccato
        file_name = item.text()
        
        # Costruisci il percorso completo del file
        appdata_folder = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp', 'territori')
        file_path = os.path.join(appdata_folder, file_name)
        
        # Carica il file nel QWebEngineView
        self.web_view_territorio.setUrl(QUrl.fromLocalFile(file_path))
                    
    def update_map(self):
        angle = self.rotation_spinner.value()
        zoom = self.zoom_spinner.value()
        # Carica e aggiorna la mappa con la rotazione
        save_temp_and_show_map_html_territorio(self, self.coordinates, self.extended_data, self.extended_data_locality_number, angle, zoom, self.center_lat, self.center_lon)

    def open_kml_file_dialog_territorio(self):
        # Dialogo per selezionare un file KML
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleziona file KML", "", "KML Files (*.kml)")
        
        self.coordinates= []
        self.extended_data= []
        self.extended_data_locality_number= []
        self.center_lat = None
        self.center_lon = None
        
        if file_path:
            # Aggiorna il percorso del file KML selezionato nella QLabel
            self.kml_file_path_label.setText(f"File KML selezionato: {file_path}")

            # Processa il file KML e genera la mappa
            self.coordinates = process_kml_file_territorio_coordinates(file_path)
            self.extended_data = process_kml_file_territorio_ext_data(file_path)
            self.extended_data_locality_number = process_kml_file_territorio_locality_number(file_path)
            rotation_angle = 0 #lo inizializzo a 0
            zoom = 18
            if self.coordinates:
                save_temp_and_show_map_html_territorio(self, self.coordinates, self.extended_data, self.extended_data_locality_number, rotation_angle, zoom, self.center_lat, self.center_lon)
            self.kml_loaded = True  # Imposta il flag come caricato
            self.toggle_spinners_territorio(True)  # Abilita gli spinner
        else:
            self.kml_loaded = False  # In caso di fallimento o annullamento
            self.toggle_spinners_territorio(False)  # Disabilita gli spinner
            
    def toggle_spinners_territorio(self, enabled):
        self.rotation_spinner.setEnabled(enabled)
        self.zoom_spinner.setEnabled(enabled)
        self.save_map_button.setEnabled(enabled)
        self.up_button.setEnabled(enabled)
        self.down_button.setEnabled(enabled)
        self.left_button.setEnabled(enabled)
        self.right_button.setEnabled(enabled)
                    
    def save_map_to_folder(self):
        # Ottieni il percorso della cartella di destinazione
        default_folder = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp', 'territori')

        # Verifica se la cartella esiste
        if not os.path.exists(default_folder):
            os.makedirs(default_folder)

        if not self.html_content_territorio:
            QMessageBox.warning(self, "Attenzione", "Nessun contenuto HTML da salvare.")
            return

        file_name = ""
        # Assicurati che extended_data_locality_number contenga almeno due elementi
        if len(self.extended_data_locality_number) >= 2:
            file_name = self.extended_data_locality_number[1] + "_" + self.extended_data_locality_number[0] + ".html"
            file_path = os.path.join(default_folder, file_name)

            if file_name:
                try:
                    # Salva il file HTML nella posizione di destinazione
                    with open(file_path, 'w') as file:
                        file.write(self.html_content_territorio)

                    # Apri una finestra di dialogo per selezionare il percorso di salvataggio del PDF
                    options = QFileDialog.Options()
                    pdf_path, _ = QFileDialog.getSaveFileName(self, "Salva Mappa come PDF", default_folder, "PDF Files (*.pdf)", options=options)

                    if pdf_path:
                        try:
                            # Funzione per stampare la pagina in PDF
                            def save_pdf_to_file(data):
                                try:
                                    with open(pdf_path, 'wb') as f:
                                        f.write(data)
                                    handle_print_result(self, True, pdf_path)  # Chiamata alla funzione di successo
                                except Exception as e:
                                    QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio del PDF: {e}")

                            # Assicurati che la mappa sia completamente renderizzata prima di generare il PDF
                            def on_load_finished():
                                QTimer.singleShot(1000, lambda: page.printToPdf(save_pdf_to_file))

                            page = self.web_view_territorio.page()
                            self.web_view_territorio.page().loadFinished.connect(on_load_finished)
                            self.web_view_territorio.setUrl(QUrl.fromLocalFile(file_path))
                            update_html_file_list(self)
                        except Exception as e:
                            QMessageBox.critical(self, "Errore", f"Impossibile salvare il file PDF: {e}")
                    else:
                        QMessageBox.warning(self, "Salvataggio Annullato", "Il salvataggio è stato annullato.")
                except Exception as e:
                    QMessageBox.critical(self, "Errore", f"Impossibile salvare il file HTML: {e}")



####################################################################
################## VIGEO




    def load_local_ViGeo(self):
        url = QUrl.fromLocalFile(os.path.abspath(os.path.join(os.path.dirname(__file__), "./ViGeo/index.html")))
        self.local_html_view.setUrl(url)
        
        # Collega il segnale di richiesta di download
        self.local_html_view.page().profile().downloadRequested.connect(self.handle_download)

    def handle_download(self, download):
        # Mostra una finestra di dialogo di download
        # Utilizzando os
        home_directory_os = os.path.expanduser("~")
        desktop_directory_os = os.path.join(home_directory_os, "Desktop")
        system_name = platform.system()
        if(system_name=="Windows"):
            download.setPath(desktop_directory_os +"/"+ download.suggestedFileName())
        else:    
            download.setPath(home_directory_os +"/"+ download.suggestedFileName())
        
        download.accept()
        # Crea e mostra il messaggio di avviso
        show_alert("Download avvenuto con successo!")
        
    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Esci", "Sei sicuro di voler uscire?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    ensure_folder_appdata()
    main_window = CongregationToolsApp()
    main_window.show()
    sys.exit(app.exec_())
