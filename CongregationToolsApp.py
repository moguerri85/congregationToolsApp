import sys
import os
import shutil
import platform

from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QTabWidget, QPushButton, QMessageBox, QLineEdit, QProgressBar, QTextEdit
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PyQt5.QtCore import QUrl, QEventLoop, QTimer, QObject, pyqtSlot, Qt
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWebChannel import QWebChannel

from utils.av_uscieri import combine_html_av_uscieri, retrieve_content_av_uscieri
from utils.infra_settimanale import combine_html_infrasettimale, click_toggle_js_infraSettimanale, click_expand_js_infraSettimanale, retrieve_content_infraSettimanale_tab
from utils.fine_settimana import combine_html_fine_settimana
from utils.update_software import check_for_updates
from utils.pulizie import combine_html_pulizie, retrieve_content_pulizie
from utils.testimonianza_pubblica import combine_html_testimonianza_pubbl, retrieve_content_testimonianza_pubbl, click_toggle_js_testimonianza_pubbl
from utils.utility import show_alert, save_html, addProgressbar

CURRENT_VERSION = "1.0.1"  # Versione corrente dell'app
GITHUB_RELEASES_API_URL = "https://api.github.com/repos/moguerri85/congregationToolsApp/releases/latest"

class RequestInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        url = info.requestUrl().toString()
        print(f"Intercepted request to: {url}")
        # Non bloccare le richieste
        info.block(False)

class OverlayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(255, 255, 255, 0.8);")  # Colore bianco semitrasparente
        self.setGeometry(parent.rect())  # Adatta le dimensioni all'area del genitore
        self.setVisible(False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 255, 255, 128))  # Colore bianco con trasparenza

class CongregationToolsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scra - ViGeo")
        self.setGeometry(100, 100, 800, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Aggiungi l'overlay
        self.overlay = OverlayWidget(self)

        # Aggiungi QTabWidget per gestire i tab
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Tab per la visualizzazione web
        self.web_tab = QWidget()
        self.web_layout = QVBoxLayout(self.web_tab)
        self.view = QWebEngineView()
        self.web_layout.addWidget(self.view)
        self.tabs.addTab(self.web_tab, "Hourglass")

        # Tab per il file HTML locale
        self.local_html_view = QWebEngineView()
        interceptor = RequestInterceptor()
        self.local_html_view.page().profile().setRequestInterceptor(interceptor)
        self.local_tab = QWidget()
        self.local_layout = QVBoxLayout(self.local_tab)
        self.local_layout.addWidget(self.local_html_view)
        self.tabs.addTab(self.local_tab, "ViGeo")

        # Imposta l'interceptor per monitorare le richieste di rete
        interceptor = RequestInterceptor()
        QWebEngineProfile.defaultProfile().setRequestInterceptor(interceptor)

        self.load_local_ViGeo()
        self.load_page("https://app.hourglass-app.com/v2/page/app/scheduling/")

        # Connette i segnali di navigazione alla funzione di gestione
        self.view.urlChanged.connect(self.call_page)

        # Controlla aggiornamenti all'avvio
        message_update = ""
        message_update = check_for_updates(CURRENT_VERSION, GITHUB_RELEASES_API_URL)
        #self.label(message_update)
        self.statusBar().showMessage(message_update)

    def load_page(self, url):
        self.view.setUrl(QUrl(url))

    def call_page(self, url):
        self.__dict__.pop('content', None)
        url = self.view.url().toString() 

        self.clear_existing_widgets()
        

        if "/wm" in url:
            self.setup_weekend_tab()
        elif "/mm" in url:
            self.setup_infra_week_tab()
        elif "/avattendant" in url:
            self.setup_av_attendant_tab()
        elif "/cleaning" in url:
            self.setup_cleaning_tab()
        elif "/manageGroups" in url:
            self.setup_groups_tab()
        elif "/publicWitnessing" in url:       
            self.setup_publicWitnessing_tab()            
        else:
            self.statusBar().showMessage("")

    def clear_existing_widgets(self):
        for widget in self.central_widget.findChildren((QPushButton, QLineEdit)):
            widget.setParent(None)

    def setup_weekend_tab(self):
        self.horizontal_layout = QHBoxLayout()
        self.add_button("Genera Stampa Fine Settimana", self.load_schedule_fineSettimana_tab)
        # Aggiungi il layout orizzontale al layout principale
        self.web_layout.addLayout(self.horizontal_layout)

    def setup_infra_week_tab(self):
        # Creiamo un layout orizzontale per contenere il QLineEdit e il QPushButton
        self.horizontal_layout = QHBoxLayout()
        self.add_text_field("Numero di settimane:")
        self.add_button("Genera Stampa Infrasettimanale", lambda: self.load_schedule_infraSettimanale_tab(self.text_field))

        # Aggiungi il layout orizzontale al layout principale
        self.web_layout.addLayout(self.horizontal_layout)

    def setup_av_attendant_tab(self):
        self.horizontal_layout = QHBoxLayout()
        self.add_text_field("Numero di mesi:")
        self.add_button("Genera Stampa Incarchi", lambda: self.load_schedule_av_uscieri(self.text_field))
        self.web_layout.addLayout(self.horizontal_layout)

    def setup_cleaning_tab(self):
        self.horizontal_layout = QHBoxLayout()
        self.add_text_field("Numero di mesi:")
        self.add_button("Genera Stampa Pulizie", lambda: self.load_schedule_pulizie_tab(self.text_field))
        self.web_layout.addLayout(self.horizontal_layout)

    def setup_groups_tab(self):
        self.add_button("Genera Stampa Gruppo di Servizio", self.load_schedule_gruppi_servizio_tab)

    def setup_publicWitnessing_tab(self):
        self.horizontal_layout = QHBoxLayout()
        self.add_text_field("Numero di mesi:")
        self.add_button("Genera Stampa Testimonianza Pubblica", lambda: self.load_schedule_publicWitnessing_tab(self.text_field))
        self.web_layout.addLayout(self.horizontal_layout)


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

    def load_schedule_infraSettimanale_tab(self, text_field):
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
        self.timer.timeout.connect(self.handle_timeout_infraSettimanale_tab)
        self.timer.start(2000)  # Intervallo di 2000 ms tra i clic
    
    def handle_timeout_infraSettimanale_tab(self):
        """Gestisce il timeout del timer per eseguire i clic e recuperare il contenuto."""
        if self.current_click_index < self.num_clicks:
            QTimer.singleShot(1000, lambda: retrieve_content_infraSettimanale_tab(self, self.current_click_index))
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

        #self.view.page().runJavaScript(click_expand_js_infraSettimanale)
        #self.view.page().runJavaScript(click_toggle_js_infraSettimanale)

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
            print(self.current_click_index)
            QTimer.singleShot(1000, lambda: retrieve_content_av_uscieri(self, self.current_click_index))
            self.current_click_index += 1
        else:
            combined_html = combine_html_av_uscieri(self.content_array)
            # Salva HTML
            save_html(self, combined_html)

            self.timer.stop()      
      
    def load_schedule_pulizie_tab(self, text_field):
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
             
    def load_schedule_gruppi_servizio_tab(self):
        print("stampa gruppo di servizio")

    def load_schedule_publicWitnessing_tab(self, text_field):
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
        self.timer.timeout.connect(self.handle_timeout_testimonianza_pubbl)
        self.timer.start(2000)  # Intervallo di 2000 ms tra i clic

    def handle_timeout_testimonianza_pubbl(self):

        if self.current_click_index < self.num_clicks:
            QTimer.singleShot(1000, lambda: retrieve_content_testimonianza_pubbl(self, self.current_click_index))
            self.current_click_index += 1
        else:
            combined_html = combine_html_testimonianza_pubbl(self.content_array)
            # Salva HTML
            save_html(self, combined_html)

            self.timer.stop()

    def load_schedule_fineSettimana_tab(self):
        self.__dict__.pop('content', None)
        addProgressbar(self)
        self.progress_bar.setValue(10)  # Imposta il progresso al 10%

        self.view.page().runJavaScript("""
        document.querySelector('[data-rr-ui-event-key="schedule"]').click();
        """, self.check_content_fineSettimana)

    def load_crh_fineSettimana_tab(self):
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
            self.load_crh_fineSettimana_tab()  # presidente e lettore
        else:
            self.progress_bar.setValue(60)  # Set progress to 60%
            combined_html = combine_html_fine_settimana(self, self.content, html)
            save_html(self, combined_html)

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

def ensure_folder_appdata():
    # Ottieni il percorso della cartella APPDATA e aggiungi 'CongregationToolsApp'
    appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp')

    # Verifica se la cartella esiste, altrimenti creala
    if not os.path.exists(appdata_path):
        try:
            os.makedirs(appdata_path)
            print(f"Cartella creata: {appdata_path}")
        except OSError as e:
            print(f"Errore durante la creazione della cartella: {e}")
    else:
        print(f"La cartella esiste già: {appdata_path}")

    # Percorso della cartella 'template' che vuoi copiare
    source_folder = './template'

    # Destinazione in cui copiare la cartella 'template'
    destination_folder = os.path.join(appdata_path, 'template')

    # Copia la cartella 'template' nella cartella 'CongregationToolsApp'
    try:
        if os.path.exists(source_folder):
            # Copia l'intera cartella con i file e le sottocartelle
            shutil.copytree(source_folder, destination_folder)
            print(f"Cartella '{source_folder}' copiata con successo in '{destination_folder}'")
        else:
            print(f"La cartella sorgente '{source_folder}' non esiste.")
    except Exception as e:
        print(f"Errore durante la copia della cartella: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ensure_folder_appdata()
    scraper = CongregationToolsApp()
    scraper.show()
    sys.exit(app.exec_())
