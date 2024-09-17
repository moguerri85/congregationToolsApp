import sys
import base64
import hashlib
import os
import requests
from PyQt5.QtWidgets import QPushButton, QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget, QMessageBox, QAction, QToolBar
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QPainter, QColor, QIcon

from hourglass.hourglass_manager import (
    handle_finesettimana_html, handle_timeout_av_uscieri, handle_timeout_infraSettimanale, handle_timeout_pulizie,
    handle_timeout_testimonianza_pubblica, load_schedule_av_uscieri, load_schedule_gruppi_servizio, load_schedule_infraSettimanale, check_content_fineSettimana,
    load_schedule_fineSettimana, load_schedule_pulizie, load_schedule_testimonianza_pubblica, scrape_content_fineSettimana, setup_schedule
)

from hourglass.ui_hourglass import setup_hourglass_tab
from utils.ui_benvenuto import setup_benvenuto_tab
from utils.ui_espositore import setup_espositore_tab
from utils.ui_vigeo import setup_vigeo_tab
from utils.update_software import check_for_updates
from utils.utility import clear_layout, ensure_folder_appdata
from utils.ui_territorio import load_html_file_from_list, setup_territorio_tab
from utils.kml_manager import open_kml_file_dialog_territorio, update_map, save_map_to_folder

CURRENT_VERSION = "1.0.1"  # Versione corrente dell'app
GITHUB_RELEASES_API_URL = "https://api.github.com/repos/moguerri85/congregationToolsApp/releases/latest"

# Funzioni per PKCE
def generate_code_verifier():
    return base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')

def generate_code_challenge(code_verifier):
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode('utf-8').rstrip('=')
    return code_challenge

# Funzioni per l'autenticazione con Dropbox
def initiate_authentication(client_id, code_challenge):
    redirect_uri = "http://localhost:5000/callback"
    auth_url = (
        f"https://www.dropbox.com/oauth2/authorize?"
        f"client_id={client_id}&response_type=code&"
        f"redirect_uri={redirect_uri}&code_challenge={code_challenge}&"
        f"code_challenge_method=S256"
    )
    return auth_url

def exchange_code_for_tokens(client_id, code_verifier, code, redirect_uri):
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": client_id,
        "code_verifier": code_verifier,
        "redirect_uri": redirect_uri
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        tokens = response.json()
        return tokens["access_token"], tokens.get("refresh_token")
    except requests.exceptions.RequestException as e:
        print(f"Errore durante lo scambio del codice di autorizzazione: {e}")
        return None, None

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

        setup_benvenuto_tab(self)
        
        # Aggiungi la barra degli strumenti
        self.add_toolbar()

        # Genera code verifier e code challenge
        self.code_verifier = generate_code_verifier()
        self.code_challenge = generate_code_challenge(self.code_verifier)

        # Controlla aggiornamenti all'avvio
        message_update = check_for_updates(CURRENT_VERSION, GITHUB_RELEASES_API_URL)
        self.statusBar().showMessage(message_update)

    def add_toolbar(self):
        # Crea la barra degli strumenti
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Aggiungi un'icona (logo) al pulsante di login
        dropbox_icon = QIcon("./dropbox_icon.png")  # Assicurati che l'immagine sia disponibile in questo percorso

        # Aggiungi un'azione per la login di Dropbox con l'icona
        dropbox_login_action = QAction(dropbox_icon, "Login Dropbox", self)
        dropbox_login_action.triggered.connect(self.handle_dropbox_login)
        toolbar.addAction(dropbox_login_action)

    def handle_dropbox_login(self):
        # Pulizia del layout esistente, escludendo il welcome_label
        clear_layout(self.benvenuto_layout, exclude_widgets=[self.welcome_label])

        # Aggiorna il testo dell'etichetta
        self.welcome_label.setText("Effettua il login con Dropbox...")
        
        # Aggiungi il welcome_label al layout
        if self.welcome_label not in [self.benvenuto_layout.itemAt(i).widget() for i in range(self.benvenuto_layout.count())]:
            self.benvenuto_layout.addWidget(self.welcome_label)
        
        # Forza la visibilità dell'etichetta
        self.welcome_label.show()
        
        # Inizializza l'autenticazione
        client_id = "4purifuc7efvwld"  # Sostituisci con il tuo client_id
        auth_url = initiate_authentication(client_id, self.code_challenge)

        # Carica l'URL di autenticazione nella QWebEngineView
        self.view = QWebEngineView()
        self.view.setUrl(QUrl(auth_url))

        # Connetti il cambio di URL per catturare il codice di autorizzazione
        self.view.urlChanged.connect(self.handle_dropbox_auth_url_change)

        # Aggiungi la QWebEngineView al layout di benvenuto
        self.benvenuto_layout.addWidget(self.view)

        # Aggiorna il layout
        self.benvenuto_layout.update()
        self.view.show()


    def handle_dropbox_auth_url_change(self, url):
        url_str = url.toString()

        if "code=" in url_str:
            # Ottieni il codice di autorizzazione dall'URL
            code = url_str.split("code=")[1].split("&")[0]
            print(f"Authorization Code: {code}")

            # Scambia il codice di autorizzazione con un token di accesso
            access_token, refresh_token = exchange_code_for_tokens("4purifuc7efvwld", self.code_verifier, code, "http://localhost:5000/callback")
            print(f"Access Token: {access_token}")

            if access_token:
                # Disconnetti il segnale per evitare chiamate multiple
                self.view.urlChanged.disconnect(self.handle_dropbox_auth_url_change)

                # Aggiorna il layout di benvenuto
                self.update_welcome_layout_after_login()

            else:
                print("Failed to get access token.")
        
        elif "error" in url_str:
            # Gestisci eventuali errori di autenticazione
            print("Error during authentication.")
            self.view.urlChanged.disconnect(self.handle_dropbox_auth_url_change)

    def update_welcome_layout_after_login(self):
        # Rimuovi il web view e aggiorna il layout dopo il login
        self.benvenuto_layout.removeWidget(self.view)
        self.view.deleteLater()  # Rimuovi il widget dal layout e dalla memoria

        # Aggiorna il messaggio di benvenuto
        self.welcome_label.setText("Login effettuato con successo! Puoi accedere ai tuoi strumenti.")
        
        # Aggiungi un pulsante per visualizzare gli altri tab
        show_tabs_button = QPushButton("Visualizza Strumenti", self)
        show_tabs_button.setStyleSheet("padding: 10px; font-size: 16px;")
        self.benvenuto_layout.addWidget(show_tabs_button)
        # Connetti il pulsante per mostrare gli altri tab
        show_tabs_button.clicked.connect(self.show_other_tabs)
        
        # Cambia il layout aggiungendo nuovi strumenti se necessario
        self.welcome_label.setStyleSheet("font-size: 18px; color: green;")

    def show_other_tabs(self):
        # Rimuovi il tab di benvenuto (o tenerlo visibile)
        #self.tabs.removeTab(self.tabs.indexOf(self.benvenuto_tab))
        
        # Aggiungi il tab 
        setup_hourglass_tab(self)

        # Imposta l'URL della pagina Hourglass
        self.load_page("https://app.hourglass-app.com/v2/page/app/scheduling/")
        self.view.urlChanged.connect(self.handle_url_change_hourglass)

        # Verifica che il tab sia visibile
        self.tabs.setCurrentWidget(self.hourglass_tab)

        # Controlla se l'URL è stato caricato
        self.view.loadFinished.connect(self.handle_load_finished)
        
        # Imposta l'intercettore per monitorare le richieste di rete
        interceptor = RequestInterceptor()
        QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(interceptor)

        # Imposta gli altri tab con le rispettive funzioni
        setup_vigeo_tab(self)
        setup_territorio_tab(self)
        setup_espositore_tab(self)

        # Imposta il tab predefinito da mostrare (ad esempio Hourglass)
        self.tabs.setCurrentIndex(0)

    def handle_load_finished(self, ok):
        if ok:
            print("Page loaded successfully.")
        else:
            print("Failed to load page.")

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
