from PyQt5.QtWidgets import (QMessageBox, QInputDialog, QPushButton, QLabel, QComboBox,
                             QListWidgetItem, QDialog, QVBoxLayout, QTimeEdit)
from PyQt5.QtCore import Qt
from espositore.espositore_utils import save_data, update_last_modification_time, update_week_display_and_data
from utils.logging_custom import logging_custom

def add_tipo_luogo(app):
    try:
        text, ok = QInputDialog.getText(app, "Aggiungi Tipologia\\Luogo", "Nome Tipologia\\Luogo:")
        if ok and text:
            tipo_luogo_id = f'tipo_luogo_{len(app.tipo_luogo_schedule) + 1}'  # Genera ID unico
            app.tipo_luogo_schedule[tipo_luogo_id] = {"nome": text, "fasce": {}, "attivo": False}
            update_list_tipo_luogo_widget(app.tipologie_list, text, tipo_luogo_id)
            save_data(app)
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Errore durante l'aggiunta della tipologia: {e}")

def update_list_tipo_luogo_widget(list_widget, text, item_id):
    """Aggiunge un nuovo elemento al QListWidget con l'ID associato."""
    item = QListWidgetItem(text)
    item.setData(Qt.UserRole, item_id)  # Imposta l'ID come dato utente
    list_widget.addItem(item)

def modify_selected_tipo_luogo(app):
    try:
        current_item = app.tipologie_list.currentItem()
        if current_item:
            tipo_luogo_id = current_item.data(Qt.UserRole)
            modify_tipo_luogo(app, tipo_luogo_id)
    except Exception as e:
        logging_custom(app, "error", f"Errore durante la selezione della tipologia da modificare: {e}")

def modify_tipo_luogo(app, tipo_luogo_id):
    try:
        current_name = app.tipo_luogo_schedule.get(tipo_luogo_id, {}).get("nome", "")
        new_name, ok = QInputDialog.getText(app, "Modifica Tipologia\\Luogo", "Nome Tipologia\\Luogo:", text=current_name)
        if ok and new_name:
            app.tipo_luogo_schedule[tipo_luogo_id]["nome"] = new_name

            # Aggiorna la lista delle tipologie
            for index in range(app.tipologie_list.count()):
                item = app.tipologie_list.item(index)
                if item.data(Qt.UserRole) == tipo_luogo_id:
                    item.setText(new_name)
                    break
            save_data(app)  # Salva i dati dopo aver modificato una tipologia
            
    except Exception as e:
        logging_custom(app, "error", f"Errore durante la modifica della tipologia: {e}")

def remove_tipo_luogo(app):
    selected_item = app.tipologie_list.currentItem()
    if not selected_item:
        QMessageBox.critical(app, "Errore", "Nessuna tipologia selezionata!")
        return
    
    tipo_luogo_id = selected_item.data(Qt.UserRole)
    if tipo_luogo_id in app.tipo_luogo_schedule:
        del app.tipo_luogo_schedule[tipo_luogo_id]
        
        # Rimuovi le fasce di questa tipologia dalle disponibilità delle persone
        for person_id, person_data in app.people.items():
            availability = person_data.get("availability", {})
            if tipo_luogo_id in availability:
                del availability[tipo_luogo_id]

        app.tipologie_list.takeItem(app.tipologie_list.row(selected_item))
        update_week_display_and_data(app, None)
        save_data(app)  # Salva i dati dopo aver eliminato una tipologia
        
    else:
        QMessageBox.critical(app, "Errore", "Errore nel trovare l'ID della tipologia!")

def show_day_dialog(app, day):
    try:
        dialog = QDialog()
        dialog.setWindowTitle("Aggiungi Fascia Oraria")
        layout = QVBoxLayout(dialog)

        tipo_luogo_label = QLabel("Seleziona la tipologia:")
        layout.addWidget(tipo_luogo_label)
        
        tipo_luogo_combo = QComboBox()
        for tipo_luogo_id, tipologia in app.tipo_luogo_schedule.items():
            tipo_luogo_combo.addItem(tipologia['nome'], tipo_luogo_id)
        layout.addWidget(tipo_luogo_combo)

        fascia_inizio_label = QLabel("Fascia Oraria Inizio:")
        layout.addWidget(fascia_inizio_label)
        fascia_inizio_time = QTimeEdit()
        layout.addWidget(fascia_inizio_time)

        fascia_fine_label = QLabel("Fascia Oraria Fine:")
        layout.addWidget(fascia_fine_label)
        fascia_fine_time = QTimeEdit()
        layout.addWidget(fascia_fine_time)

        confirm_button = QPushButton("Aggiungi Fascia Oraria")
        confirm_button.clicked.connect(lambda: add_time_slot(app, day, tipo_luogo_combo.currentData(), fascia_inizio_time.time().toString(), fascia_fine_time.time().toString(), dialog))
        layout.addWidget(confirm_button)

        dialog.setLayout(layout)
        dialog.exec_()  # Utilizzare exec_() per il dialogo modale

    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

def add_time_slot(app, day, tipo_luogo_id, start_time, end_time, dialog):
    try:
        # Verifica se la tipologia esiste
        if tipo_luogo_id not in app.tipo_luogo_schedule:
            QMessageBox.warning(dialog, "Attenzione", "La tipologia selezionata non esiste.")
            return

        # Aggiungi la fascia oraria alla tipologia
        if day not in app.tipo_luogo_schedule[tipo_luogo_id]["fasce"]:
            app.tipo_luogo_schedule[tipo_luogo_id]["fasce"][day] = []

        # Aggiungi la fascia oraria
        app.tipo_luogo_schedule[tipo_luogo_id]["fasce"][day].append(f"{start_time} - {end_time}")

        # Aggiorna la visualizzazione della settimana
        update_week_display_and_data(app, app.tipologie_list.currentItem().text())

        # Chiudi il dialogo
        dialog.accept()
        
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore durante l'aggiunta della fascia oraria: {str(e)}")

def fix_orari(app):
    """
    Questa funzione cerca tipologie con fasce vuote e cerca di popolarle 
    utilizzando le fasce di altre tipologie con nomi simili.
    """
    try:
        similar_types = {}

        # Step 1: Identifica le tipologie con e senza fasce
        for tipo_luogo_id, tipo_luogo_data in app.tipo_luogo_schedule.items():
            nome = tipo_luogo_data.get("nome", "").strip()
            fasce = tipo_luogo_data.get("fasce", {})

            # Se le fasce sono vuote, aggiungiamo al gruppo di tipologie da "fixare"
            if not fasce:
                # Gestisci il caso per "Piazza\\Lido"
                if "\\" in nome:
                    base_names = nome.split("\\")
                    for base_name in base_names:
                        base_name = base_name.strip()
                        if base_name.lower().startswith("piazza"):
                            # Popola fasce da tipologie che iniziano con "Piazza"
                            similar_types[base_name] = {"with_fasce": [], "without_fasce": [tipo_luogo_id]}
                        elif base_name.lower() == "lido":
                            # Popola fasce da tipologie di "Lungomare"
                            for lungomare_id, lungomare_data in app.tipo_luogo_schedule.items():
                                if "lungomare" in lungomare_data.get("nome", "").lower():
                                    similar_types.setdefault(lungomare_data["nome"], {"with_fasce": [], "without_fasce": []})["with_fasce"].append((lungomare_id, lungomare_data["fasce"]))
                            similar_types[base_name] = {"with_fasce": similar_types.get("Lungomare", {}).get("with_fasce", []), "without_fasce": [tipo_luogo_id]}
                else:
                    # Gestisci normalmente
                    base_name = find_base_name(nome)
                    similar_types.setdefault(base_name, {"with_fasce": [], "without_fasce": []})["without_fasce"].append(tipo_luogo_id)

            else:
                # Popola le fasce già esistenti
                base_name = find_base_name(nome)
                similar_types.setdefault(base_name, {"with_fasce": [], "without_fasce": []})["with_fasce"].append((tipo_luogo_id, fasce))

        # Step 2: Popola le fasce mancanti utilizzando quelle simili
        for base_name, tipo_groups in similar_types.items():
            if tipo_groups["with_fasce"]:
                for tipo_luogo_id in tipo_groups["without_fasce"]:
                    # Prende le fasce dalla prima tipologia simile trovata
                    fasce_source_id, fasce_source = tipo_groups["with_fasce"][0]
                    app.tipo_luogo_schedule[tipo_luogo_id]["fasce"] = fasce_source
                    
                    logging_custom(app, "debug", f"Fasce per '{app.tipo_luogo_schedule[tipo_luogo_id]['nome']}' "
                                                f"popolate con quelle di '{app.tipo_luogo_schedule[fasce_source_id]['nome']}'.")

        QMessageBox.information(app, "Fix Orari", "Le fasce sono state corrette con successo.")
        save_data(app)
    except Exception as e:
        logging_custom(app, "error", f"Errore durante il fix delle fasce: {str(e)}")
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore durante il fix delle fasce: {str(e)}")

def find_base_name(nome):
    """
    Funzione helper per estrarre il nome base, escludendo eventuali parti tra parentesi o parole accessorie.
    Gestisce anche il caso di split per nomi come 'Piazza\\Lido'.
    """
    # Se ci sono parentesi, estrai solo la parte iniziale
    if "(" in nome:
        nome = nome.split("(")[0].strip()

    # Split del nome per gestire casi come 'Piazza\\Lido'
    base_names = nome.split("\\")
    
    # Prendere la prima parte di base_names
    first_part = base_names[0].strip()

    # Restituisce il nome base considerando le parole chiave specifiche
    if first_part.lower().startswith("piazza"):
        return "Piazza"
    elif first_part.lower().startswith("piazzetta"):
        return "Piazza"
    elif first_part.lower().startswith("lungomare"):
        return "Piazza"
    elif first_part.lower().startswith("lido"):
        return "Lido"
    elif first_part.lower().startswith("lungomare"):
        return "Lungomare"
    elif first_part.lower().startswith("mercato"):
        return "Mercato"
    elif first_part.lower().startswith("istituto"):
        return "Scuola"
    elif first_part.lower().startswith("scuola"):
        return "Scuola"
    
    # Restituisce la prima parola significativa
    return first_part.strip()

def fix_proclamatori(app):
    try:
        # Itera su tutti i proclamatori nel people
        for person_id, person_data in app.people.items():
            availability = person_data.get("availability", {})
            tipo_luogo_to_remove = []  # Lista per tenere traccia dei tipo_luogo da rimuovere
            
            # Itera su tutti i tipi di luogo
            for tipo_luogo_id, tipo_luogo_data in app.tipo_luogo_schedule.items():
                if tipo_luogo_id not in availability:  # Se il proclamatore non ha disponibilità per questo luogo
                    base_name = find_base_name(tipo_luogo_data["nome"])
                    
                    # Cerca una tipologia simile con disponibilità
                    similar_luogo_id = find_similar_luogo(app, base_name, availability)
                    
                    if similar_luogo_id:
                        # Prendi le fasce orarie del luogo simile
                        similar_availability = availability[similar_luogo_id]
                        
                        # Aggiungi le fasce orarie alla disponibilità del luogo attuale
                        availability[tipo_luogo_id] = similar_availability
                        
                        logging_custom(app, "debug", f"Aggiunta disponibilità per '{tipo_luogo_data['nome']}' "
                                                     f"utilizzando fasce di '{app.tipo_luogo_schedule[similar_luogo_id]['nome']}' "
                                                     f"per il proclamatore {person_id}.")

                        tipo_luogo_to_remove.append(similar_luogo_id)  # Aggiungi il tipo luogo vecchio alla lista da rimuovere
            
            # Rimuovi i tipo_luogo vecchi dalla disponibilità
            for tipo_luogo_id in tipo_luogo_to_remove:
                if tipo_luogo_id in availability:
                    del availability[tipo_luogo_id]
                    logging_custom(app, "debug", f"Rimosso '{app.tipo_luogo_schedule[tipo_luogo_id]['nome']}' "
                                                  f"dalla disponibilità del proclamatore {person_id}.")

        # Salva i dati dopo il fix
        save_data(app)
        QMessageBox.information(app, "Fix Disponibilità", "La disponibilità dei proclamatori è stata corretta con successo.")
    
    except Exception as e:
        logging_custom(app, "error", f"Errore durante il fix delle disponibilità dei proclamatori: {str(e)}")
        QMessageBox.critical(app, "Errore", f"Errore durante il fix delle disponibilità dei proclamatori: {str(e)}")


def find_similar_luogo(app, base_name, availability):
    """
    Trova un luogo simile tra quelli con disponibilità nel proclamatore corrente.
    """
    for tipo_luogo_id, tipo_luogo_data in app.tipo_luogo_schedule.items():
        if find_base_name(tipo_luogo_data["nome"]) == base_name and tipo_luogo_id in availability:
            return tipo_luogo_id
    return None

def aggiorna_genere_sino(app):
    if app.genere_si_radio.isChecked():
        app.autoabbinamento_gender_sino["same_gender"] = True
    elif app.genere_no_radio.isChecked():
        app.autoabbinamento_gender_sino["same_gender"] = False
    
    # Salva il dizionario aggiornato nel file JSON
    save_data(app)    

def aggiorna_numero_utilizzi(tipo, valore, app):
    """
    Aggiorna il numero di utilizzi settimanali per pionieri o proclamatori.
    
    :param tipo: Stringa "pionieri" o "proclamatori" per identificare il gruppo.
    :param valore: Valore selezionato dallo spinbox.
    :param app: Istanza dell'applicazione o del contesto corrente.
    """
    if tipo == "pionieri_mes":
        app.numero_utilizzi["numero_utilizzi_mensile_pionieri"] = valore
        print(f"Aggiornato numero di utilizzi mensile per pionieri a {valore}")
    elif tipo == "proclamatori_mes":
        app.numero_utilizzi["numero_utilizzi_mensile_proclamatori"] = valore
        print(f"Aggiornato numero di utilizzi mensile per proclamatori a {valore}")
    elif tipo == "pionieri_sett":
        app.numero_utilizzi["numero_utilizzi_settimanale_pionieri"] = valore
        print(f"Aggiornato numero di utilizzi settimanali per pionieri a {valore}")
    elif tipo == "proclamatori_sett":
        app.numero_utilizzi["numero_utilizzi_settimanale_proclamatori"] = valore
        print(f"Aggiornato numero di utilizzi settimanali per proclamatori a {valore}")

    save_data(app)        