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

def handle_autoabbinamento(app):
    selected_month = app.current_date.month()  # Current month
    selected_year = app.current_date.year()    # Current year

    # Define the types of location (tipologia) to use
    selected_tipologie = [item.data(Qt.UserRole) for item in app.multi_tipologie.selectedItems()]

    # Determine if same-gender pairing is required
    same_gender_required = app.autoabbinamento_gender_sino.get('same_gender', False)

    # Generate a list of all days in the selected month
    days_in_month = app.current_date.daysInMonth()

    # Create a schedule for the month
    monthly_schedule = {}
    
    for day in range(1, days_in_month + 1):
        current_date = QDate(selected_year, selected_month, day)
        day_of_week = current_date.dayOfWeek()  # Get the day of the week (1=Mon, 7=Sun)
        
        # Iterate through each selected tipologia (type)
        for selected_tipologia_id in selected_tipologie:
            if selected_tipologia_id in app.tipo_luogo_schedule:
                tipo_luogo_info = app.tipo_luogo_schedule[selected_tipologia_id]
                selected_tipologia_name = tipo_luogo_info['nome']  # Get the name of the type (tipologia)
                fasce = tipo_luogo_info['fasce'].get(str(day_of_week), [])
                
                for selected_fascia in fasce:
                    # Find available people for this type and time slot
                    available_people = []
                    
                    for proclamatore_id, proclamatore_info in app.people.items():
                        availability = proclamatore_info.get('availability', {})
                        if selected_tipologia_id in availability and str(day_of_week) in availability[selected_tipologia_id]:
                            available_times = availability[selected_tipologia_id][str(day_of_week)]
                            if selected_fascia in available_times:
                                available_people.append(proclamatore_info)

                    if not available_people:
                        continue  # No available people for this slot, move on

                    # Separate individuals by gender if same-gender pairing is required
                    selected_proclamatori = []
                    proclamatore_gender = []

                    if same_gender_required:
                        grouped_people = {}
                        for person in available_people:
                            gender = person.get('genere_status', {}).get('genere', 'Non specificato')
                            if gender not in grouped_people:
                                grouped_people[gender] = []
                            grouped_people[gender].append(person)

                        # Create one pair per gender group
                        for gender, people in grouped_people.items():
                            if len(people) >= 2:
                                selected_proclamatori, proclamatore_gender = create_single_pair_with_gender(people)
                                break  # Stop after one pair
                    else:
                        # Create a pair from all available people
                        selected_proclamatori, proclamatore_gender = create_single_pair_with_gender(available_people)

                    if selected_proclamatori:
                        date_key = current_date.toString('yyyy-MM-dd')
                        if date_key not in monthly_schedule:
                            monthly_schedule[date_key] = []
                        
                        # Append the appointment with the required attributes, including tipologia and tipologia_id
                        monthly_schedule[date_key].append({
                            'tipologia': selected_tipologia_name,       # Name of the tipo_luogo
                            'tipologia_id': selected_tipologia_id,     # ID of the tipo_luogo
                            'fascia': selected_fascia,                 # Time slot
                            'proclamatori': selected_proclamatori,     # Names of the selected people
                            'genere': proclamatore_gender              # Genders of the selected people
                        })
                        break  # Ensure only one pairing per time slot

    # Process the generated monthly schedule as needed (e.g., save it, display it, etc.)
    # Populate the calendar with the appointments
    for date_key, appointments in monthly_schedule.items():
        # Convert date_key back to QDate
        date = QDate.fromString(date_key, 'yyyy-MM-dd')

        # Add the appointments to the app's schedule
        app.schedule[date_key] = appointments

        # Update the button on the calendar to reflect the new appointments
        update_day_button(app, date)
        print(monthly_schedule)

    


def create_single_pair_with_gender(people_list):
    """Create a single pair and collect their gender information."""
    if len(people_list) < 2:
        return None, None  # Not enough people to create a pair
    random.shuffle(people_list)  # Shuffle the list to randomize the pair

    selected_pair = (people_list[0]['name'], people_list[1]['name'])
    genders = [people_list[0].get('genere_status', {}).get('genere', 'Non specificato'),
               people_list[1].get('genere_status', {}).get('genere', 'Non specificato')]

    return selected_pair, genders

def update_day_button(app, date):
    date_key = date.toString('yyyy-MM-dd')
    print(f"Checking appointments for date: {date_key}")

    if date_key in app.day_buttons:
        button = app.day_buttons[date_key]
        appointments = app.schedule.get(date_key, [])

        layout = button.layout()

        # Pulisci il layout senza rimuovere l'etichetta del giorno
        clear_layout(layout)

        # Etichetta con il numero del giorno (se esistente, non rimuoverla)
        # day_label = QLabel(str(date.day()))
        # day_label.setStyleSheet("background-color: white; border: 1px solid black;")
        # day_label.setAlignment(Qt.AlignCenter)
        # layout.addWidget(day_label, alignment=Qt.AlignTop)  # Allinea in alto

        # Se ci sono appuntamenti, aggiungili al layout
        if appointments:
            info_text = "\n".join(
                f"{appt['tipologia']} - {appt['fascia']} - {', '.join(appt['proclamatori'])}"
                for appt in appointments
            )
            appointments_label = QLabel(info_text)
            appointments_label.setAlignment(Qt.AlignCenter)
            appointments_label.setWordWrap(True)
            appointments_label.setStyleSheet("background-color: lightgray; border: 1px solid black; padding: 5px;")
            layout.addWidget(appointments_label, alignment=Qt.AlignTop)

        # Riduci spaziatura e margini in eccesso
        layout.setSpacing(0)  # Rimuove spaziatura tra i widget
        layout.setContentsMargins(0, 0, 0, 0)  # Elimina margini interni nel layout

        button.setMinimumWidth(100)
        
    else:
        print(f"No button found for date: {date_key}")


def clear_layout(layout):
    if layout:
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            widget = item.widget()
            if widget and not isinstance(widget, QLabel):  # Non rimuovere l'etichetta del giorno
                widget.deleteLater()


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
        button.setMinimumWidth(100)

        button_layout = QVBoxLayout(button)

        day_label = QLabel(str(day))
        day_label.setStyleSheet("background-color: white; border: 1px solid black;")
        day_label.setAlignment(Qt.AlignCenter)

        button_layout.addWidget(day_label, alignment=Qt.AlignTop)
        button_layout.addStretch()
        button_layout.setSpacing(0)  # Rimuove spaziatura tra i widget
        button_layout.setContentsMargins(0, 0, 0, 0)  # Elimina margini interni nel layout

        button.clicked.connect(lambda _, d=day_date: show_programmazione_dialog(app, d))

        app.custom_calendar_layout.addWidget(button, grid_row, grid_column)

        # Riduci spaziatura e margini in eccesso
        app.custom_calendar_layout.setSpacing(0)  # Rimuove spaziatura tra i widget
        app.custom_calendar_layout.setContentsMargins(0, 0, 0, 0)  # Elimina margini interni nel layout

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
