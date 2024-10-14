from PyQt5.QtWidgets import (QVBoxLayout, QMenu, QLabel, QListWidget, QPushButton, 
                             QDialog, QComboBox, QMessageBox, QSizePolicy)
from PyQt5.QtCore import QDate, Qt

def show_programmazione_dialog(app, date):
    dialog = QDialog()
    dialog.setWindowTitle(f"Programmazione del {date.toString('dd MMM yyyy')}")

    layout = QVBoxLayout(dialog)
    
    # Controlla se ci sono appuntamenti esistenti per quel giorno
    existing_appointments = app.person_schedule.get(date, [])
    
    # Seleziona l'appuntamento esistente (se disponibile)
    appointments_combo = QComboBox()
    if existing_appointments:
        layout.addWidget(QLabel("Seleziona un appuntamento esistente o aggiungine uno nuovo:"))
        appointments_combo.addItem("Aggiungi nuovo appuntamento")  # Opzione per aggiungere nuovo

        for idx, appointment in enumerate(existing_appointments):
            tipologia = appointment.get('tipologia', '')
            fascia = appointment.get('fascia', '')
            proclamatori = ', '.join(appointment.get('proclamatori', []))
            appointments_combo.addItem(f"{tipologia} - {fascia} - {proclamatori}", idx)

        layout.addWidget(appointments_combo)
    else:
        layout.addWidget(QLabel("Aggiungi un nuovo appuntamento:"))

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
        proclamatori_list.clear()  # Pulisci la lista esistente

        if selected_tipo and selected_fascia:
            date_key = date.toString('yyyy-MM-dd')
            day_of_week = str(date.dayOfWeek())

            for proclamatore_id, proclamatore_nome in app.people.items():
                availability = app.person_schedule.get(proclamatore_id, {}).get('availability', {})
                
                if selected_tipo in availability:
                    if day_of_week in availability[selected_tipo]:
                        available_times = availability[selected_tipo][day_of_week]
                        if selected_fascia in available_times:
                            proclamatori_list.addItem(proclamatore_nome)
                    elif date_key in availability[selected_tipo]:
                        available_times = availability[selected_tipo][date_key]
                        if selected_fascia in available_times:
                            proclamatori_list.addItem(proclamatore_nome)

    # Connessione al cambiamento della fascia
    fascia_combo.currentIndexChanged.connect(lambda: update_proclamatori(tipologia_combo.currentData(), fascia_combo.currentText()))

    # Se esiste un appuntamento, selezionare e popolare i campi
    if existing_appointments and appointments_combo:
        def load_existing_appointment(index):
            if index > 0:
                selected_appointment = existing_appointments[appointments_combo.currentData()]
                tipologia_combo.setCurrentText(selected_appointment['tipologia'])
                fascia_combo.setCurrentText(selected_appointment['fascia'])
                proclamatori_list.clearSelection()
                for i in range(proclamatori_list.count()):
                    item = proclamatori_list.item(i)
                    if item.text() in selected_appointment['proclamatori']:
                        item.setSelected(True)

        appointments_combo.currentIndexChanged.connect(lambda: load_existing_appointment(appointments_combo.currentIndex()))

    # Pulsante Conferma
    confirm_button = QPushButton("Conferma")
    layout.addWidget(confirm_button)

    def confirm_selection():
        selected_tipologia = tipologia_combo.currentText()
        selected_fascia = fascia_combo.currentText()
        selected_proclamatori = [item.text() for item in proclamatori_list.selectedItems()]

        if not selected_tipologia or not selected_fascia or not selected_proclamatori:
            QMessageBox.warning(dialog, "Errore", "Tutti i campi devono essere compilati.")
            return

        # Collect the genders of the selected proclaimers
        proclamatore_gender = []
        for proclamatore in selected_proclamatori:
            for proclamatore_id, proclamatore_nome in app.people.items():
                if proclamatore_nome == proclamatore:  # Match by name
                    gender = app.person_schedule.get(proclamatore_id, {}).get('genere_status', {}).get('genere', 'Non specificato')
                    proclamatore_gender.append(gender)
                    break

        # Avoiding duplicate entries
        existing_appointments = app.person_schedule.get(date, [])
        if existing_appointments and appointments_combo.currentIndex() > 0:
            appointment_index = appointments_combo.currentData()
            app.person_schedule[date][appointment_index] = {
                'tipologia': selected_tipologia,
                'fascia': selected_fascia,
                'proclamatori': selected_proclamatori,
                'genere': proclamatore_gender  # List of genders for each selected proclaimer
            }
        else:
            if date not in app.person_schedule:
                app.person_schedule[date] = []
            app.person_schedule[date].append({
                'tipologia': selected_tipologia,
                'fascia': selected_fascia,
                'proclamatori': selected_proclamatori,
                'genere': proclamatore_gender  # Handle appropriately
            })

        update_day_button(app, date)
        QMessageBox.information(dialog, "Successo", "Appuntamento confermato con successo!")
        dialog.accept()

    confirm_button.clicked.connect(confirm_selection)
    dialog.exec_()

def update_day_button(app, date):
    if date in app.day_buttons:
        button = app.day_buttons[date]
        appointments = app.person_schedule.get(date, [])

        # Crea un testo compatto da visualizzare per ogni appuntamento
        info_text = "\n".join(
            f"{appt['tipologia']} - {appt['fascia']} - {', '.join(appt['proclamatori'])}" 
            for appt in appointments
        )

        # Crea un QLabel per visualizzare gli appuntamenti
        appointments_label = QLabel(info_text if appointments else "")
        appointments_label.setAlignment(Qt.AlignCenter)
        appointments_label.setWordWrap(True)

        # Controlla se il layout è già stato impostato
        if button.layout() is not None:
            for i in reversed(range(button.layout().count())):
                widget = button.layout().itemAt(i).widget()
                if widget is not None:  # Controllo se il widget non è None
                    widget.deleteLater()
        else:
            button = QPushButton()
            button.setLayout(QVBoxLayout())  # Imposta un layout se non è già impostato

        # Aggiungi il numero del giorno e il QLabel degli appuntamenti
        day_label = QLabel(str(date.day()))
        day_label.setStyleSheet("background-color: white; border: 1px solid black;")
        day_label.setAlignment(Qt.AlignCenter)

        button.layout().addWidget(day_label)
        button.layout().addWidget(appointments_label)

        button.setMaximumWidth(100)  # Imposta una larghezza massima per il pulsante
        button.setStyleSheet("background-color: lightgray; border: 1px solid black; padding: 5px;")

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
    app.current_month_label.setText(app.current_date.toString("MMMM yyyy").upper())

    # Aggiungi intestazione dei giorni della settimana
    day_names = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]  # Nomi dei giorni della settimana
    for i, day_name in enumerate(day_names):
        day_header_label = QLabel(day_name)
        day_header_label.setAlignment(Qt.AlignCenter)
        day_header_label.setStyleSheet("background-color: lightgray; border: 1px solid black; padding: 5px;")
        app.custom_calendar_layout.addWidget(day_header_label, 0, i)  # Aggiungi intestazione in prima riga

    # Riempie i giorni del mese nella griglia
    for day in range(1, days_in_month + 1):
        day_date = QDate(app.current_date.year(), app.current_date.month(), day)
        grid_row = (start_day_of_week + day - 2) // 7 + 1  # Aggiungi 1 per considerare l'intestazione
        grid_column = (start_day_of_week + day - 2) % 7
        
        # Crea un pulsante per il giorno
        button = QPushButton()
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Permette al pulsante di espandersi
        button.setStyleSheet("background-color: lightgray; border: 1px solid black;")

        # Imposta dimensioni minime e massime
        button.setMinimumHeight(50)  # Imposta l'altezza minima
        button.setMaximumWidth(100)  # Imposta la larghezza massima

        # Crea un layout verticale per il pulsante
        button_layout = QVBoxLayout(button)

        # Crea un rettangolo bianco per il numero del giorno
        day_label = QLabel(str(day))
        day_label.setStyleSheet("background-color: white; border: 1px solid black;")
        day_label.setAlignment(Qt.AlignCenter)

        # Aggiungi il label del giorno al layout del pulsante
        button_layout.addWidget(day_label, alignment=Qt.AlignTop)  # Allinea in alto

        # Aggiungi uno spazio elastico per spingere gli elementi in basso
        button_layout.addStretch()

        # Collega l'evento di clic al dialogo di programmazione
        button.clicked.connect(lambda _, d=day_date: show_programmazione_dialog(app, d))

        # Aggiungi il pulsante al layout del calendario
        app.custom_calendar_layout.addWidget(button, grid_row, grid_column)
        app.day_buttons[day_date] = button


def load_schedule(app):
    app.programmazione_list.clear()
    for date, details in app.schedule.items():
        entry_text = f"{date} - Tipologia: {details['tipologia']}, Fascia: {details['fascia']}, Proclamatori: {', '.join(details['proclamatori'])}"
        app.programmazione_list.addItem(entry_text)

def modify_programmazione(app, item):
    """Modifica una programmazione esistente."""
    entry_text = item.text()
    date_str, details = entry_text.split(" - Tipologia: ")
    date = QDate.fromString(date_str, "dd MMM yyyy")

    # Mostra la finestra di dialogo per la programmazione
    show_programmazione_dialog(app, date)

def remove_programmazione(app, item):
    entry_text = item.text()
    date_str = entry_text.split(" - Tipologia: ")[0]
    date = QDate.fromString(date_str, "dd MMM yyyy")

    app.schedule.pop(date, None)
    load_schedule(app)

def context_menu_event(app, event):
    menu = QMenu(app)
    selected_item = app.programmazione_list.currentItem()

    if selected_item:
        menu.addAction("Modifica", lambda: modify_programmazione(app, selected_item))
        menu.addAction("Rimuovi", lambda: remove_programmazione(app, selected_item))

    menu.exec_(event.globalPos())
