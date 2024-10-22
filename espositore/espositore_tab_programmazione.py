from PyQt5.QtWidgets import (QVBoxLayout, QMenu, QLabel, QListWidget, QPushButton, 
                             QDialog, QComboBox, QMessageBox, QSizePolicy)
from PyQt5.QtCore import QDate, Qt

def show_programmazione_dialog(app, date):
    dialog = QDialog()
    dialog.setWindowTitle(f"Programmazione del {date.toString('dd MMM yyyy')}")

    layout = QVBoxLayout(dialog)

    day_of_week = str(date.dayOfWeek())  # Get day of the week (1=Mon, 7=Sun)
    date_key = date.toString('yyyy-MM-dd')  # Format date for comparisons

    # Check for existing appointments
    existing_appointments = app.person_schedule.get(date_key, [])

    # Select existing appointment (if available)
    appointments_combo = QComboBox()
    if existing_appointments:
        layout.addWidget(QLabel("Seleziona un appuntamento esistente o aggiungine uno nuovo:"))
        appointments_combo.addItem("Aggiungi nuovo appuntamento")  # Option to add new

        for idx, appointment in enumerate(existing_appointments):
            tipologia = appointment.get('tipologia', '')
            fascia = appointment.get('fascia', '')
            proclamatori = ', '.join(appointment.get('proclamatori', []))
            appointments_combo.addItem(f"{tipologia} - {fascia} - {proclamatori}", idx)

        layout.addWidget(appointments_combo)
    else:
        layout.addWidget(QLabel("Aggiungi un nuovo appuntamento:"))

    # Select Type
    tipologia_label = QLabel("Seleziona Tipologia:")
    layout.addWidget(tipologia_label)
    tipologia_combo = QComboBox()
    tipologia_combo.addItem("")  # First empty item

    # Populate the active types for the selected day
    if app.tipo_luogo_schedule:
        for tipo, info in app.tipo_luogo_schedule.items():
            if info.get('attivo', False) and day_of_week in info['fasce']:
                tipologia_combo.addItem(info['nome'], tipo)

    if tipologia_combo.count() == 1:
        tipologia_combo.addItem("Nessuna tipologia attiva disponibile per il giorno selezionato")

    layout.addWidget(tipologia_combo)

    # Select Time Slot
    layout.addWidget(QLabel("Seleziona Fascia Oraria"))
    fascia_combo = QComboBox()
    fascia_combo.addItem("")  # First empty item

    def update_fasce():
        """Update time slots based on selected type."""
        fascia_combo.clear()  # Clear previous slots
        selected_tipo = tipologia_combo.currentData()  # Get selected type

        if selected_tipo and selected_tipo in app.tipo_luogo_schedule:
            fasce = app.tipo_luogo_schedule[selected_tipo]['fasce'].get(day_of_week, [])
            for fascia in fasce:
                fascia_combo.addItem(fascia)

            update_proclamatori(selected_tipo, fascia_combo.currentText())

    # Connect to type change
    tipologia_combo.currentIndexChanged.connect(update_fasce)

    layout.addWidget(fascia_combo)

    # Select Available Proclaimers
    layout.addWidget(QLabel("Seleziona Proclamatori Disponibili"))
    proclamatori_list = QListWidget()
    proclamatori_list.setSelectionMode(QListWidget.MultiSelection)
    layout.addWidget(proclamatori_list)

    def update_proclamatori(selected_tipo, selected_fascia):
        proclamatori_list.clear()  # Clear existing list

        if selected_tipo and selected_fascia:
            for proclamatore_id, proclamatore_info in app.people.items():
                availability = proclamatore_info.get('availability', {})

                # Check if the proclaimer is available for the selected type and time slot
                if selected_tipo in availability:
                    if day_of_week in availability[selected_tipo]:
                        available_times = availability[selected_tipo][day_of_week]
                        if selected_fascia in available_times:
                            proclamatori_list.addItem(proclamatore_info['name'])

    # Connect to time slot change
    fascia_combo.currentIndexChanged.connect(lambda: update_proclamatori(tipologia_combo.currentData(), fascia_combo.currentText()))

    # Confirm Button
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
            for proclamatore_id, proclamatore_info in app.people.items():
                if proclamatore_info['name'] == proclamatore:  # Match by name
                    gender = proclamatore_info.get('genere_status', {}).get('genere', 'Non specificato')
                    proclamatore_gender.append(gender)
                    break

        # Check for existing appointments
        if existing_appointments and appointments_combo.currentIndex() > 0:
            appointment_index = appointments_combo.currentData()
            app.person_schedule[date_key][appointment_index] = {
                'tipologia': selected_tipologia,
                'fascia': selected_fascia,
                'proclamatori': selected_proclamatori,
                'genere': proclamatore_gender
            }
        else:
            if date_key not in app.person_schedule:
                app.person_schedule[date_key] = []
            app.person_schedule[date_key].append({
                'tipologia': selected_tipologia,
                'fascia': selected_fascia,
                'proclamatori': selected_proclamatori,
                'genere': proclamatore_gender
            })

        # Update the button on the calendar
        update_day_button(app, date)
        QMessageBox.information(dialog, "Successo", "Appuntamento confermato con successo!")
        dialog.accept()

    confirm_button.clicked.connect(confirm_selection)
    dialog.exec_()

def handle_autoabbinamento(app):
    print("handle_autoabbinamento")

def update_day_button(app, date):
    date_key = date.toString('yyyy-MM-dd')  # Ensure the date key matches the button key format
    print(f"Checking appointments for date: {date_key}")

    if date_key in app.day_buttons:
        button = app.day_buttons[date_key]
        appointments = app.person_schedule.get(date_key, [])  # Fetch from person_schedule

        info_text = "\n".join(
            f"{appt['tipologia']} - {appt['fascia']} - {', '.join(appt['proclamatori'])}" 
            for appt in appointments
        )

        appointments_label = QLabel(info_text if appointments else "")
        appointments_label.setAlignment(Qt.AlignCenter)
        appointments_label.setWordWrap(True)

        layout = button.layout()
        clear_layout(layout)

        day_label = QLabel(str(date.day()))
        day_label.setStyleSheet("background-color: white; border: 1px solid black;")
        day_label.setAlignment(Qt.AlignCenter)

        # Add widgets to button layout
        button.layout().addWidget(day_label)
        button.layout().addWidget(appointments_label)

        button.setMaximumWidth(100)
        button.setStyleSheet("background-color: lightgray; border: 1px solid black; padding: 5px;")
    else:
        print(f"No button found for date: {date_key}")

def clear_layout(layout):
    if layout:
        while layout.count() > 0:
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

def update_calendar(app):
    # Clear the existing calendar layout
    while app.custom_calendar_layout.count():
        item = app.custom_calendar_layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()

    days_in_month = app.current_date.daysInMonth()
    first_day_of_month = app.current_date.addDays(-app.current_date.day() + 1)
    start_day_of_week = first_day_of_month.dayOfWeek()

    app.current_month_label.setText(app.current_date.toString("MMMM yyyy").upper())

    day_names = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]  # Day names
    for i, day_name in enumerate(day_names):
        day_header_label = QLabel(day_name)
        day_header_label.setAlignment(Qt.AlignCenter)
        day_header_label.setStyleSheet("background-color: lightgray; border: 1px solid black; padding: 5px;")
        app.custom_calendar_layout.addWidget(day_header_label, 0, i)

    for day in range(1, days_in_month + 1):
        day_date = QDate(app.current_date.year(), app.current_date.month(), day)
        date_key = day_date.toString('yyyy-MM-dd')  # Store date in yyyy-MM-dd format
        grid_row = (start_day_of_week + day - 2) // 7 + 1
        grid_column = (start_day_of_week + day - 2) % 7
        
        button = QPushButton()
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        button.setStyleSheet("background-color: lightgray; border: 1px solid black;")
        button.setMinimumHeight(50)
        button.setMaximumWidth(100)

        button_layout = QVBoxLayout(button)

        day_label = QLabel(str(day))
        day_label.setStyleSheet("background-color: white; border: 1px solid black;")
        day_label.setAlignment(Qt.AlignCenter)

        button_layout.addWidget(day_label, alignment=Qt.AlignTop)
        button_layout.addStretch()

        button.clicked.connect(lambda _, d=day_date: show_programmazione_dialog(app, d))

        app.custom_calendar_layout.addWidget(button, grid_row, grid_column)
        app.day_buttons[date_key] = button  # Store the button with the date key
        print(f"Button created for date: {date_key}")

def load_schedule(app):
    app.programmazione_list.clear()
    for date, details in app.schedule.items():
        entry_text = f"{date} - Tipologia: {details['tipologia']}, Fascia: {details['fascia']}, Proclamatori: {', '.join(details['proclamatori'])}"
        app.programmazione_list.addItem(entry_text)

def modify_programmazione(app, item):
    """Modify an existing programmazione."""
    entry_text = item.text()
    date_str, details = entry_text.split(" - Tipologia: ")
    date = QDate.fromString(date_str, "dd MMM yyyy")

    # Show the programming dialog
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
