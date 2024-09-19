import sys
import base64
import hashlib
import os
import requests
import pickle

from PyQt5.QtWidgets import (QPushButton, QApplication, QMainWindow, 
                             QVBoxLayout, QWidget, QTabWidget, 
                             QMessageBox, QAction, QToolBar, QTableWidget, QListWidget)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QGuiApplication


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

import logging

# Configura il logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def save_tokens(access_token, refresh_token):
    appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp')
    local_file_pkl= appdata_path+'/tokens.pkl'
    with open(local_file_pkl, "wb") as f:
        pickle.dump((access_token, refresh_token), f)

def load_tokens():
    appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp')
    local_file_pkl= appdata_path+'/tokens.pkl'
    try:
        with open(local_file_pkl, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None, None

# Funzioni per l'autenticazione con Dropbox
def initiate_authentication(client_id, code_challenge):
    redirect_uri = "http://localhost:5000/callback"
    auth_url = (
        f"https://www.dropbox.com/oauth2/authorize?client_id={client_id}&response_type=code&"
        f"redirect_uri={redirect_uri}&code_challenge={code_challenge}&"
        f"code_challenge_method=S256&token_access_type=offline"
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
        return tokens.get("access_token"), tokens.get("refresh_token")
    except requests.exceptions.RequestException as e:
        print(f"Errore durante lo scambio del codice di autorizzazione: {e}")
        if e.response is not None:
            print(f"Risposta dell'errore: {e.response.text}")
        return None, None

def refresh_access_token(client_id, refresh_token):
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": refresh_token
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        tokens = response.json()
        return tokens.get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Errore durante il refresh del token di accesso: {e}")
        return None

# Funzione per ottenere informazioni dell'account dell'utente
def get_user_info(access_token):
    url = "https://api.dropboxapi.com/2/users/get_current_account"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        user_info = response.json()
        return user_info.get("name", {}).get("given_name", ""), user_info.get("name", {}).get("surname", "")
    except requests.exceptions.RequestException as e:
        print(f"Errore durante il recupero delle informazioni dell'utente: {e}")
        return "", ""

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

        # Variabile per tenere traccia dello stato del login
        self.logged_in = False
        self.week_display = QWidget()  # Inizializza week_display come un QWidget
        self.tipologie_list = QListWidget()  # Inizializza tipologie_list come QListWidget
        self.person_list = QListWidget()  # Inizializza person_list come 
        
        # Carica i token salvati
        self.access_token, self.refresh_token = load_tokens()
        self.logged_in = self.access_token is not None
        if self.logged_in:
            self.view = QWebEngineView()
            self.update_welcome_layout_after_login()
            self.show_other_tabs()
            self.update_dropbox_button_to_logout()    

        self.center()  # Centratura della finestra

    def center(self):
        # Ottieni le dimensioni dello schermo
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        screen_center = screen_geometry.center()

        # Ottieni la geometria della finestra
        window_geometry = self.frameGeometry()

        # Calcola la posizione centrata tenendo conto delle dimensioni della finestra
        x = screen_center.x() - window_geometry.width() // 2
        y = 50 #screen_center.y() - window_geometry.height() // 2

        # Imposta la geometria della finestra
        self.setGeometry(x, y, window_geometry.width(), window_geometry.height())

    def add_toolbar(self):
        # Crea la barra degli strumenti
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)

        # Aggiungi un'icona (logo) al pulsante di login
        self.dropbox_icon = QIcon("./dropbox_icon.png")  # Assicurati che l'immagine sia disponibile in questo percorso
        self.logout_icon = QIcon("./logout_icon.png")    # Aggiungi un'icona per il logout

        # Aggiungi un'azione per la login di Dropbox con l'icona
        self.dropbox_login_action = QAction(self.dropbox_icon, "Login Dropbox", self)
        self.dropbox_login_action.triggered.connect(self.handle_dropbox_login)
        self.toolbar.addAction(self.dropbox_login_action)

    def handle_dropbox_login(self):
        # Pulizia del layout esistente
        clear_layout(self.benvenuto_layout, exclude_widgets=[self.welcome_label])

        # Aggiorna il testo dell'etichetta
        self.welcome_label.setText("Effettua il login con Dropbox...")
        if self.welcome_label not in [self.benvenuto_layout.itemAt(i).widget() for i in range(self.benvenuto_layout.count())]:
            self.benvenuto_layout.addWidget(self.welcome_label)
        self.welcome_label.show()

        # Inizializza l'autenticazione
        client_id = "4purifuc7efvwld"  # Sostituisci con il tuo client_id
        auth_url = initiate_authentication(client_id, self.code_challenge)

        # Carica l'URL di autenticazione nella QWebEngineView
        self.view = QWebEngineView()
        self.view.setUrl(QUrl(auth_url))
        self.view.urlChanged.connect(self.handle_dropbox_auth_url_change)

        # Aggiungi la QWebEngineView al layout di benvenuto
        self.benvenuto_layout.addWidget(self.view)
        self.benvenuto_layout.update()
        self.view.show()

    def handle_dropbox_auth_url_change(self, url):
        url_str = url.toString()

        if "code=" in url_str:
            code = url_str.split("code=")[1].split("&")[0]
            access_token, refresh_token = exchange_code_for_tokens("4purifuc7efvwld", self.code_verifier, code, "http://localhost:5000/callback")
            
            if access_token:
                # Disconnetti il segnale e aggiorna il layout dopo il login
                self.view.urlChanged.disconnect(self.handle_dropbox_auth_url_change)
                self.update_welcome_layout_after_login()

                # Salva i token per un uso futuro
                self.access_token = access_token
                self.refresh_token = refresh_token
                save_tokens(self.access_token, self.refresh_token)
                
                # Cambia lo stato di login
                self.logged_in = True

                # Cambia le variabili del nome e cognome dell'utente (dovresti ottenere questi dati tramite l'API di Dropbox o un altro metodo)
                self.user_name = "Nome"     # Sostituisci con il nome dell'utente
                self.user_surname = "Cognome"  # Sostituisci con il cognome dell'utente

                # Aggiorna il pulsante della barra degli strumenti in "Logout"
                self.update_dropbox_button_to_logout()

    def handle_dropbox_logout(self):
        # Implementa la logica di logout (es. rimuovere il token, ripulire lo stato)
        print("Logged out from Dropbox.")
        # Resetta lo stato di login
        self.logged_in = False
        self.access_token = None
        self.refresh_token = None        
        # Rimuovi tutti i tab tranne il tab di benvenuto
        self.remove_all_tabs()
        
        setup_benvenuto_tab(self)
        # Aggiorna il pulsante della barra degli strumenti in "Login"
        self.update_dropbox_button_to_login()
        save_tokens(None, None)  # Rimuovi i token salvati

    def use_access_token(self):
        if not self.access_token:
            if self.refresh_token:
                new_access_token = refresh_access_token("4purifuc7efvwld", self.refresh_token)
                if new_access_token:
                    self.access_token = new_access_token
                    save_tokens(self.access_token, self.refresh_token)
                else:
                    print("Impossibile aggiornare il token di accesso.")
            else:
                print("Nessun token di accesso o refresh token disponibili.")

    def remove_all_tabs(self):
        # Ottieni il numero totale dei tab
        total_tabs = self.tabs.count()

        # Rimuovi i tab a partire dall'ultimo verso il primo
        for i in range(total_tabs - 1, -1, -1):
            self.tabs.removeTab(i)

    def update_dropbox_button_to_login(self):
        # Ripristina l'icona e il testo del pulsante in "Login"
        self.dropbox_login_action.setIcon(self.dropbox_icon)
        self.dropbox_login_action.setText("Login Dropbox")
        self.dropbox_login_action.triggered.disconnect(self.handle_dropbox_logout)
        self.dropbox_login_action.triggered.connect(self.handle_dropbox_login)

    def update_dropbox_button_to_logout(self):
        # Aggiorna l'icona e il testo del pulsante in "Logout"
        self.dropbox_login_action.setIcon(self.logout_icon)
        self.dropbox_login_action.setText("Logout Dropbox")
        self.dropbox_login_action.triggered.disconnect(self.handle_dropbox_login)
        self.dropbox_login_action.triggered.connect(self.handle_dropbox_logout)

    def update_welcome_layout_after_login(self):
        # Rimuovi il web view e aggiorna il layout dopo il login
        self.benvenuto_layout.removeWidget(self.view)
        self.view.deleteLater()  # Rimuovi il widget dal layout e dalla memoria
        
        # Ottieni nome e cognome dell'utente
        if self.access_token:
            self.user_name, self.user_surname = get_user_info(self.access_token)

        # Aggiorna il messaggio di benvenuto
        if hasattr(self, 'user_name') and hasattr(self, 'user_surname'):
            self.welcome_label.setText(f"Benvenuto {self.user_name} {self.user_surname}! Puoi accedere ai tuoi strumenti.")
        else:
            self.welcome_label.setText("Benvenuto! Puoi accedere ai tuoi strumenti.")

        # Aggiungi un pulsante per visualizzare gli altri tab
        self.show_tabs_button = QPushButton("Visualizza Strumenti", self)
        self.show_tabs_button.setStyleSheet("padding: 10px; font-size: 16px;")
        self.benvenuto_layout.addWidget(self.show_tabs_button)
        # Connetti il pulsante per mostrare gli altri tab
        self.show_tabs_button.clicked.connect(self.show_other_tabs)
        
        # Cambia il layout aggiungendo nuovi strumenti se necessario
        self.welcome_label.setStyleSheet("font-size: 18px; color: green;")

    def show_other_tabs(self):
        # Rimuovi il tab di benvenuto (o tenerlo visibile)
        #self.tabs.removeTab(self.tabs.indexOf(self.benvenuto_tab))
        
        # Rimuovi il pulsante 'show_tabs_button' se esiste
        if hasattr(self, 'show_tabs_button'):
            self.benvenuto_layout.removeWidget(self.show_tabs_button)
            self.show_tabs_button.deleteLater()

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
