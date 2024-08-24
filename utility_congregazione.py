import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QTabWidget, QPushButton, QMessageBox, QLineEdit, QProgressBar
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PyQt5.QtCore import QUrl, QEventLoop, QTimer, QObject, pyqtSlot
from jinja2 import Template
import platform
from PyQt5.QtWebChannel import QWebChannel

from utils.av_uscieri import combine_html_av_uscieri
from utils.infra_settimanale import combine_html_infrasettimale, click_toggle_js_infraSettimanale, click_expand_js_infraSettimanale, perform_click_infraSettimanale_tab, retrieve_content_infraSettimanale_tab
from utils.fine_settimana import combine_html_fine_settimana
from utils.update_software import check_for_updates
from utils.pulizie import combine_html_pulizie
from utils.utility import show_alert

CURRENT_VERSION = "1.0.1"  # Versione corrente dell'app
GITHUB_RELEASES_API_URL = "https://api.github.com/repos/moguerri85/utility_congregazione/releases/latest"

class RequestInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        url = info.requestUrl().toString()
        print(f"Intercepted request to: {url}")
        # Non bloccare le richieste
        info.block(False)

class JavaScriptBridge(QObject):
    def __init__(self):
        super().__init__()

    @pyqtSlot(str)
    def linkClicked(self, url):
        # Questa funzione viene chiamata dal JavaScript per notificare il clic su un link
        print(f"Link cliccato: {url}")

class WebScraper(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scra - ViGeo")
        self.setGeometry(100, 100, 800, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Aggiungi QTabWidget per gestire i tab
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Tab per la visualizzazione web
        self.web_tab = QWidget()
        self.web_layout = QVBoxLayout(self.web_tab)
        self.view = QWebEngineView()
        self.web_layout.addWidget(self.view)
        #self.scrape_button = QPushButton('Genera Stampa')
        #self.scrape_button.clicked.connect(self.call_page)
        #self.web_layout.addWidget(self.scrape_button)
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

        # Configura il canale web
        self.channel = QWebChannel()
        self.bridge = JavaScriptBridge()
        self.channel.registerObject('bridge', self.bridge)
        self.view.page().setWebChannel(self.channel)

        self.load_local_ViGeo()
        self.load_page("https://app.hourglass-app.com/v2/page/app/scheduling/")

        # Inietta il codice JavaScript nella pagina per monitorare i clic sui link
        self.inject_javascript()

        # Connette i segnali di navigazione alla funzione di gestione
        self.view.urlChanged.connect(self.call_page)

        # Controlla aggiornamenti all'avvio
        message_update = ""
        message_update = check_for_updates(CURRENT_VERSION, GITHUB_RELEASES_API_URL)
        #self.label(message_update)
        self.statusBar().showMessage(message_update)

    def addProgressbar(self):
        # Rimuovi tutti i QProgressBar dal layout
        for widget in self.central_widget.findChildren(QProgressBar):
            widget.setParent(None)  # Rimuove il pulsante dal layout
        # Create and add the progress bar
        self.progress_bar = QProgressBar(self)
        self.layout.addWidget(self.progress_bar)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)  # Assume 100% as max value

    def inject_javascript(self):
        # Codice JavaScript per rilevare clic sui link e inviare l'URL al Python
        js_code = """
        (function() {
            document.addEventListener('click', function(event) {
                if (event.target.tagName === 'A' && event.target.href) {
                    // Invia l'URL al Python tramite il canale web
                    window.bridge.linkClicked(event.target.href);
                }
            }, true);
        })();
        """
        self.view.page().runJavaScript(js_code)

    def load_page(self, url):
        self.view.setUrl(QUrl(url))

    def call_page(self, url):
        self.__dict__.pop('content', None)
        url = self.view.url().toString()        
        
        # Crea un layout orizzontale
        button_and_edit_layout = QHBoxLayout()
        
        # Rimuovi tutti i QPushButton dal layout
        for widget_button in self.central_widget.findChildren(QPushButton):
            widget_button.setParent(None)  # Rimuove il pulsante dal layout
        # Rimuovi tutti i QPushButton dal layout
        for widget_edit in self.central_widget.findChildren(QLineEdit):
            widget_edit.setParent(None)  # Rimuove il pulsante dal layout    
        
        if "/wm" in url:      
            self.scrape_button = QPushButton('Genera Stampa Fine Settimana')
            self.scrape_button.setFixedWidth(200)  # Imposta larghezza fissa a 200 pixel
            self.scrape_button.setFixedHeight(30)  # Imposta altezza fissa a 30 pixel
            self.scrape_button.clicked.connect(self.load_schedule_fineSettimana_tab)
            button_and_edit_layout.addWidget(self.scrape_button)

            # Aggiungi il layout orizzontale alla web layout
            self.web_layout.addLayout(button_and_edit_layout)
        elif "/mm" in url:
            

            # Aggiungi il campo di testo
            self.text_field = QLineEdit()
            self.text_field.setPlaceholderText("Numero di settimane:")
            self.text_field.setFixedWidth(200)  # Imposta larghezza fissa a 200 pixel
            self.text_field.setFixedHeight(30)  # Imposta altezza fissa a 30 pixel
            button_and_edit_layout.addWidget(self.text_field)

            # Crea il pulsante
            self.scrape_button = QPushButton('Genera Stampa Infra-Settimanale')
            self.scrape_button.setFixedWidth(200)  # Imposta larghezza fissa a 200 pixel
            self.scrape_button.setFixedHeight(30)  # Imposta altezza fissa a 30 pixel
            # Usa lambda o partial per passare self.text_field
            self.scrape_button.clicked.connect(lambda: self.load_schedule_infraSettimanale_tab(self.text_field))
            # oppure: self.scrape_button.clicked.connect(partial(self.load_schedule_infraSettimanale_tab, self.text_field))
            button_and_edit_layout.addWidget(self.scrape_button)

            # Aggiungi il layout orizzontale alla web layout
            self.web_layout.addLayout(button_and_edit_layout)
        elif "/avattendant" in url:
            self.scrape_button = QPushButton('Genera Stampa Incarchi') 
            self.scrape_button.setFixedWidth(200)  # Imposta larghezza fissa a 200 pixel
            self.scrape_button.setFixedHeight(30)  # Imposta altezza fissa a 30 pixel
            self.scrape_button.clicked.connect(self.load_schedule_incarichi) 
            button_and_edit_layout.addWidget(self.scrape_button)

            # Aggiungi il layout orizzontale alla web layout
            self.web_layout.addLayout(button_and_edit_layout)
        elif "/cleaning" in url:
            self.scrape_button = QPushButton('Genera Stampa Pulizie') 
            self.scrape_button.setFixedWidth(200)  # Imposta larghezza fissa a 200 pixel
            self.scrape_button.setFixedHeight(30)  # Imposta altezza fissa a 30 pixel
            self.scrape_button.clicked.connect(self.load_schedule_pulizie_tab)
            button_and_edit_layout.addWidget(self.scrape_button)

            # Aggiungi il layout orizzontale alla web layout
            self.web_layout.addLayout(button_and_edit_layout)
        elif "/manageGroups" in url:
            self.scrape_button = QPushButton('Genera Stampa Gruppo di Servizio') 
            self.scrape_button.setFixedWidth(200)  # Imposta larghezza fissa a 200 pixel
            self.scrape_button.setFixedHeight(30)  # Imposta altezza fissa a 30 pixel
            self.scrape_button.clicked.connect(self.load_schedule_gruppi_servizio_tab)
            button_and_edit_layout.addWidget(self.scrape_button)

            # Aggiungi il layout orizzontale alla web layout
            self.web_layout.addLayout(button_and_edit_layout)
        else:
            self.statusBar().showMessage("")

    def handle_html(self, html):
        combined_html = ""
        url = self.view.url().toString()
        isSave = False
        if "/wm" in url:
            if not hasattr(self, 'content'):
                self.content = html  # discorsi pubblici
                self.load_crh_fineSettimana_tab()  # presidente e lettore
            else:
                combined_html = combine_html_fine_settimana(self.content, html)
                isSave = True
        elif "/avattendant" in url:
            combined_html = combine_html_av_uscieri(html)
            isSave = True
        elif "/cleaning" in url:
            combined_html = combine_html_pulizie(html)
            isSave = True  
        else:
            print("no!")

        # Salva HTML
        if isSave:
            self.save_html(combined_html)

    def load_schedule_infraSettimanale_tab(self, text_field):
        self.addProgressbar()
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
            return

        self.view.page().runJavaScript(click_expand_js_infraSettimanale)
        self.view.page().runJavaScript(click_toggle_js_infraSettimanale)

        self.progress_bar.setValue(20)  # Set progress to 20%

        """Esegue clic sul pulsante con ritardo specificato e gestisce il recupero del contenuto."""
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
            perform_click_infraSettimanale_tab(self)
            QTimer.singleShot(1000, lambda: retrieve_content_infraSettimanale_tab(self, self.current_click_index))
            self.current_click_index += 1
        else:
            combined_html = combine_html_infrasettimale(self.content_array)
            # Salva HTML
            self.save_html(combined_html)

            self.timer.stop()
            self.progress_bar.setValue(100)  # Imposta la barra di progresso al 100%
            # Rimuovi tutti i QPushButton dal layout
            for widget_edit in self.central_widget.findChildren(QProgressBar):
                widget_edit.setParent(None)  # Rimuove il QProgressBar dal layout      
       

    def load_schedule_pulizie_tab(self):
        self.view.page().runJavaScript("""
            function getContent() {
                   return document.getElementById('mainContent').outerHTML;                      
            }
            getContent();
            """, self.handle_html)

    def load_schedule_gruppi_servizio_tab(self):
        print("stampa gruppo di servizio")

    def load_schedule_incarichi(self):
        self.view.page().runJavaScript("""
        function getContent() {
                return document.getElementById('mainContent').outerHTML;                      
        }
        getContent();
        """, self.handle_html)

    def load_schedule_fineSettimana_tab(self):
        self.view.page().runJavaScript("""
        document.querySelector('[data-rr-ui-event-key="schedule"]').click();
        """, self.check_content_fineSettimana)

    def load_crh_fineSettimana_tab(self):
        self.view.page().runJavaScript("""
        document.querySelector('[data-rr-ui-event-key="crh"]').click();
        """, self.check_content_fineSettimana)

    def check_content_fineSettimana(self, content):
        loop = QEventLoop()
        QTimer.singleShot(2000, loop.quit)
        loop.exec_()
        self.scrape_content_fineSettimana()

    def scrape_content_fineSettimana(self):        
        self.view.page().runJavaScript("""
        function getContent() {
                return document.getElementsByClassName('d-flex flex-column gap-4')[0].outerHTML;                      
        }
        getContent();
        """, self.handle_html)
        
    def save_html(self, html):
        # Nome del file da scrivere
        file_name = "example.html"
        
        cwd = os.getcwd()  # Get the current working directory (cwd)
        files = os.listdir(cwd)  # Get all the files in that directory
        #print("Files in %r: %s" % (cwd, files))

        try:
            with open("./template/css/cssHourglass.css", 'r') as css:
                css_content = css.read()
        except FileNotFoundError:
            print("CSS file not found")
            # Handle the error, e.g., provide a default CSS or exit the program                    
         
        url = self.view.url().toString()
        if "/avattendant" in url: 
            with open("./template/css/cssAVUscieri.css", 'r') as css:
                style_custom = css.read()
            script_custom = ""
            data = {"scraped_data": html, "programma": "Audio\\Video e Uscieri", "css_content": css_content, "style_custom": style_custom, "script_custom": script_custom}
            file_name = "audio_video_uscieri.html"
        elif "/wm" in url: 
            with open("./template/css/cssFineSettimana.css", 'r') as css:
                style_custom = css.read()
                script_custom = ""
            data = {"scraped_data": html, "programma": "Adunanza del fine settimana", "css_content": css_content, "style_custom": style_custom, "script_custom": script_custom}
            file_name = "fine_settimana.html"
        elif "/mm" in url: 
            with open("./template/css/cssInfrasettimanale.css", 'r') as css:
                style_custom = css.read()
                script_custom = ""
            data = {"scraped_data": html, "programma": "Adunanza Infrasettimanale", "css_content": css_content, "style_custom": style_custom, "script_custom": script_custom}
            file_name = "infrasettimanale.html" 
        elif "/cleaning" in url: 
            with open("./template/css/cssPulizie.css", 'r') as css:
                style_custom = css.read()
                script_custom = ""
            data = {"scraped_data": html, "programma": "Pulizie", "css_content": css_content, "style_custom": style_custom, "script_custom": script_custom}
            file_name = "pulizie.html"        
        else:
            data = {"scraped_data": html, "programma": "Generico", "css_content": css_content}
            file_name = "generico.html"
            
        # Caricamento del template HTML
        with open("./template/template.html", encoding='utf-8') as file:
            template = Template(file.read())

        html_content = template.render(data)                    
        # Scrittura del contenuto HTML su file
        home_directory_os = os.path.expanduser("~")
        desktop_directory_os = os.path.join(home_directory_os, "Desktop")
        system_name = platform.system()
        
        file_path =""
        if(system_name=="Windows"):
            file_path = os.path.join(desktop_directory_os, file_name)
        else:    
            file_path = os.path.join(home_directory_os, file_name)
            
        with open(file_path, "w", encoding='utf-8') as file:
            file.write(html_content)
        
        #HTML("output.html").write_pdf('output.pdf')
        show_alert("Generazione e download avvenuto con successo!")
        print('Combined HTML saved as output.html')  

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
    scraper = WebScraper()
    scraper.show()
    sys.exit(app.exec_())
