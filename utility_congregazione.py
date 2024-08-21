import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget, QPushButton, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PyQt5.QtCore import QUrl, QEventLoop, QTimer, QObject, pyqtSlot
from bs4 import BeautifulSoup
from jinja2 import Template
from weasyprint import HTML
import platform
from PyQt5.QtWebChannel import QWebChannel

from utils.av_uscieri import combine_html_av_uscieri
from utils.infra_settimanale import combine_html_infrasettimale
from utils.fine_settimana import combine_html_fine_settimana
from utils.update_software import check_for_updates
from utils.pulizie import combine_html_pulizie

CURRENT_VERSION = "1.0.0"  # Versione corrente dell'app
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
        
        # Rimuovi tutti i QPushButton dal layout
        for widget in self.central_widget.findChildren(QPushButton):
            widget.setParent(None)  # Rimuove il pulsante dal layout
        
        if "/wm" in url:      
            self.scrape_button = QPushButton('Genera Stampa Fine Settimana')
            self.scrape_button.clicked.connect(self.load_schedule_fineSettimana_tab)
            self.web_layout.addWidget(self.scrape_button)
        elif "/mm" in url:
            self.scrape_button = QPushButton('Genera Stampa Infra-Settimanale')  
            self.scrape_button.clicked.connect(self.load_schedule_infraSettimanale_tab)
            self.web_layout.addWidget(self.scrape_button)
        elif "/avattendant" in url:
            self.scrape_button = QPushButton('Genera Stampa Incarchi') 
            self.scrape_button.clicked.connect(self.load_schedule_incarichi) 
            self.web_layout.addWidget(self.scrape_button)
        elif "/cleaning" in url:
            self.scrape_button = QPushButton('Genera Stampa Pulizie') 
            self.scrape_button.clicked.connect(self.load_schedule_pulizie_tab)
            self.web_layout.addWidget(self.scrape_button)
        elif "/manageGroups" in url:
            self.scrape_button = QPushButton('Genera Stampa Gruppo di Servizio') 
            self.scrape_button.clicked.connect(self.load_schedule_gruppi_servizio_tab)
            self.web_layout.addWidget(self.scrape_button)
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
        elif "/mm" in url:
            combined_html = combine_html_infrasettimale(html)
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

    def load_schedule_infraSettimanale_tab(self):
        self.view.page().runJavaScript("""
            function getContent() {
                   return document.getElementById('mainContent').outerHTML;                      
            }
            getContent();
            """, self.handle_html)  

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
        self.show_alert("Generazione e download avvenuto con successo!")
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
        self.show_alert("Download avvenuto con successo!")

    def show_alert(self, testo):
        # Crea e mostra il messaggio di avviso
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(testo)
        msg.setWindowTitle("Avviso")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
        
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
