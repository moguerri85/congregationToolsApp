from PyQt5.QtWidgets import (QMessageBox, QInputDialog, 
                             QListWidgetItem)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox

from utils.espositore_utils import save_data, update_person_details, update_week_display

def add_person(app):
    try:
        # Mostra una finestra di input per il nome della persona
        name, ok = QInputDialog.getText(app, "Aggiungi Proclamatore", "Nome del Proclamatore:")
        
        if ok and name:
            # Genera un ID univoco per la persona (ad esempio, un contatore o UUID)
            person_id = str(len(app.people) + 1)
            
            # Aggiungi la persona al dizionario
            app.people[person_id] = name
            
            # Aggiungi la persona alla lista visuale
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, person_id)
            app.person_list.addItem(item)
            
            # Salva i dati
            save_data(app)
            
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")


def remove_person(app):
    selected_item = app.person_list.currentItem()
    if not selected_item:
        QMessageBox.critical(app, "Errore", "Nessun proclamatore selezionato!")
        return
    
    person_id = selected_item.data(Qt.UserRole)
    if person_id in app.people:
        del app.people[person_id]
        del app.person_schedule[person_id]
        app.person_list.takeItem(app.person_list.row(selected_item))
        update_person_details(app, person_id)
        save_data(app)
    else:
        QMessageBox.critical(app, "Errore", "Errore nel trovare l'ID del proclamatore!")

def add_tipologia(app):
    try:
        text, ok = QInputDialog.getText(app, "Aggiungi Tipologia", "Nome della Tipologia:")
        if ok and text:
            # Genera un ID unico per la tipologia
            tipologia_id = str(len(app.tipologia_schedule) + 1)
            app.tipologia_schedule[tipologia_id] = {"nome": text, "fasce": []}

            # Aggiungi la tipologia alla lista
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, tipologia_id)
            app.tipologie_list.addItem(item)
            save_data(app)  # Salva i dati dopo aver aggiunto una tipologia
            
    except Exception as e:
        print(f"Errore durante l'aggiunta della tipologia: {e}")

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
            
            # Mostra la disponibilità per la tipologia
            availability = person.get('availability', {})
            if availability:
                for tipologia, giorni in availability.items():
                    app.detail_text.append(f"\nTipologia: {tipologia}")
                    for giorno, fasce in giorni.items():
                        app.detail_text.append(f"  Giorno: {giorno}")
                        for fascia in fasce:
                            app.detail_text.append(f"    Fascia: {fascia}")
            else:
                app.detail_text.append("Nessuna disponibilità disponibile.")
        else:
            app.detail_text.append("Dettagli non disponibili per il proclamatore selezionato.")
            
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

def update_person_availability(app, date, tipologia, fascia, dialog):
    try:
        if tipologia not in app.tipologia_schedule:
            app.tipologia_schedule[tipologia] = {}
        if date not in app.tipologia_schedule[tipologia]:
            app.tipologia_schedule[tipologia][date] = []

        # Aggiungi la fascia oraria
        app.tipologia_schedule[tipologia][date].append(fascia)

        # Aggiorna la visualizzazione
        update_week_display(app, app.tipologie_list.currentItem().text())

        # Chiudi il dialogo
        dialog.accept()

    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore durante l'aggiornamento della disponibilità: {str(e)}")
