import sys
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
from utils.ui_territorio import setup_territorio_tab, load_html_file_from_list
from utils.kml_manager import open_kml_file_dialog_territorio, update_map, save_map_to_folder
from utils.ui_espositore import setup_espositore_tab
from utils.ui_vigeo import setup_vigeo_tab


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


        # Imposta l'interceptor per monitorare le richieste di rete
        interceptor = RequestInterceptor()
        QWebEngineProfile.defaultProfile().setRequestInterceptor(interceptor)

        setup_vigeo_tab(self)
        interceptor = RequestInterceptor()
        self.local_html_view.page().profile().setRequestInterceptor(interceptor)

        setup_territorio_tab(self)
        setup_espositore_tab(self)


        # Controlla aggiornamenti all'avvio
        message_update = ""
        message_update = check_for_updates(CURRENT_VERSION, GITHUB_RELEASES_API_URL)
        self.statusBar().showMessage(message_update)

        # Disable the ViGeo tab
        # vigeo_index = self.tabs.indexOf(self.local_tab)
        # if vigeo_index != -1:
        #     self.tabs.setTabEnabled(vigeo_index, False)

    def openKML(self):
        open_kml_file_dialog_territorio(self)

    def call_update_map(self):
        update_map(self)

    def call_save_map_to_folder(self):                
        self.save_map = True
        save_map_to_folder(self)
            
    def call_load_html_file_from_list(self, item):
        load_html_file_from_list(self, item)

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

    def setup_weekend(self):
        self.horizontal_layout = QHBoxLayout()
        button = QPushButton("Genera Stampa Fine Settimana")
        button.setFixedWidth(200)
        button.setFixedHeight(30)
        button.clicked.connect(self.load_schedule_fineSettimana)
        self.horizontal_layout.addWidget(button)
        #self.add_button("Genera Stampa Fine Settimana", self.load_schedule_fineSettimana)
        # Aggiungi il layout orizzontale al layout principale
        self.web_layout.addLayout(self.horizontal_layout)
    
    def setup_infra_week(self):
        self.horizontal_layout = QHBoxLayout()
        button = QPushButton("Genera Stampa Infrasettimanale")
        self.add_text_field("Numero di settimane:")
        button.setFixedWidth(200)
        button.setFixedHeight(30)
        button.clicked.connect(lambda: self.load_schedule_infraSettimanale(self.text_field))
        self.horizontal_layout.addWidget(button)
        self.web_layout.addLayout(self.horizontal_layout)


    def setup_av_attendant(self):
        self.horizontal_layout = QHBoxLayout()
        self.add_text_field("Numero di mesi:")
        button = QPushButton("Genera Stampa Incarchi")
        button.setFixedWidth(200)
        button.setFixedHeight(30)
        button.clicked.connect(lambda: self.load_schedule_av_uscieri(self.text_field))
        self.horizontal_layout.addWidget(button)
        self.web_layout.addLayout(self.horizontal_layout)


    def setup_cleaning(self):
        self.horizontal_layout = QHBoxLayout()
        self.add_text_field("Numero di mesi:")
        button = QPushButton("Genera Stampa Pulizie")
        button.setFixedWidth(200)
        button.setFixedHeight(30)
        button.clicked.connect(lambda: self.load_schedule_pulizie(self.text_field))
        self.horizontal_layout.addWidget(button)
        self.web_layout.addLayout(self.horizontal_layout)


    def setup_groups(self):
        button = QPushButton("Genera Stampa Gruppi di Servizio")
        button.setFixedWidth(200)
        button.setFixedHeight(30)
        button.clicked.connect(self.load_schedule_gruppi_servizio)
        self.horizontal_layout.addWidget(button)

    def setup_testimonianza_pubblica(self):
        self.horizontal_layout = QHBoxLayout()
        self.add_text_field("Numero di mesi:")
        button = QPushButton("Genera Stampa Testimonianza Pubblica")
        button.setFixedWidth(200)
        button.setFixedHeight(30)
        button.clicked.connect(lambda: self.load_schedule_testimonianza_pubblica(self.text_field))
        self.horizontal_layout.addWidget(button)
        self.web_layout.addLayout(self.horizontal_layout)

    
    def add_text_field(self, placeholder_text):
        self.text_field = QLineEdit()
        self.text_field.setPlaceholderText(placeholder_text)
        self.text_field.setFixedWidth(200)
        self.text_field.setFixedHeight(30)
        self.horizontal_layout.addWidget(self.text_field)

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
