from PyQt5.QtWidgets import (QMessageBox, QInputDialog, QPushButton, QLabel, QComboBox,
                             QListWidgetItem, QDialog, QVBoxLayout, 
                             QWidget, QSizePolicy, QListWidget)

from PyQt5.QtCore import Qt
from espositore.espositore_utils import get_day_from_date, save_data
import uuid

def add_person(app):
    try:
        name, ok = QInputDialog.getText(app, "Aggiungi Proclamatore", "Nome del Proclamatore:")
        if ok and name:
            person_id = str(uuid.uuid4())
            app.people[person_id] = name
            
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, person_id)
            app.person_list.addItem(item)
            
            # Initialize person_schedule entry for the new person
            app.person_schedule[person_id] = {"availability": {}}
            
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

# Funzione per mostrare i dettagli del proclamatore
def update_person_details(app, person_id):
    try:
        if person_id in app.person_schedule:
            app.detail_text.clear()
            availability = app.person_schedule[person_id]["availability"]
            tipo_luogo_map = {t_id: t_info['nome'] for t_id, t_info in app.tipo_luogo_schedule.items()}
            
            if availability:
                for tipo_luogo_id, giorni in availability.items():
                    tipo_luogo_nome = tipo_luogo_map.get(tipo_luogo_id, 'N/A')
                    app.detail_text.append(f"\nTipo\\Luogo: {tipo_luogo_nome}")
                    
                    for day_id, fasce in giorni.items():
                        app.detail_text.append(f"  Data: {day_id}")
                        
                        for fascia in fasce:
                            app.detail_text.append(f"    Fascia: {fascia}")
            else:
                app.detail_text.append("Nessuna disponibilità disponibile.")
        else:
            app.detail_text.setPlainText("Nessuna disponibilità registrata per questo proclamatore.")
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Errore nell'aggiornamento del dettaglio: {str(e)}")

# Funzione per aggiornare la disponibilità del proclamatore
def update_person_availability(app, date, tipo_luogo_id, fascia, dialog):
    try:
        selected_person_id = app.person_list.currentItem().data(Qt.UserRole)

        if not selected_person_id:
            QMessageBox.warning(app, "Attenzione", "Nessun proclamatore selezionato.")
            return

        if selected_person_id not in app.person_schedule:
            app.person_schedule[selected_person_id] = {"availability": {}}

        # Aggiungi la disponibilità per la data specifica
        day_id = date.toString("yyyy-MM-dd")  # Usa la data completa come chiave
        if tipo_luogo_id not in app.person_schedule[selected_person_id]["availability"]:
            app.person_schedule[selected_person_id]["availability"][tipo_luogo_id] = {}

        if day_id not in app.person_schedule[selected_person_id]["availability"][tipo_luogo_id]:
            app.person_schedule[selected_person_id]["availability"][tipo_luogo_id][day_id] = []

        # Aggiungi la fascia oraria selezionata
        if fascia not in app.person_schedule[selected_person_id]["availability"][tipo_luogo_id][day_id]:
            app.person_schedule[selected_person_id]["availability"][tipo_luogo_id][day_id].append(fascia)

        save_data(app)

        update_person_details(app, selected_person_id)
        
        dialog.accept()  # Chiudi il dialogo una volta completato
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore durante l'aggiornamento della disponibilità: {str(e)}")

def show_availability_dialog(app, selected_date):
    try:
        dialog = QDialog()  # Cambiato a QDialog
        dialog.setWindowTitle("Aggiungi Disponibilità")
        layout = QVBoxLayout(dialog)

        day_name = selected_date.toString("dddd").capitalize()
        day_id_map = {
            "Lunedì": "1",
            "Martedì": "2",
            "Mercoledì": "3",
            "Giovedì": "4",
            "Venerdì": "5",
            "Sabato": "6",
            "Domenica": "7"
        }
        day_id = day_id_map.get(day_name)
            
        day_name = day_name.encode('utf-8').decode('utf-8')  # Ensure it's in UTF-8 format

        day_label = QLabel(f"Giorno selezionato: {day_name} (ID: {day_id})")
        layout.addWidget(day_label)

        tipo_luogo_label = QLabel("Seleziona il tipo\\luogo:")
        layout.addWidget(tipo_luogo_label)

        tipo_luogo_combo = QComboBox()
        for tipo_luogo_id, tipo_luogo in app.tipo_luogo_schedule.items():
            tipo_luogo_combo.addItem(tipo_luogo['nome'], tipo_luogo_id)
        layout.addWidget(tipo_luogo_combo)

        fascia_label = QLabel("Seleziona la fascia oraria:")
        layout.addWidget(fascia_label)

        fascia_combo = QComboBox()
        layout.addWidget(fascia_combo)

        confirm_button = QPushButton("Conferma")
        confirm_button.setEnabled(False)  # Inizialmente disattivato
        layout.addWidget(confirm_button)

        def update_fasce():
            selected_tipo_luogo_id = tipo_luogo_combo.currentData()

            fasce = app.tipo_luogo_schedule[selected_tipo_luogo_id]['fasce'].get(day_id, [])
            fascia_combo.clear()
            if fasce:
                fascia_combo.addItems(fasce)
                confirm_button.setEnabled(True)
            else:
                fascia_combo.addItem("Nessuna fascia disponibile")
                confirm_button.setEnabled(False)

        tipo_luogo_combo.currentIndexChanged.connect(update_fasce)
        update_fasce()  # Aggiorna all'inizio

        confirm_button.clicked.connect(lambda: on_confirm(app, selected_date, tipo_luogo_combo.currentData(), fascia_combo.currentText(), dialog))

        dialog.setLayout(layout)
        dialog.exec_()  # Usa exec_() per mostrare il dialogo come modale

    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

def on_confirm(app, selected_date, selected_tipo_luogo_id, selected_fascia, dialog):
    if selected_tipo_luogo_id is None:
        QMessageBox.warning(dialog, "Attenzione", "Nessun tipo\\luogo selezionato.")
        return

    person_item = app.person_list.currentItem()  # Ottieni l'elemento selezionato
    if person_item is None:
        QMessageBox.warning(dialog, "Attenzione", "Nessun proclamatore selezionato.")
        return

    if selected_fascia:
        update_person_availability(app, selected_date, selected_tipo_luogo_id, selected_fascia, dialog)
    else:
        QMessageBox.warning(dialog, "Attenzione", "Devi selezionare una fascia oraria.")
