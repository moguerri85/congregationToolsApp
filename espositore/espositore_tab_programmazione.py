from PyQt5.QtWidgets import (QVBoxLayout, QMenu, QLabel, QListWidget, QPushButton, 
                             QDialog, QComboBox, QMessageBox, QInputDialog)
from PyQt5.QtCore import QDate

def show_programmazione_dialog(app, date):
    """Mostra il dialogo per la selezione di tipologia, fascia oraria e proclamatori disponibili."""
    
    dialog = QDialog()
    dialog.setWindowTitle(f"Selezione per il giorno {date.toString('dd/MM/yyyy')}")

    layout = QVBoxLayout(dialog)

    # Seleziona Tipologia
    layout.addWidget(QLabel("Seleziona Tipologia"))
    tipologia_combo = QComboBox()
    tipologia_combo.addItem("")  # Primo item vuoto

    day_of_week = str(date.dayOfWeek())

    # Popola il QComboBox delle tipologie
    if app.tipo_luogo_schedule:
        for tipo, info in app.tipo_luogo_schedule.items():
            if info.get('attivo', False) and 'fasce' in info and day_of_week in info['fasce']:
                tipologia_combo.addItem(info['nome'], tipo)

    if tipologia_combo.count() == 1:
        tipologia_combo.addItem("Nessuna tipologia attiva disponibile per il giorno selezionato")

    layout.addWidget(tipologia_combo)

    # Seleziona Fascia Oraria
    layout.addWidget(QLabel("Seleziona Fascia Oraria"))
    fascia_combo = QComboBox()
    fascia_combo.addItem("")  # Primo item vuoto

    def update_fasce():
        """Aggiorna le fasce orarie in base alla tipologia selezionata."""
        fascia_combo.clear()  # Pulisce le fasce precedenti
        selected_tipo = tipologia_combo.currentData()  # Ottieni il tipo selezionato

        if selected_tipo and selected_tipo in app.tipo_luogo_schedule:
            fasce = app.tipo_luogo_schedule[selected_tipo]['fasce'].get(day_of_week, [])
            for fascia in fasce:
                fascia_combo.addItem(fascia)

            # Aggiorna i proclamatori in base alla tipologia e fascia selezionata
            update_proclamatori(selected_tipo, fascia_combo.currentText())

    # Connessione al cambiamento della tipologia
    tipologia_combo.currentIndexChanged.connect(update_fasce)

    layout.addWidget(fascia_combo)

    # Seleziona Proclamatori disponibili
    layout.addWidget(QLabel("Seleziona Proclamatori Disponibili"))
    proclamatori_list = QListWidget()
    proclamatori_list.setSelectionMode(QListWidget.MultiSelection)
    layout.addWidget(proclamatori_list)

    def update_proclamatori(selected_tipo, selected_fascia):
        """Aggiorna la lista dei proclamatori in base alla tipologia e fascia selezionate."""
        proclamatori_list.clear()  # Pulisci la lista esistente

        if selected_tipo and selected_fascia:
            date_key = date.toString('yyyy-MM-dd')  # Formato della data
            day_of_week = str(date.dayOfWeek())  # Ottenere il giorno della settimana

            print(f"Verifica disponibilità per la tipologia: {selected_tipo}, fascia: {selected_fascia}, data: {date_key}")  # Debug

            for proclamatore_id, proclamatore_nome in app.people.items():
                # Verifica se il proclamatore ha disponibilità per la tipologia selezionata
                availability = app.person_schedule.get(proclamatore_id, {}).get('availability', {})
                
                print(f"Selected tipo: {selected_tipo}")  # Debug
                print(availability)
                
                if selected_tipo in availability:
                    # Controlla se il proclamatore ha disponibilità per il giorno della settimana
                    print(f"Controllo disponibilità per {availability[selected_tipo]})")  # Debug
                    if day_of_week in availability[selected_tipo]:
                        # Verifica se la fascia selezionata è presente
                        available_times = availability[selected_tipo][day_of_week]
                        if selected_fascia in available_times:
                            proclamatori_list.addItem(proclamatore_nome)  # Aggiungi il proclamatore alla lista
                            print(f"Aggiunto proclamatore: {proclamatore_nome}")  # Debug
                        else:
                            print(f"{proclamatore_nome} non disponibile nella fascia {selected_fascia} per il giorno della settimana")  # Debug

                    # Controlla se ci sono disponibilità per la data specifica
                    elif date_key in availability[selected_tipo]:
                        # Verifica se la fascia selezionata è presente per la data specifica
                        available_times = availability[selected_tipo][date_key]
                        if selected_fascia in available_times:
                            proclamatori_list.addItem(proclamatore_nome)  # Aggiungi il proclamatore alla lista
                            print(f"Aggiunto proclamatore per data specifica: {proclamatore_nome}")  # Debug
                    else:
                        print(f"{proclamatore_nome} non ha disponibilità per il giorno {day_of_week}")  # Debug
                else:
                    print(f"{proclamatore_nome} non ha disponibilità per la tipologia {selected_tipo}")  # Debug

    # Connessione al cambiamento della fascia
    fascia_combo.currentIndexChanged.connect(lambda: update_proclamatori(tipologia_combo.currentData(), fascia_combo.currentText()))

    # Aggiungi il pulsante di conferma
    confirm_button = QPushButton("Conferma")
    confirm_button.clicked.connect(lambda: confirm_selections(app, date, 
        tipologia_combo.currentText(), fascia_combo.currentText(), proclamatori_list.selectedItems(), dialog))
    layout.addWidget(confirm_button)

    dialog.setLayout(layout)
    dialog.exec_()

def confirm_selections(app, date, tipologia, fascia, selected_proclamatori, dialog):
    """Conferma le selezioni e aggiorna il calendario con le informazioni."""

    if not selected_proclamatori:
        QMessageBox.warning(None, "Errore", "Seleziona almeno un proclamatore.")
        return

    # Ottieni i nomi dei proclamatori selezionati
    proclamatori_names = [item.text() for item in selected_proclamatori]

    # Formatta il testo da visualizzare nel calendario o nella lista
    entry_text = f"{date.toString('dd/MM/yyyy')} - Tipologia: {tipologia}, Fascia: {fascia}, Proclamatori: {', '.join(proclamatori_names)}"

    # Aggiungi l'assegnazione nella lista della programmazione
    app.programmazione_list.addItem(entry_text)

    # Chiudi il dialogo
    dialog.accept()

def load_schedule(app):
    """Carica le assegnazioni salvate (ad esempio da un file o backend) e visualizzale nella lista."""
    app.programmazione_list.clear()
    for date, details in app.schedule.items():
        entry_text = f"{date} - Tipologia: {details['tipologia']}, Fascia: {details['fascia']}, Proclamatori: {', '.join(details['proclamatori'])}"
        app.programmazione_list.addItem(entry_text)

def modify_programmazione(app, item):
    """Modifica una programmazione esistente."""
    # Estrarre i dati della programmazione selezionata dalla lista
    entry_text = item.text()
    date_str, details = entry_text.split(" - Tipologia: ")
    date_str = date_str.strip()
    
    # Chiedi all'utente di selezionare una nuova tipologia
    new_tipologia, ok = QInputDialog.getItem(None, "Modifica Tipologia", "Seleziona una nuova tipologia:", list(app.tipologie.keys()), 0, False)
    if ok:
        # Aggiorna i dati della programmazione
        app.schedule[date_str]['tipologia'] = new_tipologia
        load_schedule(app)  # Ricarica la lista della programmazione

def remove_programmazione(app, item):
    """Rimuovi una programmazione esistente."""
    reply = QMessageBox.question(None, "Conferma Cancellazione", "Vuoi cancellare questa programmazione?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    if reply == QMessageBox.Yes:
        # Rimuove l'assegnazione dal dizionario e dalla lista
        date_str = item.text().split(" - ")[0].strip()
        del app.schedule[date_str]
        load_schedule(app)  # Ricarica la lista della programmazione

def setup_programmazione_tab(app):
    """Imposta il tab della programmazione."""
    app.programmazione_list.itemDoubleClicked.connect(lambda item: modify_programmazione(app, item))
    app.programmazione_list.setContextMenuPolicy(Qt.CustomContextMenu)
    app.programmazione_list.customContextMenuRequested.connect(lambda pos: show_context_menu(app, pos))

def show_context_menu(app, pos):
    """Mostra un menu contestuale per modificare o rimuovere una programmazione."""
    item = app.programmazione_list.itemAt(pos)
    if item:
        menu = QMenu()
        modify_action = menu.addAction("Modifica")
        remove_action = menu.addAction("Elimina")
        
        action = menu.exec_(app.programmazione_list.viewport().mapToGlobal(pos))
        
