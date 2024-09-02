import os
from PyQt5.QtWidgets import QMessageBox, QProgressBar, QPushButton
from jinja2 import Template


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
    if "/avattendant" in url: 
        with open("./template/css/cssAVUscieri.css", 'r') as css:
            style_custom = css.read()
        script_custom = ""
        data = {"scraped_data": html, "programma": "Audio\\Video e Uscieri", "logo_bibbia": logo_bibbia, "css_content": css_content, "style_custom": style_custom, "script_custom": script_custom}
        file_name = "audio_video_uscieri.html"
    elif "/wm" in url: 
        with open("./template/css/cssFineSettimana.css", 'r') as css:
            style_custom = css.read()
            script_custom = ""
        data = {"scraped_data": html, "programma": "Adunanza del fine settimana", "logo_bibbia": logo_bibbia, "css_content": css_content, "style_custom": style_custom, "script_custom": script_custom}
        file_name = "fine_settimana.html"
    elif "/mm" in url: 
        with open("./template/css/cssInfrasettimanale.css", 'r') as css:
            style_custom = css.read()
            script_custom = ""
        data = {"scraped_data": html, "programma": "Adunanza Infrasettimanale", "logo_bibbia": logo_bibbia, "css_content": css_content, "style_custom": style_custom, "script_custom": script_custom}
        file_name = "infrasettimanale.html" 
    elif "/cleaning" in url: 
        with open("./template/css/cssPulizie.css", 'r') as css:
            style_custom = css.read()
            script_custom = ""
        data = {"scraped_data": html, "programma": "Pulizie", "logo_bibbia": logo_bibbia, "css_content": css_content, "style_custom": style_custom, "script_custom": script_custom}
        file_name = "pulizie.html"        
    else:
        data = {"scraped_data": html, "programma": "Generico", "logo_bibbia": logo_bibbia, "css_content": css_content}
        file_name = "generico.html"
        
    # Caricamento del template HTML
    with open("./template/template.html", encoding='utf-8') as file:
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
