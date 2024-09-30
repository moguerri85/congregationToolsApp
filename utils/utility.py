import os
from PyQt5.QtWidgets import QMessageBox, QProgressBar, QPushButton, QLineEdit
from jinja2 import Template
import shutil
import platform

from utils.logging_custom import logging_custom


def show_overlay(self):
        self.overlay.show()
    
def hide_overlay(self):
    self.overlay.hide()
    
def addProgressbar(self):
    # Rimuovi tutti i QProgressBar dal layout
    for widget in self.central_widget.findChildren(QProgressBar):
        widget.setParent(None)  # Rimuove il pulsante dal layout
    # Create and add the progress bar
    self.progress_bar = QProgressBar(self)
    self.layout.addWidget(self.progress_bar)
    self.progress_bar.setValue(0)
    self.progress_bar.setMaximum(100)  # Assume 100% as max value
    show_overlay(self)  # Mostra l'overlay quando inizia l'operazione
        
def show_alert(testo):
    """Mostra un messaggio di avviso."""
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setText(testo)
    msg.setWindowTitle("Avviso")
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec()
    
def save_html(self, html):
    self.progress_bar.setValue(90)  # Imposta la barra di progresso al 90%

    # Nome del file da scrivere
    file_name = "example.html"
    
    cwd = os.getcwd()  # Get the current working directory (cwd)
    files = os.listdir(cwd)  # Get all the files in that directory
    #logging_custom(self, "debug", "Files in %r: %s" % (cwd, files))

    try:
        with open("./template/css/cssHourglass.css", 'r') as css:
            css_content = css.read()
    
        image_path = './template/img/bibbia.png'
        logo_bibbia = f'<img src="{image_path}" alt="bibbia" style="width:100px; height:auto;">'    
        
    except FileNotFoundError:
        logging_custom(self, "error", "CSS file not found")
        # Handle the error, e.g., provide a default CSS or exit the program                    
        
    url = self.view.url().toString()
    if "/scheduling/avattendant" in url: 
        with open("./template/css/cssAVUscieri.css", 'r') as css:
            style_custom = css.read()
        script_custom = ""
        data = {"scraped_data": html, "programma": "Audio\\Video e Uscieri", "logo_bibbia": logo_bibbia, "css_content": css_content, "style_custom": style_custom, "script_custom": script_custom}
        file_name = "audio_video_uscieri.html"
    elif "/scheduling/wm" in url: 
        with open("./template/css/cssFineSettimana.css", 'r') as css:
            style_custom = css.read()
            script_custom = ""
        data = {"scraped_data": html, "programma": "Adunanza del fine settimana", "logo_bibbia": logo_bibbia, "css_content": css_content, "style_custom": style_custom, "script_custom": script_custom}
        file_name = "fine_settimana.html"
    elif "/scheduling/mm" in url: 
        with open("./template/css/cssInfrasettimanale.css", 'r') as css:
            style_custom = css.read()
            script_custom = ""
        data = {"scraped_data": html, "programma": "Adunanza Infrasettimanale", "logo_bibbia": logo_bibbia, "css_content": css_content, "style_custom": style_custom, "script_custom": script_custom}
        file_name = "infrasettimanale.html" 
    elif "/scheduling/cleaning" in url: 
        with open("./template/css/cssPulizie.css", 'r') as css:
            style_custom = css.read()
            script_custom = ""
        data = {"scraped_data": html, "programma": "Pulizie", "logo_bibbia": logo_bibbia, "css_content": css_content, "style_custom": style_custom, "script_custom": script_custom}
        file_name = "pulizie.html"    
    elif "/scheduling/publicWitnessing" in url: 
        with open("./template/css/cssPublicWitnessing.css", 'r') as css:
            style_custom = css.read()
            script_custom = ""
        data = {"scraped_data": html, "programma": "Testimonianza Pubblica", "logo_bibbia": logo_bibbia, "css_content": css_content, "style_custom": style_custom, "script_custom": script_custom}
        file_name = "testimonianza_pubblica.html"         
    else:
        data = {"scraped_data": html, "programma": "Generico", "logo_bibbia": logo_bibbia, "css_content": css_content}
        file_name = "generico.html"
        
    # Caricamento del template HTML
    with open("./template/template_schedule.html", encoding='utf-8') as file:
        template = Template(file.read())

    html_content = template.render(data)  

    # Scrittura del contenuto HTML su file
    # Creazione html in appdata
    appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp')
    local_file_path= appdata_path+'/'+file_name

    #pdf_path = local_file_path+'.pdf'

    with open(local_file_path, "w", encoding='utf-8') as file:
        file.write(html_content)


    ###### parte per la creazione di pdf


    # Leggi il contenuto HTML dal file
    # with open(local_file_path, 'r', encoding='utf-8') as file:
    #     html_content = file.read()

    # Converti HTML in PDF
    # Convert HTML file to PDF
    # pdfkit.from_file(local_file_path, pdf_path)

    # print("Conversion complete. PDF saved at:", pdf_path)

    
    # Scrittura del contenuto HTML su file
    # home_directory_os = os.path.expanduser("~")
    # desktop_directory_os = os.path.join(home_directory_os, "Desktop")
    #  = platform.system()
    
    #file_path =""
    #if(system_name=="Windows"):
    #    file_path = os.path.join(desktop_directory_os, file_name)
    #else:    
    #    file_path = os.path.join(home_directory_os, file_name)

    #with open(file_path, "w", encoding='utf-8') as file:
    #    file.write(html_content)

    show_alert("Generazione e download avvenuto con successo!")
    self.progress_bar.setValue(100)  # Imposta la barra di progresso al 100%
    hide_overlay(self)
    # Rimuovi tutti i QPushButton dal layout
    for widget_edit in self.central_widget.findChildren(QProgressBar):
        widget_edit.setParent(None)  # Rimuove il QProgressBar dal layout    

def clear_existing_widgets(self):
    logging_custom(self, "debug", "clear_existing_widgets!")
    if self.hourglass_layout is None:
        return

    if self.hourglass_layout.count() == 0:
        return

    for i in reversed(range(self.hourglass_layout.count())):
        item = self.hourglass_layout.itemAt(i)
        if item is not None:
            widget = item.widget()
            if widget is not None:
                if isinstance(widget, (QPushButton, QLineEdit)):
                    self.hourglass_layout.removeWidget(widget)
                    widget.deleteLater()
            else:
                layout = item.layout()
                if layout is not None:
                    clear_layout(self, layout)

def ensure_folder_appdata():
    # Ottieni il percorso della cartella APPDATA e aggiungi 'CongregationToolsApp'
    appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp')

    # Verifica se la cartella esiste
    if os.path.exists(appdata_path):
        # Svuota la cartella esistente tranne le cartelle 'territori', 'ViGeo' e i file 'tokens.pkl', 'espositore_data.json'
        for item in os.listdir(appdata_path):
            item_path = os.path.join(appdata_path, item)
            if item not in ['territori', 'ViGeo', 'tokens.pkl', 'espositore_data.json']:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)  # Rimuove le cartelle e il loro contenuto
                else:
                    os.remove(item_path)  # Rimuove i file
            elif item == 'territori':
                # Gestisci la cartella 'territori'
                territori_path = item_path
                # Elimina solo il file 'territorio_map.html'
                map_file_path = os.path.join(territori_path, 'territorio_map.html')
                if os.path.exists(map_file_path):
                    os.remove(map_file_path)
    else:
        # Crea la cartella se non esiste
        try:
            os.makedirs(appdata_path)
            print(f"Cartella creata: {appdata_path}")
        except OSError as e:
            print(f"Errore durante la creazione della cartella: {e}")

    # Copia la cartella 'ViGeo' nella cartella 'CongregationToolsApp'
    source_vigeo_folder = './ViGeo'  # Presumo che ViGeo sia nella root del progetto
    destination_vigeo_folder = os.path.join(appdata_path, 'ViGeo')

    try:
        if os.path.exists(source_vigeo_folder):
            shutil.copytree(source_vigeo_folder, destination_vigeo_folder)
            print(f"Cartella 'ViGeo' copiata con successo in '{destination_vigeo_folder}'")
        else:
            print(f"La cartella 'ViGeo' non esiste nella sorgente.")
    except FileExistsError:
        print(f"La cartella 'ViGeo' esiste già nella destinazione.")
    except Exception as e:
        print(f"Errore durante la copia della cartella 'ViGeo': {e}")

    # Percorso della cartella 'template' che vuoi copiare
    source_template_folder = './template'

    # Destinazione in cui copiare la cartella 'template'
    destination_template_folder = os.path.join(appdata_path, 'template')

    # Copia la cartella 'template' nella cartella 'CongregationToolsApp'
    try:
        if os.path.exists(source_template_folder):
            # Copia l'intera cartella con i file e le sottocartelle
            shutil.copytree(source_template_folder, destination_template_folder)
            print(f"Cartella '{source_template_folder}' copiata con successo in '{destination_template_folder}'")
        else:
            print(f"La cartella sorgente '{source_template_folder}' non esiste.")
    except FileExistsError:
        print(f"La cartella di destinazione '{destination_template_folder}' esiste già.")
    except Exception as e:
        print(f"Errore durante la copia della cartella 'template': {e}")          

def handle_download(download):
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

def clear_layout(self, layout):
    """Rimuove tutti i widget da un layout specificato."""
    if layout is None:
        return

    for i in reversed(range(layout.count())):
        item = layout.itemAt(i)
        if item is not None:
            widget = item.widget()
            if widget is not None:
                layout.removeWidget(widget)
                widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout is not None:
                    clear_layout(self, sub_layout)            
                