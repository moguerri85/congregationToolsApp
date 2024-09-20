import json
import os

from PyQt5.QtWidgets import (QMessageBox, QPushButton, QDialog, QVBoxLayout, QComboBox,
                             QLabel, QTimeEdit, QWidget, QListWidget, QSizePolicy, QInputDialog)
from PyQt5.QtCore import Qt, QSize


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

def save_data(app):
    try:
        appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp')
        local_file_jsn= appdata_path+'/'+SAVE_FILE
        # Salva i dati in un file JSON
        with open(local_file_jsn, 'w') as f:
            data = {
                'people': app.people,
                'tipologia_schedule': app.tipologia_schedule,
                'person_schedule': app.person_schedule
            }
            json.dump(data, f, indent=4)
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore durante il salvataggio: {str(e)}")

def load_data(app):
    try:
        appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp')
        local_file_jsn= appdata_path+'/'+SAVE_FILE
        with open(local_file_jsn, 'r') as file:
            data = json.load(file)
            app.person_schedule = data.get("person_schedule", {})
            app.people = data.get("people", {})
            app.tipologie = data.get("tipologie", {})
    except (FileNotFoundError, json.JSONDecodeError):
        app.person_schedule = {}
        app.people = {}
        app.tipologie = {}

def update_person_details(app, person_id):
    if person_id in app.person_schedule:
        details = f"Dettagli del proclamatore con ID {person_id}:\n\n"
        for day, info in app.person_schedule[person_id].items():
            tipologia_name = app.tipologie.get(info['tipologia'], 'Sconosciuta')
            details += f"{day}: Tipologia - {tipologia_name}, Fascia Oraria - {info['fascia_oraria']}\n"
        app.detail_text.setPlainText(details)
    else:
        app.detail_text.setPlainText(f"Nessuna disponibilità registrata per il proclamatore con ID {person_id}.")

def show_day_dialog(app, day):
    try:
        dialog = QDialog()
        dialog.setWindowTitle("Aggiungi Fascia Oraria")
        layout = QVBoxLayout(dialog)

        tipologia_label = QLabel("Seleziona la tipologia:")
        layout.addWidget(tipologia_label)
        
        tipologia_combo = QComboBox()
        for tipologia in app.tipologia_schedule.keys():
            tipologia_combo.addItem(tipologia)
        layout.addWidget(tipologia_combo)

        fascia_inizio_label = QLabel("Fascia Oraria Inizio:")
        layout.addWidget(fascia_inizio_label)
        fascia_inizio_time = QTimeEdit()
        layout.addWidget(fascia_inizio_time)

        fascia_fine_label = QLabel("Fascia Oraria Fine:")
        layout.addWidget(fascia_fine_label)
        fascia_fine_time = QTimeEdit()
        layout.addWidget(fascia_fine_time)

        confirm_button = QPushButton("Aggiungi Fascia Oraria")
        confirm_button.clicked.connect(lambda: add_time_slot(app, day, tipologia_combo.currentText(), fascia_inizio_time.time().toString(), fascia_fine_time.time().toString(), dialog))
        layout.addWidget(confirm_button)

        dialog.setLayout(layout)
        dialog.exec_()  # Utilizzare exec_() per il dialogo modale

    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

def add_time_slot(app, day, tipologia, start_time, end_time, dialog):
    try:
        # Verifica se la tipologia e il giorno sono già registrati
        if tipologia not in app.tipologia_schedule:
            app.tipologia_schedule[tipologia] = {}
        if day not in app.tipologia_schedule[tipologia]:
            app.tipologia_schedule[tipologia][day] = []

        # Aggiungi la fascia oraria
        app.tipologia_schedule[tipologia][day].append(f"{start_time} - {end_time}")

        # Aggiorna la visualizzazione della settimana
        update_week_display(app, app.tipologie_list.currentItem().text())

        # Chiudi il dialogo
        dialog.accept()
        
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore durante l'aggiunta della fascia oraria: {str(e)}")

def update_week_display(app, tipologia_nome):
    try:
        # Pulisce il layout esistente
        if app.week_display.layout():
            while app.week_display.layout().count():
                child = app.week_display.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        # Ottieni l'ID della tipologia selezionata
        tipologia_id = None
        for index in range(app.tipologie_list.count()):
            item = app.tipologie_list.item(index)
            if item.text() == tipologia_nome:
                tipologia_id = item.data(Qt.UserRole)
                break

        if not tipologia_id:
            return

        # Crea e visualizza i quadrati per ogni giorno della settimana usando gli ID
        days_of_week = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        
        for day in days_of_week:
            day_id = DAY_TO_ID[day]  # Usa l'ID del giorno
            
            day_widget = QWidget()
            day_layout = QVBoxLayout(day_widget)
            
            day_label = QLabel(day)
            day_layout.addWidget(day_label)
            
            square_button = QPushButton()
            square_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            square_button.setFixedSize(QSize(60, 60))
            square_button.setStyleSheet("background-color: lightgray; border: 1px solid black;")
            
            # Imposta il testo e il colore del quadrato in base alla tipologia
            if tipologia_id in app.tipologia_schedule and day_id in app.tipologia_schedule[tipologia_id]["fasce"]:
                fasce = app.tipologia_schedule[tipologia_id]["fasce"][day_id]
                square_button.setText(", ".join(fasce))
            else:
                square_button.setText("")

            # Collega il click al quadrato con la funzione per aggiungere/modificare la fascia oraria
            square_button.clicked.connect(lambda _, d=day_id, t=tipologia_id, b=square_button: on_square_click(app, d, t, b))
            
            day_layout.addWidget(square_button)
            day_widget.setLayout(day_layout)
            app.week_display.layout().addWidget(day_widget)

    except Exception as e:
        print(f"Errore durante l'aggiornamento della settimana: {e}")

def on_square_click(app, day, tipologia_id, button):
    try:
        # Crea la finestra di dialogo per la gestione delle fasce orarie
        dialog = QDialog()
        dialog.setWindowTitle(f"Gestisci Fasce Orarie per {day}")
        layout = QVBoxLayout(dialog)

        # Lista delle fasce orarie
        fascia_list_widget = QListWidget()
        fasce = app.tipologia_schedule.get(tipologia_id, {}).get(day, [])
        fascia_list_widget.addItems(fasce)
        layout.addWidget(fascia_list_widget)

        # Pulsante per aggiungere una fascia oraria
        add_button = QPushButton("Aggiungi Fascia Oraria")
        add_button.clicked.connect(lambda: add_fascia(app, day, tipologia_id, fascia_list_widget))
        layout.addWidget(add_button)

        # Pulsante per modificare la fascia oraria selezionata
        modify_button = QPushButton("Modifica Fascia Oraria")
        modify_button.clicked.connect(lambda: modify_fascia(app, day, tipologia_id, fascia_list_widget))
        layout.addWidget(modify_button)

        # Pulsante per eliminare la fascia oraria selezionata
        delete_button = QPushButton("Elimina Fascia Oraria")
        delete_button.clicked.connect(lambda: delete_fascia(app, day, tipologia_id, fascia_list_widget))
        layout.addWidget(delete_button)

        dialog.setLayout(layout)
        dialog.exec_()  # Mostra il dialogo modale

    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

def add_fascia(app, day, tipologia_id, fascia_list_widget):
    try:
        text, ok = QInputDialog.getText(app, "Aggiungi Fascia Oraria", "Inserisci fascia oraria (es. 1-2):")
        if ok and text:
            # Usa l'ID del giorno
            day_id = DAY_TO_ID.get(day, day)  # Converti il nome del giorno in ID, se applicabile
            
            if tipologia_id not in app.tipologia_schedule:
                app.tipologia_schedule[tipologia_id] = {
                    "nome": f"{tipologia_id}",  # Nome di default, può essere cambiato
                    "fasce": {}
                }
            if day_id not in app.tipologia_schedule[tipologia_id]["fasce"]:
                app.tipologia_schedule[tipologia_id]["fasce"][day_id] = []

            # Aggiungi la fascia oraria per quel giorno (usando l'ID del giorno)
            app.tipologia_schedule[tipologia_id]["fasce"][day_id].append(text)
            fascia_list_widget.addItem(text)
            
            # Aggiorna la visualizzazione
            update_day_square(app, day_id, tipologia_id)
            save_data(app)  # Salva i dati dopo aver aggiunto una fascia oraria
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore durante l'aggiunta della fascia oraria: {str(e)}")

def modify_fascia(app, day, tipologia_id, fascia_list_widget):
    try:
        selected_item = fascia_list_widget.currentItem()
        if selected_item:
            old_text = selected_item.text()
            new_text, ok = QInputDialog.getText(app, "Modifica Fascia Oraria", "Nuova fascia oraria:", text=old_text)
            if ok and new_text:
                # Usa l'ID del giorno
                day_id = DAY_TO_ID.get(day, day)
                
                fasce = app.tipologia_schedule[tipologia_id]["fasce"][day_id]
                fasce[fasce.index(old_text)] = new_text
                selected_item.setText(new_text)
                update_day_square(app, day_id, tipologia_id)
                save_data(app)  # Salva i dati dopo aver modificato una fascia oraria
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore durante la modifica della fascia oraria: {str(e)}")

def delete_fascia(app, day_id, tipologia_id, fascia_list_widget):
    try:
        selected_item = fascia_list_widget.currentItem()
        if selected_item:
            text = selected_item.text()
            reply = QMessageBox.question(app, 'Conferma Eliminazione', f"Sei sicuro di voler eliminare la fascia oraria '{text}'?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                fasce = app.tipologia_schedule[tipologia_id]["fasce"][day_id]
                fasce.remove(text)
                fascia_list_widget.takeItem(fascia_list_widget.row(selected_item))
                update_day_square(app, day_id, tipologia_id)
                save_data(app)  # Salva i dati dopo aver eliminato una fascia oraria
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore durante l'eliminazione della fascia oraria: {str(e)}")

def update_day_square(app, day, tipologia_id):
    try:
        # Trova il quadrato del giorno corretto
        for index in range(app.week_display.layout().count()):
            widget = app.week_display.layout().itemAt(index).widget()
            if widget:
                layout = widget.layout()
                if layout:
                    for i in range(layout.count()):
                        child = layout.itemAt(i).widget()
                        if isinstance(child, QPushButton):
                            if child.property("tipologia_id") == tipologia_id:
                                # Ottieni le fasce orarie per il giorno e la tipologia selezionati
                                fasce = app.tipologia_schedule.get(tipologia_id, {}).get(day, [])
                                child.setText(", ".join(fasce))
                                break
        update_week_display(app, app.tipologie_list.currentItem().text())    
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore durante l'aggiornamento del quadrato del giorno: {str(e)}")