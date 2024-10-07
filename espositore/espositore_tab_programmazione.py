from PyQt5.QtWidgets import (QVBoxLayout, QMenu, QLabel, QListWidget, QPushButton, 
                             QDialog, QComboBox, QMessageBox, QInputDialog)
from PyQt5.QtCore import QDate

def show_programmazione_dialog(app, date):
    # Crea una finestra di dialogo per selezionare tipologia, fascia oraria e proclamatori
    dialog = QDialog()
    dialog.setWindowTitle(f"Programmazione del {date.toString('dd MMM yyyy')}")

    layout = QVBoxLayout(dialog)

    # Seleziona Tipologia
    tipologia_label = QLabel("Seleziona Tipologia:")
    layout.addWidget(tipologia_label)
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
    proclamatori_list = QListWidget()  # Definisco proclamatori_list qui
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

    # Pulsante Conferma
    confirm_button = QPushButton("Conferma")
    layout.addWidget(confirm_button)

    def confirm_selection():
        selected_tipologia = tipologia_combo.currentText()
        selected_fascia = fascia_combo.currentText()
        selected_proclamatori = [item.text() for item in proclamatori_list.selectedItems()]  # proclamatore_list ora è visibile

        # Salva i dati per il giorno selezionato
        app.person_schedule[date] = {
            'tipologia': selected_tipologia,
            'fascia': selected_fascia,
            'proclamatori': selected_proclamatori
        }

        # Aggiorna il quadrato del giorno nel calendario
        update_day_button(app, date)

        dialog.accept()

    confirm_button.clicked.connect(confirm_selection)
    dialog.exec_()

def update_day_button(app, date):
    # Trova il pulsante del giorno corrispondente
    if date in app.day_buttons:
        button = app.day_buttons[date]

        # Recupera le informazioni del giorno
        day_data = app.person_schedule.get(date, {})
        tipologia = day_data.get('tipologia', '')
        fascia = day_data.get('fascia', '')
        proclamatori = ', '.join(day_data.get('proclamatori', []))

        # Se le informazioni sono troppo lunghe, possiamo abbreviare i proclamatori o usare una label per un'icona
        proclamatori_text = ', '.join([p.split()[0] for p in day_data.get('proclamatori', [])]) if len(proclamatori) > 30 else proclamatori

        # Crea un testo compatto da visualizzare
        info_text = f"{tipologia}\n{fascia}\n{proclamatori_text}"

        # Aggiorna il pulsante con le informazioni selezionate
        button.setText(f"{date.day()}\n{info_text}")

def update_calendar(app):
    # Pulisci la griglia dei giorni
    while app.custom_calendar_layout.count():
        item = app.custom_calendar_layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()

    # Ottieni il mese corrente
    days_in_month = app.current_date.daysInMonth()
    first_day_of_month = app.current_date.addDays(-app.current_date.day() + 1)
    start_day_of_week = first_day_of_month.dayOfWeek()

    # Aggiorna l'etichetta del mese corrente
    app.current_month_label.setText(app.current_date.toString("MMMM yyyy"))

    # Riempie i giorni del mese nella griglia
    for day in range(1, days_in_month + 1):
        day_date = QDate(app.current_date.year(), app.current_date.month(), day)
        grid_row = (start_day_of_week + day - 2) // 7
        grid_column = (start_day_of_week + day - 2) % 7
        
        button = QPushButton(str(day))
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        button.setFixedSize(80, 80)
        button.setStyleSheet("background-color: lightgray; border: 1px solid black;")
        
        button.clicked.connect(lambda _, d=day_date: show_programmazione_dialog(app, d))

        app.custom_calendar_layout.addWidget(button, grid_row, grid_column)
        app.day_buttons[day_date] = button

        # Aggiorna il quadrato con eventuali informazioni salvate
        update_day_button(app, day_date)

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
        
