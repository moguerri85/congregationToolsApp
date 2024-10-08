import sys

from PyQt5.QtWidgets import (QPushButton, QApplication, QMainWindow, 
                             QVBoxLayout, QWidget, QTabWidget, 
                             QMessageBox, QAction, QToolBar, QScrollArea, QListWidget)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QGuiApplication


from PyQt5.QtGui import QPainter, QColor, QIcon

from hourglass.hourglass_manager import (
    handle_finesettimana_html, handle_timeout_av_uscieri, handle_timeout_infraSettimanale, handle_timeout_pulizie,
    handle_timeout_testimonianza_pubblica, load_disponibilita_espositore, load_disponibilita_testimonianza_pubblica, load_schedule_av_uscieri, load_schedule_infraSettimanale, check_content_fineSettimana,
    load_schedule_fineSettimana, load_schedule_pulizie, load_schedule_testimonianza_pubblica, process_html_disponibilita_espositore, scrape_content_fineSettimana, setup_schedule
)

from hourglass.ui_hourglass import setup_hourglass_tab
from utils.auth_utility import exchange_code_for_tokens, generate_code_challenge, generate_code_verifier, get_user_info, initiate_authentication, load_tokens, refresh_access_token, save_tokens
from espositore.espositore_utils import load_data
from utils.logging_custom import logging_custom
from utils.ui_benvenuto import setup_benvenuto_tab
from espositore.ui_espositore import setup_espositore_tab
from utils.ui_vigeo import setup_vigeo_tab
from utils.update_software import check_for_updates
from utils.utility import clear_layout, ensure_folder_appdata
from utils.ui_territorio import load_html_file_from_list, setup_territorio_tab
from utils.kml_manager import open_kml_file_dialog_territorio, update_map, save_map_to_folder

CURRENT_VERSION = "1.0.5"  # Versione corrente dell'app
GITHUB_RELEASES_API_URL = "https://api.github.com/repos/moguerri85/congregationToolsApp/releases/latest"

# Interceptor per le richieste
class RequestInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        url = info.requestUrl().toString()
        logging_custom(self, "debug", f"Intercepted request to: {url}")
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
        # Imposta dimensioni minime e massime della finestra
        self.setMinimumSize(800, 600)  # Dimensione minima
        #self.setMaximumSize(1200, 800)  # Dimensione massima

        # Crea il widget centrale
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.benvenuto_layout = QVBoxLayout()  # Aggiungi questa riga nel costruttore

        # Aggiungi l'overlay
        self.overlay = OverlayWidget(self)

        # Aggiungi QTabWidget per gestire i tab
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        setup_benvenuto_tab(self)
        
        # Aggiungi la barra degli strumenti
        self.add_toolbar()

        # Genera code verifier e code challenge
        self.code_verifier = generate_code_verifier(self)
        self.code_challenge = generate_code_challenge(self, self.code_verifier)

        # Controlla aggiornamenti all'avvio
        message_update = check_for_updates(CURRENT_VERSION, GITHUB_RELEASES_API_URL)
        self.statusBar().showMessage(message_update)

        # Variabile per tenere traccia dello stato del login
        self.logged_in = False
        self.week_display_and_data = QWidget()  # Inizializza week_display_and_data come un QWidget
        self.tipologie_list = QListWidget()  # Inizializza tipologie_list come QListWidget
        self.person_list = QListWidget()  # Inizializza person_list come 
        
        self.is_logged_in = False  # Attributo per tenere traccia dello stato di login

        # Carica i token salvati
        self.access_token, self.refresh_token = load_tokens(self)
        self.logged_in = self.access_token is not None
        if self.logged_in:
            self.view = QWebEngineView()
            self.update_welcome_layout_after_login()
            self.show_other_tabs()
            self.update_dropbox_button_to_logout()
        else:
            save_tokens(self, None, None) 
            self.remove_all_tabs()
            # Aggiorna il pulsante della barra degli strumenti in "Login"
            self.update_dropbox_button_to_login()
            setup_benvenuto_tab(self)
            
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

        # Aggiungi un'azione per il caricamento dei dati
        self.load_data_icon = QIcon("./load_data_icon.png")  # Sostituisci con il percorso dell'icona che desideri utilizzare
        self.load_data_action = QAction(self.load_data_icon, "Carica Dati", self)
        self.load_data_action.triggered.connect(self.call_load_data)  # Collega il pulsante alla funzione load_data senza chiamarla
        self.toolbar.addAction(self.load_data_action)

    def call_load_data(self):
        load_data(self)

    def handle_dropbox_login(self):
        # Pulizia del layout esistente
        clear_layout(self, self.benvenuto_layout, exclude_widgets=[self.welcome_label])

        # Aggiorna il testo dell'etichetta
        self.welcome_label.setText("Effettua il login con Dropbox...")
        if self.welcome_label not in [self.benvenuto_layout.itemAt(i).widget() for i in range(self.benvenuto_layout.count())]:
            self.benvenuto_layout.addWidget(self.welcome_label)
        self.welcome_label.show()

        # Inizializza l'autenticazione
        client_id = "4purifuc7efvwld"  # Sostituisci con il tuo client_id
        auth_url = initiate_authentication(self, client_id, self.code_challenge)

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
            try:
                access_token, refresh_token = exchange_code_for_tokens(self, "4purifuc7efvwld", self.code_verifier, code, "http://localhost:5000/callback")
                if access_token:
                    self.logged_in = True
                    self.access_token = access_token
                    self.refresh_token = refresh_token
                    save_tokens(self, self.access_token, self.refresh_token)

                    # Aggiorna immediatamente il pulsante del toolbar
                    self.update_dropbox_button_to_logout()

                    # Aggiorna il layout di benvenuto dopo il login
                    self.update_welcome_layout_after_login()
                else:
                    raise Exception("Access token not received.")
            except Exception as e:
                logging_custom(self, "error", f"Error during login: {str(e)}")
                QMessageBox.critical(self, "Login Error", "Failed to login. Please try again.")

    def handle_dropbox_logout(self):
        # Implementa la logica di logout (es. rimuovere il token, ripulire lo stato)
        logging_custom(self, "debug", "Logged out from Dropbox.")
        # Resetta lo stato di login
        self.logged_in = False
        self.access_token = None
        self.refresh_token = None        
        # Rimuovi tutti i tab tranne il tab di benvenuto
        self.remove_all_tabs()
        
        setup_benvenuto_tab(self)
        # Aggiorna il pulsante della barra degli strumenti in "Login"
        self.update_dropbox_button_to_login()
        save_tokens(self, None, None)  # Rimuovi i token salvati

    def use_access_token(self):
        if not self.access_token:
            if self.refresh_token:
                new_access_token = refresh_access_token(self, "4purifuc7efvwld", self.refresh_token)
                if new_access_token:
                    self.access_token = new_access_token
                    save_tokens(self, self.access_token, self.refresh_token)
                else:
                    logging_custom(self, "debug", "Impossibile aggiornare il token di accesso.")
            else:
                logging_custom(self, "debug", "Nessun token di accesso o refresh token disponibili.")

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

        # Se l'azione di logout è connessa, disconnettila
        if self.is_logged_in:
            self.dropbox_login_action.triggered.disconnect(self.handle_dropbox_logout)
            self.is_logged_in = False  # Aggiorna lo stato

        # Ricollega il segnale per il login
        self.dropbox_login_action.triggered.connect(self.handle_dropbox_login)

    def update_dropbox_button_to_logout(self):
        logging_custom(self, "debug", "Cambio pulsante in Logout")
        # Aggiorna l'icona e il testo del pulsante in "Logout"
        self.dropbox_login_action.setIcon(self.logout_icon)
        self.dropbox_login_action.setText("Logout Dropbox")

        # Se l'azione di login è connessa, disconnettila
        if not self.is_logged_in:
            self.dropbox_login_action.triggered.disconnect(self.handle_dropbox_login)
            self.is_logged_in = True  # Aggiorna lo stato

        # Ricollega il segnale per il logout
        self.dropbox_login_action.triggered.connect(self.handle_dropbox_logout)

    def update_welcome_layout_after_login(self):
        # Rimuovi il web view e aggiorna il layout dopo il login
        self.benvenuto_layout.removeWidget(self.view)
        self.view.deleteLater()  # Rimuovi il widget dal layout e dalla memoria
        
        # Ottieni nome e cognome dell'utente
        if self.access_token:
            self.user_name, self.user_surname = get_user_info(self, self.access_token)

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
        # self.tabs.removeTab(self.tabs.indexOf(self.benvenuto_tab))

        # Rimuovi il pulsante 'show_tabs_button' se esiste
        if hasattr(self, 'show_tabs_button'):
            self.benvenuto_layout.removeWidget(self.show_tabs_button)
            self.show_tabs_button.deleteLater()

        # Aggiungi il tab 
        setup_hourglass_tab(self)

        # Imposta l'URL della pagina Hourglass
        self.load_page("https://app.hourglass-app.com/v2/page/app/scheduling/")
        self.view.urlChanged.connect(self.handle_url_change_hourglass)

        # Aggiungi il tab a tabs
        self.tabs.addTab(self.hourglass_tab, "Hourglass")  # Aggiungi il tab

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
            logging_custom(self, "debug", "Page loaded successfully.")
        else:
            logging_custom(self, "debug", "Failed to load page.")

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
        
    def call_load_disponibilita_testimonianza_pubblica(self):
        load_disponibilita_testimonianza_pubblica(self)  
          
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
        
    def get_tipologie_espositore(self, valore):
        self.progress_bar.setValue(20)  
        js_code_get_tipologie = """
        (function() {
            var tipologie = {};
            
            var chosenPlaceInputs = document.querySelectorAll('input[placeholder="Luogo scelto"]');
            chosenPlaceInputs.forEach(function(input, index) {
                // Trim del valore dell'input
                var trimmedValue = input.value.trim();
                if (trimmedValue) {
                    // Usa il valore trimmato come chiave e assegna un valore unico basato sull'indice
                    tipologie[trimmedValue] = index + 1; // +1 per iniziare da 1 invece di 0
                }
            });

            return tipologie; // Restituisci l'oggetto corretto
        })();
        """
        self.view.page().runJavaScript(js_code_get_tipologie, self.process_tipologie_espositore)

    def process_tipologie_espositore(self, tipologie):
        self.progress_bar.setValue(30)  
        logging_custom(self, "debug", f"Tipologie type: {type(tipologie)}")
        logging_custom(self, "debug", f"Tipologie content: {tipologie}")
            
        # Log per il tipo di ritorno
        if tipologie is None:
            logging_custom(self, "error", "Nessun dato restituito dal JavaScript")
            return

        # Verifica se è un dizionario
        if isinstance(tipologie, dict):
            # Carica la disponibilità per i luoghi scelti
            load_disponibilita_espositore(self, tipologie)
        else:
            logging_custom(self, "error", "Tipologie non è un dizionario o non è stato caricato correttamente")


    def call_process_html_disponibilita_espositore(self, html, tipologie):
        self.progress_bar.setValue(50)  
        # Verifica che html sia una stringa
        if isinstance(html, str):
            process_html_disponibilita_espositore(self, html, tipologie)
        else:
            logging_custom(self, "error", f"HTML non valido ricevuto: {html} (tipo: {type(html)})")

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
