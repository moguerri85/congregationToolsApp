import uuid
from bs4 import BeautifulSoup
import json
import os
import re

from datetime import datetime, timedelta

from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtCore import QEventLoop, QTimer

from hourglass.ui_hourglass import setup_av_attendant, setup_cleaning, setup_groups, setup_infra_week, setup_testimonianza_pubblica, setup_weekend
from hourglass.av_uscieri import combine_html_av_uscieri, retrieve_content_av_uscieri
from hourglass.fine_settimana import combine_html_fine_settimana
from hourglass.infra_settimanale import click_expand_js_infraSettimanale, click_toggle_js_infraSettimanale, combine_html_infrasettimale, retrieve_content_infraSettimanale
from hourglass.pulizie import combine_html_pulizie, retrieve_content_pulizie
from utils.logging_custom import logging_custom
from utils.utility import addProgressbar, clear_existing_widgets, hide_overlay, save_html, show_alert
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

def load_disponibilita_testimonianza_pubblica(self):
    addProgressbar(self)
    self.progress_bar.setValue(10)  # Imposta il progresso al 10%
    logging_custom(self, "debug", "load_disponibilita_testimonianza_pubblica")

    # Codice JS per cliccare sugli elementi con data-rr-ui-event-key=1 (per caricare le tipologie)
    js_code_click_tab = """
        (function() {
            var tab = document.querySelector('[data-rr-ui-event-key="1"]');
            if (tab) {
                tab.click();
            }
        })();
    """

    # Clicca sul tab per caricare le tipologie
    self.view.page().runJavaScript(js_code_click_tab, self.get_tipologie_espositore)

def load_disponibilita_espositore(self, tipologie):
    self.progress_bar.setValue(40)  
    # Codice JS per cliccare sugli elementi con data-rr-ui-event-key=2
    js_code_click_disponibilita = """
        (function() {
            var elements = document.querySelectorAll('[data-rr-ui-event-key="2"], [data-rr-ui-event-key="2"][data-value="Disponibilità"]');
            elements.forEach(function(element) {
                element.click();
            });
        })();
    """

    # Clicca sul tab per caricare le disponibilità
    self.view.page().runJavaScript(js_code_click_disponibilita)

    # Codice JS per estrarre l'HTML della tabella con un ritardo
    js_code_extract_html = """
        (function() {
            var table = document.getElementsByClassName('table pw_matrix')[0];
            return table ? table.outerHTML : null;  // Restituisce null se la tabella non esiste
        })();
    """

    # Esegui il JavaScript e passa l'HTML alla funzione process_html
    self.view.page().runJavaScript(js_code_extract_html, 
        lambda html: self.call_process_html_disponibilita_espositore(html, tipologie)
    )


def process_html_disponibilita_espositore(self, html, tipologie):
    self.progress_bar.setValue(60)  
    logging_custom(self, "debug", "Processing HTML...")

    # Verifica del tipo di tipologie
    logging_custom(self, "debug", f"Tipologie type: {type(tipologie)}")
    
    if callable(tipologie):
        try:
            tipologie = tipologie()
            logging_custom(self, "debug", f"Tipologie dopo chiamata: {tipologie}")
        except Exception as e:
            logging_custom(self, "error", f"Errore durante la chiamata a tipologie: {e}")

    if isinstance(tipologie, dict):
        giorni = {"lun": 1, "mar": 2, "mer": 3, "gio": 4, "ven": 5, "sab": 6}
        
        # Inizializza tipo_luogo_schedule con i nomi delle tipologie
        result = {"people": {}, "person_schedule": {}, "tipo_luogo_schedule": {}}
        
        for tipologia_nome, tipologia_id in tipologie.items():
            result["tipo_luogo_schedule"][f"tipo_luogo_{tipologia_id}"] = {
                "nome": tipologia_nome,
                "fasce": {}
            }
        
        logging_custom(self, "debug", f"Tipo Luogo Schedule inizializzato: {result['tipo_luogo_schedule']}")
        
        # Se l'HTML è valido, procedi con il parsing e l'assegnazione delle fasce orarie
        if isinstance(html, str):
            soup = BeautifulSoup(html, 'html.parser')
            
            header_cells = soup.select('thead th.sticky-top div.header_title')
            logging_custom(self, "debug", f"Header cells: {[cell.text.strip() for cell in header_cells]}")
            
            rows = soup.select('tbody tr')
            for row in rows:
                name = row.find('td').text.strip()
                person_id = str(uuid.uuid4())
                # Aggiungi il nome insieme alla disponibilità
                result['people'][person_id] = {
                    "name": name,
                    "availability": {}
                }
                
                availability = {}
                checkboxes = row.find_all('input', type='checkbox')
                logging_custom(self, "debug", f"Checkboxes state: {[checkbox.get('checked') for checkbox in checkboxes]}")

                for i, checkbox in enumerate(checkboxes):
                    if checkbox.get('checked') is not None:
                        header_text = header_cells[i].text.strip()
                        logging_custom(self, "debug", f"Processing header: '{header_text}'")
                        
                        # Nuova regex
                        match = re.search(r'([^\d]+)(\s*[a-z]{3})(?:\s*(\d{2}:\d{2}))?', header_text)
                        
                        if match:
                            tipologia = match.group(1).strip()  # Nome del luogo
                            giorno = match.group(2).strip()      # Giorno
                            orario = match.group(3) if match.group(3) else ""  # Orario
                            
                            id_giorno = giorni.get(giorno, None)
                            id_tipologia = tipologie.get(tipologia, None)
                            
                            logging_custom(self, "debug", f"ID Giorno: {id_giorno}, ID Tipologia: {id_tipologia}")

                            if id_giorno and id_tipologia:
                                # Inizializza la disponibilità per la tipologia della persona
                                if f"tipo_luogo_{id_tipologia}" not in availability:
                                    availability[f"tipo_luogo_{id_tipologia}"] = {}
                                
                                if id_giorno not in availability[f"tipo_luogo_{id_tipologia}"]:
                                    availability[f"tipo_luogo_{id_tipologia}"][id_giorno] = []
                                
                                # Aggiungi orario alla disponibilità della persona
                                if orario:
                                    new_orario = add_hour_and_half(orario)
                                    availability[f"tipo_luogo_{id_tipologia}"][id_giorno].append(orario + "-" + new_orario)
                                    
                                # Aggiungi orari a tipo_luogo_schedule
                                if id_giorno not in result["tipo_luogo_schedule"][f"tipo_luogo_{id_tipologia}"]["fasce"]:
                                    result["tipo_luogo_schedule"][f"tipo_luogo_{id_tipologia}"]["fasce"][id_giorno] = []

                                # Usa un set per evitare duplicati
                                unique_times = set(result["tipo_luogo_schedule"][f"tipo_luogo_{id_tipologia}"]["fasce"][id_giorno])

                                # Aggiungi solo orari unici
                                if orario:
                                    unique_times.add(orario + "-" + new_orario)

                                result["tipo_luogo_schedule"][f"tipo_luogo_{id_tipologia}"]["fasce"][id_giorno] = list(unique_times)
                            else:
                                logging_custom(self, "warning", f"Giorno o tipologia non validi: '{giorno}', '{tipologia}'")
                        else:
                            logging_custom(self, "warning", f"Invalid header: '{header_text}'")
                    else:
                        logging_custom(self, "debug", "Checkbox non selezionata")
                
                result['people'][person_id]["availability"] = availability
            
            appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp')
            file_path = os.path.join(appdata_path, 'disponibilita_espositore.json')
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            
            self.progress_bar.setValue(90)  
            logging_custom(self, "debug", f"Disponibilità salvata in: {file_path}")

            # Log finale per controllare il contenuto di tipo_luogo_schedule
            logging_custom(self, "debug", f"Tipo Luogo Schedule finale: {result['tipo_luogo_schedule']}")
        else:
            logging_custom(self, "error", f"HTML non valido ricevuto: {html} (tipo: {type(html)})")
    else:
        logging_custom(self, "error", "Tipologie non è un dizionario o non è stato caricato correttamente")
    
    self.progress_bar.setValue(100)  
    hide_overlay(self)


def add_hour_and_half(time_str):
    """Aggiunge un'ora e mezza all'orario fornito in formato HH:MM."""
    if time_str:
        time_obj = datetime.strptime(time_str, "%H:%M")
        new_time = time_obj + timedelta(hours=1, minutes=30)
        return new_time.strftime("%H:%M")
    return ""

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
