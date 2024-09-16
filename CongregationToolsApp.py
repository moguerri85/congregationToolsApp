import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QPainter, QColor

from hourglass.hourglass_manager import handle_finesettimana_html, handle_timeout_av_uscieri, handle_timeout_infraSettimanale, handle_timeout_pulizie, handle_timeout_testimonianza_pubblica, load_schedule_av_uscieri, load_schedule_infraSettimanale, check_content_fineSettimana, load_schedule_fineSettimana, load_schedule_pulizie, load_schedule_testimonianza_pubblica, scrape_content_fineSettimana, setup_schedule
from utils.update_software import check_for_updates
from utils.utility import ensure_folder_appdata
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
        self.view.urlChanged.connect(self.handle_url_change_hourglass)

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

    def handle_url_change_hourglass(self, url):
        setup_schedule(self, url.toString())

    def call_check_content_fineSettimana(self, content):
        check_content_fineSettimana(self, content)

    def call_scrape_content_fineSettimana(self):
        scrape_content_fineSettimana(self)

    def call_handle_finesettimana_html(self, html):
        handle_finesettimana_html(self, html)

    def call_load_schedule_fineSettimana(self):
        load_schedule_fineSettimana(self)

    def call_load_schedule_infraSettimanale(self, text_field):    
        load_schedule_infraSettimanale(self, text_field)

    def call_handle_timeout_infraSettimanale(self):
        handle_timeout_infraSettimanale(self)

    def call_load_schedule_av_uscieri(self, text_field):
        load_schedule_av_uscieri(self, text_field)
        
    def call_handle_timeout_av_uscieri(self):
        handle_timeout_av_uscieri(self)

    def call_load_schedule_pulizie(self, text_field):
        load_schedule_pulizie(self, text_field)

    def call_handle_timeout_pulizie(self):
        handle_timeout_pulizie(self)
        
    def call_load_schedule_testimonianza_pubblica(self, text_field):
        load_schedule_testimonianza_pubblica(self, text_field)    
        
    def call_handle_timeout_testimonianza_pubblica(self):
        handle_timeout_testimonianza_pubblica(self)
        
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
