from PyQt5.QtWidgets import (QMessageBox, QInputDialog, QPushButton, QLabel, QComboBox,
                             QListWidgetItem, QDialog, QVBoxLayout, 
                             QTimeEdit, QWidget, QSizePolicy, QListWidget)

from PyQt5.QtCore import Qt
from espositore.espositore_utils import get_day_from_date, save_data, update_week_display
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

# Funzione per mostrare i dettagli del proclamatore
def update_person_details(app, person_id):
    try:
        if person_id in app.person_schedule:
            app.detail_text.clear()
            availability = app.person_schedule[person_id]["availability"]
            tipologia_map = {t_id: t_info['nome'] for t_id, t_info in app.tipologia_schedule.items()}
            
            if availability:
                for tipologia_id, giorni in availability.items():
                    tipologia_nome = tipologia_map.get(tipologia_id, 'N/A')
                    app.detail_text.append(f"\nTipologia: {tipologia_nome}")
                    
                    for giorno_id, fasce in giorni.items():
                        # Usa la funzione per ottenere il nome del giorno dalla data
                        giorno_nome = get_day_from_date(giorno_id)
                        app.detail_text.append(f"  Giorno (ID: {giorno_id}): {giorno_nome}")
                        
                        for fascia in fasce:
                            app.detail_text.append(f"    Fascia: {fascia}")
            else:
                app.detail_text.append("Nessuna disponibilità disponibile.")
        else:
            app.detail_text.setPlainText("Nessuna disponibilità registrata per questo proclamatore.")
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Errore nell'aggiornamento del dettaglio: {str(e)}")

# Funzione per aggiornare la disponibilità del proclamatore
def update_person_availability(app, date, tipologia_id, fascia, dialog):
    try:
        # Ottieni l'ID del proclamatore selezionato
        selected_person_id = app.person_list.currentItem().data(Qt.UserRole)

        if not selected_person_id:
            QMessageBox.warning(app, "Attenzione", "Nessun proclamatore selezionato.")
            return

        # Verifica se il proclamatore ha già delle disponibilità registrate
        if selected_person_id not in app.person_schedule:
            app.person_schedule[selected_person_id] = {"availability": {}}
        
        # Aggiungi la tipologia se non esiste già
        if tipologia_id not in app.person_schedule[selected_person_id]["availability"]:
            app.person_schedule[selected_person_id]["availability"][tipologia_id] = {}

        # Aggiungi la disponibilità per la data specifica
        day_id = date.toString("yyyy-MM-dd")  # Usa la data completa come chiave
        if day_id not in app.person_schedule[selected_person_id]["availability"][tipologia_id]:
            app.person_schedule[selected_person_id]["availability"][tipologia_id][day_id] = []

        # Aggiungi la fascia oraria selezionata
        if fascia not in app.person_schedule[selected_person_id]["availability"][tipologia_id][day_id]:
            app.person_schedule[selected_person_id]["availability"][tipologia_id][day_id].append(fascia)

        # Salva i dati aggiornati
        save_data(app)

        # Aggiorna la visualizzazione del dettaglio
        update_person_details(app, selected_person_id)
        
        dialog.accept()  # Chiudi il dialogo una volta completato
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore durante l'aggiornamento della disponibilità: {str(e)}")

def show_availability_dialog(app, selected_date):
    try:
        dialog = QDialog()  # Cambiato a QDialog
        dialog.setWindowTitle("Aggiungi Disponibilità")
        layout = QVBoxLayout(dialog)

        # Nome del giorno
        day_name = selected_date.toString("dddd").capitalize()
        print(f"Giorno selezionato: {day_name}")

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
        print(f"ID del giorno selezionato: {day_id}")

        day_label = QLabel(f"Giorno selezionato: {day_name} (ID: {day_id})")
        layout.addWidget(day_label)

        tipologia_label = QLabel("Seleziona la tipologia:")
        layout.addWidget(tipologia_label)

        tipologia_combo = QComboBox()
        for tipologia_id, tipologia in app.tipologia_schedule.items():
            tipologia_combo.addItem(tipologia['nome'], tipologia_id)
        layout.addWidget(tipologia_combo)

        fascia_label = QLabel("Seleziona la fascia oraria:")
        layout.addWidget(fascia_label)

        fascia_combo = QComboBox()
        layout.addWidget(fascia_combo)

        confirm_button = QPushButton("Conferma")
        confirm_button.setEnabled(False)  # Inizialmente disattivato
        layout.addWidget(confirm_button)

        def update_fasce():
            selected_tipologia_id = tipologia_combo.currentData()
            print(f"Tipologia selezionata ID: {selected_tipologia_id}, Giorno: {day_name}")

            # Filtra le fasce orarie in base all'ID del giorno e alla tipologia selezionata
            fasce = app.tipologia_schedule[selected_tipologia_id]['fasce'].get(day_id, [])
            print(f"Fasce orarie disponibili: {fasce}")

            fascia_combo.clear()
            if fasce:
                fascia_combo.addItems(fasce)
                confirm_button.setEnabled(True)  # Attiva il pulsante se ci sono fasce
            else:
                fascia_combo.addItem("Nessuna fascia disponibile")
                confirm_button.setEnabled(False)  # Disattiva il pulsante se non ci sono fasce

        tipologia_combo.currentIndexChanged.connect(update_fasce)
        update_fasce()  # Aggiorna all'inizio

        confirm_button.clicked.connect(lambda: on_confirm(app, selected_date, tipologia_combo.currentData(), fascia_combo.currentText(), dialog))

        dialog.setLayout(layout)
        dialog.exec_()  # Usa exec_() per mostrare il dialogo come modale

    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

def on_confirm(app, selected_date, selected_tipologia_id, selected_fascia, dialog):
    if selected_tipologia_id is None:
        QMessageBox.warning(dialog, "Attenzione", "Nessuna tipologia selezionata.")
        return

    person_item = app.person_list.currentItem()  # Ottieni l'elemento selezionato
    if person_item is None:
        QMessageBox.warning(dialog, "Attenzione", "Nessun proclamatore selezionato.")
        return

    if selected_fascia:
        update_person_availability(app, selected_date, selected_tipologia_id, selected_fascia, dialog)
    else:
        QMessageBox.warning(dialog, "Attenzione", "Devi selezionare una fascia oraria.")
