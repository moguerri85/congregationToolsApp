from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtCore import QEventLoop, QTimer

from hourglass.ui_hourglass import setup_av_attendant, setup_cleaning, setup_groups, setup_infra_week, setup_testimonianza_pubblica, setup_weekend
from hourglass.av_uscieri import combine_html_av_uscieri, retrieve_content_av_uscieri
from hourglass.fine_settimana import combine_html_fine_settimana
from hourglass.infra_settimanale import click_expand_js_infraSettimanale, click_toggle_js_infraSettimanale, combine_html_infrasettimale, retrieve_content_infraSettimanale
from hourglass.pulizie import combine_html_pulizie, retrieve_content_pulizie
from utils.utility import addProgressbar, clear_existing_widgets, save_html, show_alert
from hourglass.testimonianza_pubblica import click_toggle_js_testimonianza_pubbl, combine_html_testimonianza_pubbl, retrieve_content_testimonianza_pubbl

def setup_schedule(self, url):
    self.__dict__.pop('content', None)
    url = self.view.url().toString()

    setup_methods = {
        "/scheduling/wm": setup_weekend,
        "/scheduling/mm": setup_infra_week,
        "/scheduling/avattendant": setup_av_attendant,
        "/scheduling/cleaning": setup_cleaning,
        "/scheduling/manageGroups": setup_groups,
        "/scheduling/publicWitnessing": setup_testimonianza_pubblica
    }

    # Clear existing widgets
    clear_existing_widgets(self)
    
    # Determine the appropriate setup function based on the URL substring
    setup_method = None
    for key in setup_methods:
        if key in url:
            setup_method = setup_methods[key]
            break
    
    if setup_method:
        setup_method(self)
    else:
        self.statusBar().showMessage("")

def load_schedule(self, text_field, schedule_type, retrieve_content, combine_html):
    addProgressbar(self)
    self.progress_bar.setValue(10)
    self.content_array = []

    try:
        number = int(text_field.text())
        if number <= 0:
            raise ValueError("Il numero deve essere positivo")
    except ValueError:
        show_alert("Inserisci un numero valido e positivo!")
        clear_widgets(self)
        return

    self.progress_bar.setValue(20)
    self.current_click_index = 0
    self.num_clicks = number
    self.timer = QTimer()
    self.timer.timeout.connect(lambda: self.handle_timeout(schedule_type, retrieve_content, combine_html))
    self.timer.start(2000)

def handle_timeout(self, schedule_type, retrieve_content, combine_html):
    if self.current_click_index < self.num_clicks:
        QTimer.singleShot(1000, lambda: retrieve_content(self, self.current_click_index))
        self.current_click_index += 1
    else:
        combined_html = combine_html(self.content_array)
        save_html(self, combined_html)
        self.timer.stop()

def clear_widgets(self):
    for widget in self.central_widget.findChildren(QProgressBar):
        widget.setParent(None)

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
    self.timer.timeout.connect(self.call_handle_timeout_infraSettimanale)
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
    
def load_schedule_fineSettimana(self):
    self.__dict__.pop('content', None)
    addProgressbar(self)
    self.progress_bar.setValue(10)
    self.view.page().runJavaScript("""
    document.querySelector('[data-rr-ui-event-key="schedule"]').click();
    """, self.call_check_content_fineSettimana)

def load_crh_fineSettimana(self):
    self.progress_bar.setValue(50)
    self.view.page().runJavaScript("""
    document.querySelector('[data-rr-ui-event-key="crh"]').click();
    """, self.call_check_content_fineSettimana)

def check_content_fineSettimana(self, content):
    loop = QEventLoop()
    QTimer.singleShot(2000, loop.quit)
    loop.exec_()
    self.call_scrape_content_fineSettimana()

def scrape_content_fineSettimana(self):
    self.progress_bar.setValue(20)
    self.view.page().runJavaScript("""
    function getContent() {
        return document.getElementsByClassName('d-flex flex-column gap-4')[0].outerHTML;
    }
    getContent();
    """, self.call_handle_finesettimana_html)

def handle_finesettimana_html(self, html):
    if not hasattr(self, 'content'):
        self.progress_bar.setValue(40)
        self.content = html
        load_crh_fineSettimana(self)
    else:
        self.progress_bar.setValue(60)
        combined_html = combine_html_fine_settimana(self, self.content, html)
        save_html(self, combined_html)

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
    self.timer.timeout.connect(self.call_handle_timeout_av_uscieri)
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
    self.timer.timeout.connect(self.call_handle_timeout_pulizie)
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
    self.timer.timeout.connect(self.call_handle_timeout_testimonianza_pubblica)
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

def load_schedule_gruppi_servizio(self):
    # Implementa la logica per caricare e gestire il tab dei gruppi di servizio
    pass
