import json
import os

from PyQt5.QtWidgets import (QMessageBox, QPushButton, QDialog, QVBoxLayout, QCheckBox,
                             QLabel, QHBoxLayout, QWidget, QListWidget, QSizePolicy, QInputDialog,
                             QListWidgetItem, QMessageBox)                             
from PyQt5.QtCore import Qt, QSize
from datetime import datetime
from PyQt5.QtCore import Qt, QSize, QDateTime

from utils.auth_utility import save_to_dropbox
from utils.logging_custom import logging_custom

SAVE_FILE = "espositore_data.json"

# Mappatura dei giorni della settimana a ID
DAY_TO_ID = {
    "Lunedì": "1",
    "Martedì": "2",
    "Mercoledì": "3",
    "Giovedì": "4",
    "Venerdì": "5",
    "Sabato": "6",
    "Domenica": "7"
}

# Mappatura inversa da ID a nome del giorno
ID_TO_DAY = {v: k for k, v in DAY_TO_ID.items()}

# Funzione per salvare i dati nel file JSON
def save_data(app):
    try:
        data = {
            "people": app.people,
            "tipo_luogo_schedule": app.tipo_luogo_schedule,
            "person_schedule": app.person_schedule,
            "last_import_hourglass": app.last_import_hourglass
        }
        appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp')
        local_file_jsn= appdata_path+'/'+SAVE_FILE
        with open(local_file_jsn, 'w') as f:
            json.dump(data, f, indent=4)  # Salva i dati con indentazione per leggibilità

        update_last_modification_time(app)  
        
    except Exception as e:
        logging_custom(app, "error", f"Errore nel salvataggio dei dati: {str(e)}")
        QMessageBox.critical(app, "Errore", f"Errore nel salvataggio dei dati: {str(e)}")

def load_data(app):
    """Carica i dati da un file JSON e li inserisce nelle strutture appropriate."""
    try:
        appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp')
        local_file_jsn= appdata_path+'/'+SAVE_FILE
        # Legge il file JSON
        if os.path.exists(local_file_jsn) and os.path.getsize(local_file_jsn) > 0:

            with open(local_file_jsn, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            #Carico la data dell'ultimo import
            app.last_import_hourglass = data.get('last_import_hourglass', {})

            # Popola le persone (people)
            app.people = data.get('people', {})
            app.person_schedule = data.get('person_schedule', {})
            app.tipo_luogo_schedule = data.get('tipo_luogo_schedule', {})
            app.tipologie = data.get('tipologie', {})
            app.last_import_hourglass = data.get('last_import_hourglass', {})

            # Aggiorna l'interfaccia utente
            app.person_list.clear()
            for person_id, name in app.people.items():
                item = QListWidgetItem(name)
                item.setData(Qt.UserRole, person_id)
                app.person_list.addItem(item)
            
            # Popola le tipologie (tipo_luogo_schedule)
            app.tipologie_list.clear()
            for tipo_luogo_id, tipo_luogo_data in app.tipo_luogo_schedule.items():
                nome_tipo_luogo = tipo_luogo_data.get('nome', 'Sconosciuto')
                item = QListWidgetItem(nome_tipo_luogo)
                item.setData(Qt.UserRole, tipo_luogo_id)
                app.tipologie_list.addItem(item)
            
            # Aggiorna la visualizzazione della settimana
            update_week_display_and_data(app, None)
            update_last_modification_time(app)
            update_last_load_time(app)
            # Stampa o logga un messaggio di conferma
            logging_custom(app, "debug", "Dati caricati con successo!")
        else:
            # Se il file è vuoto, inizializza le strutture dati
            app.people = {}
            app.tipo_luogo_schedule = {}
            app.tipologie = {}
            app.person_schedule = {}
            app.last_import_hourglass = {}
    
    except json.JSONDecodeError as e:
        QMessageBox.critical(app, "Errore", f"Errore nel parsing del file JSON: {str(e)}")
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore durante il caricamento dei dati: {str(e)}")        
    except FileNotFoundError:
        # Se il file non esiste, si crea una struttura vuota
        logging_custom(app, "error", f"File {SAVE_FILE} non trovato, caricamento di default.")
        app.people = {}
        app.person_schedule = {}
        app.tipo_luogo_schedule = {}
        app.tipologie = {}
        app.last_import_hourglass = {}

    
    except json.JSONDecodeError:
        # Gestione degli errori di parsing JSON
        logging_custom(app, "error", f"Errore nel parsing del file {SAVE_FILE}. Verifica che il file sia un JSON valido.")
    
    except Exception as e:
        # Gestione di altri errori
        logging_custom(app, "error", f"Errore durante il caricamento dei dati: {str(e)}")

def import_disponibilita(app):
    """Carica i dati da un file JSON e li inserisce nelle strutture appropriate."""
    try:
        # Mostra una finestra di dialogo per confermare la sovrascrittura dei dati esistenti
        confirm_msg = QMessageBox()
        confirm_msg.setIcon(QMessageBox.Warning)
        confirm_msg.setWindowTitle("Conferma sovrascrittura")
        confirm_msg.setText("Attenzione! Questa operazione sovrascriverà i dati attualmente inseriti. Vuoi continuare?")
        confirm_msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm_msg.setDefaultButton(QMessageBox.No)

        # Se l'utente sceglie "No", annulla l'importazione
        if confirm_msg.exec_() == QMessageBox.No:
            return

        appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp')
        local_file_jsn = appdata_path + '/disponibilita_espositore.json'
        
        # Controlla se il file esiste prima di provare ad aprirlo
        if not os.path.exists(local_file_jsn):
             # Inizializza le strutture dati vuote
            app.people = {}
            app.person_schedule = {}
            app.tipo_luogo_schedule = {}
            app.tipologie = {}
            app.last_import_hourglass = {}
            logging_custom(app, "error", f"File {local_file_jsn} non trovato. Scarica prima i dati dal tab 'Testimonianza Pubblica'.")
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("File non trovato")
            error_msg.setText(
                "Il file delle disponibilità non è stato trovato. "
                "Per favore, vai al tab 'Hourglass' (se non 'hai fatto, effettua la login), "
                "dal menu laterale clicca ''Testimonianza Pubblica'e successivamente"
                " clicca su 'Scarica disponibilità e luoghi' per scaricare i dati e riprova ad importare!."
            )
            error_msg.exec_()
            logging_custom(app, "error", f"File {local_file_jsn} non trovato. Scarica prima i dati dal tab 'Testimonianza Pubblica'.")
            return  # Esci dalla funzione se il file non viene trovato


        # Legge il file JSON
        if os.path.exists(local_file_jsn) and os.path.getsize(local_file_jsn) > 0:
            with open(local_file_jsn, 'r', encoding='utf-8') as file:
                data = json.load(file)            

            # Popola le persone (people)
            app.people = data.get('people', {})
            app.person_schedule = data.get('person_schedule', {})
            app.tipo_luogo_schedule = data.get('tipo_luogo_schedule', {})
            app.tipologie = data.get('tipologie', {})

            # Aggiorna l'interfaccia utente
            app.person_list.clear()
            for person_id, name in app.people.items():
                item = QListWidgetItem(name)
                item.setData(Qt.UserRole, person_id)
                app.person_list.addItem(item)

            # Popola le tipologie (tipo_luogo_schedule)
            app.tipologie_list.clear()
            for tipo_luogo_id, tipo_luogo_data in app.tipo_luogo_schedule.items():
                nome_tipo_luogo = tipo_luogo_data.get('nome', 'Sconosciuto')
                item = QListWidgetItem(nome_tipo_luogo)
                item.setData(Qt.UserRole, tipo_luogo_id)
                app.tipologie_list.addItem(item)

            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            app.last_import_hourglass = {
                'ultima_modifica': current_time,
                'stato': 'Disponibile'
            }
            
            update_last_load_time(app)
            #Carico la data dell'ultimo import
            

            # Aggiorna la visualizzazione della settimana
            update_week_display_and_data(app, None)
            update_last_modification_time(app)
            
            # Stampa o logga un messaggio di conferma
            logging_custom(app, "debug", "Dati caricati con successo!")
            save_data(app)
        else:
            # Se il file è vuoto, inizializza le strutture dati
            app.people = {}
            app.tipo_luogo_schedule = {}
            app.tipologie = {}
            app.person_schedule = {}
            app.last_import_hourglass = {}

    except json.JSONDecodeError as e:
        QMessageBox.critical(app, "Errore", f"Errore nel parsing del file JSON: {str(e)}")
    except Exception as e:
        print({str(e)})
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore durante il caricamento dei dati: {str(e)}")

def update_week_display_and_data(app, tipo_luogo_nome):
    try:
        # Pulisce il layout esistente
        if app.week_display_and_data.layout():
            while app.week_display_and_data.layout().count():
                child = app.week_display_and_data.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            app.week_display_and_data.setLayout(QVBoxLayout())  # Inizializza il layout se non esiste

        # Ottieni l'ID della tipologia selezionata
        tipo_luogo_id = None
        for index in range(app.tipologie_list.count()):
            item = app.tipologie_list.item(index)
            if item.text() == tipo_luogo_nome:
                tipo_luogo_id = item.data(Qt.UserRole)
                break

        if not tipo_luogo_id:
            return

        # Crea un QLabel con il nome della tipologia
        tipo_luogo_label = QLabel(f"{tipo_luogo_nome}")
        tipo_luogo_label.setStyleSheet("font-weight: bold; font-size: 14px;")  # Puoi cambiare lo stile se necessario
        app.week_display_and_data.layout().addWidget(tipo_luogo_label)  # Aggiungi l'etichetta al layout

        # Recupera lo stato della proprietà "attivo"
        attivo = app.tipo_luogo_schedule[tipo_luogo_id].get("attivo", False)

        # Crea un checkbox per "attivo"
        attivo_checkbox = QCheckBox("Attivo")
        attivo_checkbox.setChecked(attivo)
        attivo_checkbox.stateChanged.connect(lambda state: toggle_attivo(app, tipo_luogo_id, state))
        
        # Aggiungi il checkbox al layout
        app.week_display_and_data.layout().addWidget(attivo_checkbox)

        # Crea e visualizza i quadrati per ogni giorno della settimana usando gli ID
        days_of_week = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

        # Crea un layout orizzontale per i giorni della settimana
        horizontal_layout = QHBoxLayout()

        for day in days_of_week:
            day_id = DAY_TO_ID[day]  # Usa l'ID del giorno
            
            day_widget = QWidget()
            day_layout = QVBoxLayout(day_widget)  # Ogni giorno ha un layout verticale

            day_label = QLabel(day)
            day_layout.addWidget(day_label)
            
            square_button = QPushButton()
            square_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            square_button.setFixedSize(QSize(70, 60))
            square_button.setStyleSheet("background-color: lightgray; border: 1px solid black;")
            
            # Imposta il testo e il colore del quadrato in base alla tipologia
            if tipo_luogo_id in app.tipo_luogo_schedule and day_id in app.tipo_luogo_schedule[tipo_luogo_id]["fasce"]:
                fasce = app.tipo_luogo_schedule[tipo_luogo_id]["fasce"][day_id]

                # Funzione per convertire il testo della fascia oraria in un oggetto datetime
                def convert_to_time(fascia):
                    try:
                        return datetime.strptime(fascia.split('-')[0], '%H:%M')
                    except ValueError:
                        return datetime.max  # Se il formato non è valido, metti in fondo

                # Ordina le fasce orarie
                fasce.sort(key=convert_to_time)
                
                # Aggiungi le fasce al pulsante (separate da un'interruzione di riga)
                square_button.setText("\n".join(fasce))
            else:
                square_button.setText("")

            # Collega il click al quadrato con la funzione per aggiungere/modificare la fascia oraria
            square_button.clicked.connect(lambda _, d=day_id, t=tipo_luogo_id, b=square_button: on_square_click(app, d, t, b))
            
            day_layout.addWidget(square_button)
            day_widget.setLayout(day_layout)
            
            # Aggiungi il widget del giorno al layout orizzontale
            horizontal_layout.addWidget(day_widget)

        # Aggiungi il layout orizzontale al layout principale
        app.week_display_and_data.layout().addLayout(horizontal_layout)

    except Exception as e:
        logging_custom(app, "debug", f"Errore durante l'aggiornamento della settimana: {e}")
        
def on_square_click(app, day_id, tipo_luogo_id, button):
    try:
        # Ottieni il nome del giorno dall'ID
        day = ID_TO_DAY.get(day_id, day_id)  # Usa la mappa per ottenere il nome del giorno

        # Ottieni il nome della tipologia dall'ID
        tipo_luogo_nome = app.tipo_luogo_schedule.get(tipo_luogo_id, {}).get("nome", "N/A")

        # Crea la finestra di dialogo per la gestione delle fasce orarie
        dialog = QDialog()
        dialog.setWindowTitle(f"Gestisci Fasce Orarie per {day} - {tipo_luogo_nome}")
        layout = QVBoxLayout(dialog)

        # Lista delle fasce orarie
        fascia_list_widget = QListWidget()

        # Recupera e ordina le fasce orarie
        fasce = app.tipo_luogo_schedule.get(tipo_luogo_id, {}).get("fasce", {}).get(day_id, [])
        
        # Ordina le fasce orarie usando datetime
        def convert_to_time(fascia):
            try:
                return datetime.strptime(fascia.split('-')[0], '%H:%M')
            except ValueError:
                return datetime.max  # Se c'è un errore, metti l'orario in fondo alla lista
        
        fasce.sort(key=convert_to_time)  # Ordina le fasce usando l'ora di inizio

        # Aggiungi le fasce ordinate al widget
        fascia_list_widget.addItems(fasce)
        layout.addWidget(fascia_list_widget)

        # Pulsante per aggiungere una fascia oraria
        add_button = QPushButton("Aggiungi Fascia Oraria")
        add_button.clicked.connect(lambda: add_fascia(app, day_id, tipo_luogo_id, fascia_list_widget))
        layout.addWidget(add_button)

        # Pulsante per modificare la fascia oraria selezionata
        modify_button = QPushButton("Modifica Fascia Oraria")
        modify_button.clicked.connect(lambda: modify_fascia(app, day_id, tipo_luogo_id, fascia_list_widget))
        layout.addWidget(modify_button)

        # Pulsante per eliminare la fascia oraria selezionata
        delete_button = QPushButton("Elimina Fascia Oraria")
        delete_button.clicked.connect(lambda: delete_fascia(app, day_id, tipo_luogo_id, fascia_list_widget))
        layout.addWidget(delete_button)

        dialog.setLayout(layout)
        dialog.exec_()  # Mostra il dialogo modale

    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

def add_fascia(app, day_id, tipo_luogo_id, fascia_list_widget):
    try:
        text, ok = QInputDialog.getText(app, "Aggiungi Fascia Oraria", "Inserisci fascia oraria (es. 1-2):")
        if ok and text:
            if tipo_luogo_id not in app.tipo_luogo_schedule:
                app.tipo_luogo_schedule[tipo_luogo_id] = {
                    "nome": f"{tipo_luogo_id}",  # Nome di default, può essere cambiato
                    "fasce": {}
                }
            if day_id not in app.tipo_luogo_schedule[tipo_luogo_id]["fasce"]:
                app.tipo_luogo_schedule[tipo_luogo_id]["fasce"][day_id] = []

            # Aggiungi la fascia oraria per quel giorno (usando l'ID del giorno)
            app.tipo_luogo_schedule[tipo_luogo_id]["fasce"][day_id].append(text)
            fascia_list_widget.addItem(text)
            
            # Aggiorna la visualizzazione
            update_day_square(app, day_id, tipo_luogo_id)
            save_data(app)  # Salva i dati dopo aver aggiunto una fascia oraria
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore durante l'aggiunta della fascia oraria: {str(e)}")

def modify_fascia(app, day_id, tipo_luogo_id, fascia_list_widget):
    try:
        selected_item = fascia_list_widget.currentItem()
        if selected_item:
            old_text = selected_item.text()
            new_text, ok = QInputDialog.getText(app, "Modifica Fascia Oraria", "Nuova fascia oraria:", text=old_text)
            if ok and new_text:
                fasce = app.tipo_luogo_schedule[tipo_luogo_id]["fasce"][day_id]
                fasce[fasce.index(old_text)] = new_text
                selected_item.setText(new_text)
                update_day_square(app, day_id, tipo_luogo_id)
                save_data(app)  # Salva i dati dopo aver modificato una fascia oraria
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore durante la modifica della fascia oraria: {str(e)}")

def delete_fascia(app, day_id, tipo_luogo_id, fascia_list_widget):
    try:
        selected_item = fascia_list_widget.currentItem()
        if selected_item:
            text = selected_item.text()
            reply = QMessageBox.question(app, 'Conferma Eliminazione', f"Sei sicuro di voler eliminare la fascia oraria '{text}'?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                fasce = app.tipo_luogo_schedule[tipo_luogo_id]["fasce"][day_id]
                fasce.remove(text)
                fascia_list_widget.takeItem(fascia_list_widget.row(selected_item))
                update_day_square(app, day_id, tipo_luogo_id)
                save_data(app)  # Salva i dati dopo aver eliminato una fascia oraria
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore durante l'eliminazione della fascia oraria: {str(e)}")

def update_day_square(app, day_id, tipo_luogo_id):
    try:
        # Trova il quadrato del giorno corretto
        for index in range(app.week_display_and_data.layout().count()):
            widget = app.week_display_and_data.layout().itemAt(index).widget()
            if widget:
                layout = widget.layout()
                if layout:
                    for i in range(layout.count()):
                        child = layout.itemAt(i).widget()
                        if isinstance(child, QPushButton):
                            if child.property("tipo_luogo_id") == tipo_luogo_id:
                                # Ottieni le fasce orarie per il giorno e la tipologia selezionati
                                fasce = app.tipo_luogo_schedule.get(tipo_luogo_id, {}).get("fasce", {}).get(day_id, [])
                                child.setText(", ".join(fasce))
                                break
        update_week_display_and_data(app, app.tipologie_list.currentItem().text())    
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore durante l'aggiornamento del quadrato del giorno: {str(e)}")

# Funzione per ottenere il nome del giorno da una stringa di data
def get_day_from_date(date_str):
    try:
        # Converti la stringa in un oggetto datetime
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        # Ottieni il nome del giorno in italiano
        giorni_settimana = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
        day_name = giorni_settimana[date_obj.weekday()]
        return day_name
    except ValueError:
        return "N/A"
    
def get_day_from_id(day_id):
    giorno_map = {
        '1': 'Lunedì',
        '2': 'Martedì',
        '3': 'Mercoledì',
        '4': 'Giovedì',
        '5': 'Venerdì',
        '6': 'Sabato',
        '7': 'Domenica',
    }
    """Restituisce il nome del giorno corrispondente all'ID."""
    return giorno_map.get(day_id, "N/A")  # Restituisce "N/A" se l'ID non è valido

def update_last_modification_time(app):
    app.last_modification_label.setText(f"Ultima modifica o caricamento dei dati: {QDateTime.currentDateTime().toString('dd/MM/yyyy HH:mm:ss')}")

def update_last_load_time(app): 
    print(app.last_import_hourglass)   
    # Recupera i dati dal dizionario last_import_hourglass
    last_load_time = app.last_import_hourglass.get('ultima_modifica')
    status = app.last_import_hourglass.get('stato')
    

    print(last_load_time)
    print(status)
    # Verifica se ultima_modifica e stato sono valorizzati
    if last_load_time and status:
        # Entrambi i valori sono presenti, aggiornamento dell'etichetta
        app.last_import_hourglass_label.setText(f"Ultimo Import da Hourglass: {last_load_time} | Stato: {status}")
    else:
        # Uno dei valori non è valorizzato, impostiamo un messaggio di default
        app.last_import_hourglass_label.setText("Dati non disponibili")

def toggle_attivo(app, tipo_luogo_id, state):
    """Gestisce il cambiamento dello stato del checkbox 'attivo'."""
    try:
        app.tipo_luogo_schedule[tipo_luogo_id]["attivo"] = state == Qt.Checked
        save_data(app)  # Salva i dati dopo aver aggiornato lo stato
    except Exception as e:
        logging_custom(app, "error", f"Errore durante l'aggiornamento della proprietà 'attivo': {str(e)}")