from PyQt5.QtWidgets import (QMessageBox, QInputDialog, QPushButton, QLabel, QComboBox,
                             QListWidgetItem, QDialog, QVBoxLayout, 
                             QTimeEdit, QWidget, QSizePolicy, QListWidget)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QMessageBox

from espositore.espositore_utils import get_day_from_date, save_data, update_week_display

def add_tipologia(app):
    try:
        text, ok = QInputDialog.getText(app, "Aggiungi Tipologia", "Nome della Tipologia:")
        if ok and text:
            tipologia_id = str(len(app.tipologia_schedule) + 1)  # Genera ID unico
            app.tipologia_schedule[tipologia_id] = {"nome": text, "fasce": {}}
            update_list_widget(app.tipologie_list, text, tipologia_id)
            save_data(app)
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Errore durante l'aggiunta della tipologia: {e}")

def update_list_widget(list_widget, text, item_id):
    """Aggiunge un nuovo elemento al QListWidget con l'ID associato."""
    item = QListWidgetItem(text)
    item.setData(Qt.UserRole, item_id)  # Imposta l'ID come dato utente
    list_widget.addItem(item)

def modify_selected_tipologia(app):
    try:
        current_item = app.tipologie_list.currentItem()
        if current_item:
            tipologia_id = current_item.data(Qt.UserRole)
            modify_tipologia(app, tipologia_id)
    except Exception as e:
        print(f"Errore durante la selezione della tipologia da modificare: {e}")

def modify_tipologia(app, tipologia_id):
    try:
        current_name = app.tipologia_schedule.get(tipologia_id, {}).get("nome", "")
        new_name, ok = QInputDialog.getText(app, "Modifica Tipologia", "Nome della Tipologia:", text=current_name)
        if ok and new_name:
            app.tipologia_schedule[tipologia_id]["nome"] = new_name

            # Aggiorna la lista delle tipologie
            for index in range(app.tipologie_list.count()):
                item = app.tipologie_list.item(index)
                if item.data(Qt.UserRole) == tipologia_id:
                    item.setText(new_name)
                    break
            save_data(app)  # Salva i dati dopo aver modificato una tipologia
            
    except Exception as e:
        print(f"Errore durante la modifica della tipologia: {e}")

def remove_tipologia(app):
    selected_item = app.tipologie_list.currentItem()
    if not selected_item:
        QMessageBox.critical(app, "Errore", "Nessuna tipologia selezionata!")
        return
    
    tipologia_id = selected_item.data(Qt.UserRole)
    if tipologia_id in app.tipologia_schedule:
        del app.tipologia_schedule[tipologia_id]
        for person_id in app.person_schedule:
            for day in app.person_schedule[person_id]:
                if app.person_schedule[person_id][day]["tipologia"] == tipologia_id:
                    del app.person_schedule[person_id][day]
        app.tipologie_list.takeItem(app.tipologie_list.row(selected_item))
        update_week_display(app, None)
        save_data(app)  # Salva i dati dopo aver eliminato una tipologia
        
    else:
        QMessageBox.critical(app, "Errore", "Errore nel trovare l'ID della tipologia!")

def display_person_details(app, item):
    try:
        # Ottieni l'ID del proclamatore selezionato
        person_id = item.data(Qt.UserRole)
        person = app.person_schedule.get(person_id, {})
        
        # Aggiorna i dettagli del proclamatore
        app.detail_text.clear()
        
        if person:
            app.detail_text.append(f"Nome: {person.get('name', 'N/A')}")
            app.detail_text.append(f"ID: {person_id}")
            
            # Mappa degli ID dei giorni ai loro nomi
            giorno_map = {
                '1': 'Lunedì',
                '2': 'Martedì',
                '3': 'Mercoledì',
                '4': 'Giovedì',
                '5': 'Venerdì',
                '6': 'Sabato',
                '7': 'Domenica',
            }

            # Mappa degli ID delle tipologie ai loro nomi
            tipologia_map = {tipologia_id: tipologia["nome"] for tipologia_id, tipologia in app.tipologia_schedule.items()}

            # Mostra la disponibilità per la tipologia
            availability = person.get('availability', {})
            if availability:
                for tipologia_id, giorni in availability.items():
                    tipologia_nome = tipologia_map.get(tipologia_id, 'N/A')  # Ottieni il nome della tipologia
                    app.detail_text.append(f"\nTipologia: {tipologia_nome}")
                    for giorno_id, fasce in giorni.items():
                        giorno_n = get_day_from_date(giorno_id)
                        print(giorno_n)
                        #giorno_n = giorno_map.get(giorno_id, 'N/A')  # Ottieni il nome del giorno
                        if giorno_n == 'N/A':
                            # Se giorno_n è 'N/A', verifica che giorno_id sia un intero
                            giorno_id = str(giorno_id)  # Assicurati che sia una stringa
                            giorno_n = giorno_map.get(giorno_id, 'N/A')  # Riprova a ottenere il nome
                        app.detail_text.append(f"{giorno_n} : {giorno_id}")  # Mostra l'ID del giorno
                        for fascia in fasce:
                            app.detail_text.append(f"    Fascia: {fascia}")
            else:
                app.detail_text.append("Nessuna disponibilità disponibile.")
        else:
            app.detail_text.append("Dettagli non disponibili per il proclamatore selezionato.")
            
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

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

