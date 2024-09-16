import os
from PyQt5.QtWidgets import QMessageBox, QProgressBar, QPushButton, QLineEdit
from jinja2 import Template
import shutil
import platform


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
    #print("Files in %r: %s" % (cwd, files))

    try:
        with open("./template/css/cssHourglass.css", 'r') as css:
            css_content = css.read()
    
        image_path = './template/img/bibbia.png'
        logo_bibbia = f'<img src="{image_path}" alt="bibbia" style="width:100px; height:auto;">'    
        
    except FileNotFoundError:
        print("CSS file not found")
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
    # Assicurati che il layout esista
    if self.web_layout is None:
        # print("Il layout 'web_layout' non è stato impostato.")
        return

    # Verifica se ci sono widget nel layout
    if self.web_layout.count() == 0:
        # print("Il layout è vuoto.")
        return

    # Itera sugli elementi del layout in ordine inverso
    for i in reversed(range(self.web_layout.count())):
        item = self.web_layout.itemAt(i)
        if item is not None:
            widget = item.widget()
            if widget is not None:
                if isinstance(widget, (QPushButton, QLineEdit)):
                    # print(f"Rimuovendo widget: {widget}")  # Debug
                    self.web_layout.removeWidget(widget)  # Rimuove il widget dal layout
                    widget.deleteLater()  # Elimina il widget in modo sicuro
                # else:
                    # print(f"L'elemento {i} è un widget di tipo {type(widget)} e non è un QPushButton/QLineEdit.")  # Debug
            else:
                layout = item.layout()
                if layout is not None:
                    # print(f"L'elemento {i} è un layout di tipo {type(layout)}.")  # Debug
                    # Se è un layout, puoi anche rimuovere i widget da esso
                    clear_layout(self, layout)
                # else:
                    # print(f"L'elemento {i} è None e non è né un widget né un layout.")  # Debug
        # else:
            # print(f"Item {i} è None.")  # Debug

def clear_layout(self, layout):
    """Rimuove tutti i widget da un layout specificato."""
    if layout is None:
        return

    for i in reversed(range(layout.count())):
        item = layout.itemAt(i)
        if item is not None:
            widget = item.widget()
            if widget is not None:
                # print(f"Rimuovendo widget dal layout annidato: {widget}")  # Debug
                layout.removeWidget(widget)
                widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout is not None:
                    # print(f"L'elemento {i} è un layout annidato di tipo {type(sub_layout)}.")  # Debug
                    self.clear_layout(sub_layout)
                # else:
                    # print(f"L'elemento {i} è None e non è né un widget né un layout.")  # Debug


def ensure_folder_appdata():
    # Ottieni il percorso della cartella APPDATA e aggiungi 'CongregationToolsApp'
    appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp')

    # Verifica se la cartella esiste
    if os.path.exists(appdata_path):
        # Svuota la cartella esistente tranne la cartella 'territori'
        for item in os.listdir(appdata_path):
            item_path = os.path.join(appdata_path, item)
            if item != 'territori':
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)  # Rimuove le cartelle e il loro contenuto
                else:
                    os.remove(item_path)  # Rimuove i file
            else:
                # Gestisci la cartella 'territori'
                territori_path = item_path
                # Elimina solo il file 'territori_map.html'
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
    except FileExistsError:
        print(f"La cartella di destinazione '{destination_folder}' esiste già.")
    except Exception as e:
        print(f"Errore durante la copia della cartella: {e}")                   

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
         