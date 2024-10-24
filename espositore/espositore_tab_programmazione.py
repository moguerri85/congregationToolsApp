from PyQt5.QtWidgets import (QVBoxLayout, QMenu, QLabel, QListWidget, QPushButton, 
                             QDialog, QComboBox, QMessageBox, QSizePolicy)
from PyQt5.QtCore import QDate, Qt
import random

def show_programmazione_dialog(app, date):
    dialog = QDialog()
    dialog.setWindowTitle(f"Programmazione del {date.toString('dd MMM yyyy')}")

    layout = QVBoxLayout(dialog)

    day_of_week = str(date.dayOfWeek())  # Get day of the week (1=Mon, 7=Sun)
    date_key = date.toString('yyyy-MM-dd')  # Format date for comparisons

    # Check for existing appointments
    existing_appointments = app.schedule.get(date_key, [])

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
            app.schedule[date_key][appointment_index] = {
                'tipologia': selected_tipologia,
                'fascia': selected_fascia,
                'proclamatori': selected_proclamatori,
                'genere': proclamatore_gender
            }
        else:
            if date_key not in app.schedule:
                app.schedule[date_key] = []
            app.schedule[date_key].append({
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

def get_day_from_id(day_id):
    giorno_map = {
        '1': 'Lunedì',
        '2': 'Martedì',
        '3': 'Mercoledì',
        '4': 'Giovedì',
        '5': 'Venerdì',
        '6': 'Sabato',
        '7': 'Domenica',
    }
    """Restituisce il nome del giorno corrispondente all'ID."""
    return giorno_map.get(day_id, "N/A")  # Restituisce "N/A" se l'ID non è valido

def handle_autoabbinamento(app):
    selected_month = app.current_date.month()  # Mese corrente
    selected_year = app.current_date.year()  # Anno corrente

    same_gender_required = app.autoabbinamento_gender_sino.get('same_gender', False)
    selected_tipologie = [item.data(Qt.UserRole) for item in app.multi_tipologie.selectedItems()]

    max_utilizzi_mensile_pionieri = app.numero_utilizzi['numero_utilizzi_mensile_pionieri']
    max_utilizzi_mensile_proclamatori = app.numero_utilizzi['numero_utilizzi_mensile_proclamatori']

    max_utilizzi_settimanale_pionieri = app.numero_utilizzi['numero_utilizzi_settimanale_pionieri']
    max_utilizzi_settimanale_proclamatori = app.numero_utilizzi['numero_utilizzi_settimanale_proclamatori']

    abbinamenti = []
    abbinamenti_giorno_fascia = {}  # Dizionario per tracciare gli abbinamenti già creati per giorno, tipologia e fascia
    
    # Cicla attraverso tutti i giorni del mese selezionato
    days_in_month = QDate(selected_year, selected_month, 1).daysInMonth()

    for day in range(1, days_in_month + 1):
        current_date = QDate(selected_year, selected_month, day)  # Data corrente del ciclo
        giorno_data = current_date.toString('yyyy-MM-dd')  # Giorno specifico come stringa
        day_of_week = str(current_date.dayOfWeek())  # Numero del giorno della settimana (1=Lun, ..., 7=Dom)

        for tipologia in selected_tipologie:
            tipologia_data = app.tipo_luogo_schedule.get(tipologia)
            if not tipologia_data:
                continue

            fasce_orarie = tipologia_data.get('fasce', {}).get(day_of_week, [])
            for fascia_oraria in fasce_orarie:
                # Verifica se esiste già un abbinamento per questo giorno, tipologia e fascia oraria
                if (giorno_data, tipologia, fascia_oraria) in abbinamenti_giorno_fascia:
                    continue  # Salta se c'è già un abbinamento

                proclaimers_available = []

                for proclamatore_id, proclamatore_info in app.people.items():
                    availability = proclamatore_info.get('availability', {})

                    # Verifica la disponibilità per il tipo, giorno e fascia oraria
                    if tipologia in availability and day_of_week in availability[tipologia]:
                        available_times = availability[tipologia][day_of_week]
                        if fascia_oraria in available_times:
                            proclamatore_gender = proclamatore_info.get('genere_status', {}).get('genere', 0)
                            proclaimers_available.append((proclamatore_id, proclamatore_info['name'], proclamatore_gender))

                # Mischia proclamatori per generare abbinamenti casuali
                random.shuffle(proclaimers_available)

                # Crea abbinamenti se ci sono almeno 2 proclamatori disponibili
                if len(proclaimers_available) >= 2:
                    if same_gender_required:
                        male_group = [p for p in proclaimers_available if p[2] == 0]
                        female_group = [p for p in proclaimers_available if p[2] == 1]

                        if len(male_group) >= 2:
                            abbinamenti.append((male_group[0][1], male_group[1][1], tipologia, fascia_oraria, giorno_data))
                            proclaimers_available.remove(male_group[0])
                            proclaimers_available.remove(male_group[1])
                        elif len(female_group) >= 2:
                            abbinamenti.append((female_group[0][1], female_group[1][1], tipologia, fascia_oraria, giorno_data))
                            proclaimers_available.remove(female_group[0])
                            proclaimers_available.remove(female_group[1])
                    else:
                        proclamatore1 = proclaimers_available.pop(0)
                        proclamatore2 = proclaimers_available.pop(0)
                        abbinamenti.append((proclamatore1[1], proclamatore2[1], tipologia, fascia_oraria, giorno_data))

                    # Registra l'abbinamento per questo giorno, tipologia e fascia oraria
                    abbinamenti_giorno_fascia[(giorno_data, tipologia, fascia_oraria)] = True

    # Stampa gli abbinamenti con la data specifica
    for abbinamento in abbinamenti:
        proclamatore1, proclamatore2, tipologia, fascia_oraria, giorno_data = abbinamento
        print(f"Abbinamento: {proclamatore1} e {proclamatore2} per {tipologia} alle {fascia_oraria} il {giorno_data}")

    return abbinamenti


def update_day_button(app, date):
    date_key = date.toString('yyyy-MM-dd')  # Ensure the date key matches the button key format
    print(f"Checking appointments for date: {date_key}")

    if date_key in app.day_buttons:
        button = app.day_buttons[date_key]
        appointments = app.schedule.get(date_key, [])  # Fetch from schedule

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
