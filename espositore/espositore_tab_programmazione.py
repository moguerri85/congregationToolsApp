from PyQt5.QtWidgets import (QVBoxLayout, QMenu, QLabel, QListWidget, QPushButton, 
                             QDialog, QComboBox, QMessageBox, QSizePolicy)
from PyQt5.QtCore import QDate, Qt
from datetime import datetime
import calendar

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

def handle_autoabbinamento(app):
    selected_month = app.current_date.month()
    selected_year = app.current_date.year()

    # Limits for pioneers and proclaimers
    max_utilizzi_mensile_pionieri = app.numero_utilizzi['numero_utilizzi_mensile_pionieri']
    max_utilizzi_mensile_proclamatori = app.numero_utilizzi['numero_utilizzi_mensile_proclamatori']
    
    selected_tipologie = [item.data(Qt.UserRole) for item in app.multi_tipologie.selectedItems()]
    print(f"Tipologie selezionate (ID): {selected_tipologie}")

    filtered_availability = {}

    # Filter availability
    for person_id, schedule in app.person_schedule.items():
        for tipo_luogo, disponibilita in schedule['availability'].items():
            for day, time_slots in disponibilita.items():
                process_day_availability(day, time_slots, selected_month, selected_year, person_id, tipo_luogo, filtered_availability)

    print(f"Disponibilità filtrate: {filtered_availability}")

    matched_pairs = []
    same_gender_required = app.autoabbinamento_gender_sino.get('same_gender', False)

    utilizzi = {'pionieri': {}, 'proclamatori': {}}

    # Initialize utilizzi
    for person_id in app.person_schedule:
        genere = app.person_schedule[person_id].get('genere_status', {}).get('genere', "0")
        utilizzi['pionieri' if genere == "0" else 'proclamatori'][person_id] = 0

    # Track used time slots to avoid overlaps
    used_time_slots = {}

    # Match availability
    for person_id1, availability1 in filtered_availability.items():
        for person_id2, availability2 in filtered_availability.items():
            if person_id1 != person_id2 and can_match(same_gender_required, person_id1, person_id2, app):
                match_availability(app, person_id1, availability1, person_id2, availability2, selected_tipologie, 
                                   utilizzi, matched_pairs, max_utilizzi_mensile_pionieri, max_utilizzi_mensile_proclamatori, 
                                   used_time_slots)

    print(f"Abbinamenti trovati: {matched_pairs}")

    # Filtra gli abbinamenti per rimuovere sovrapposizioni
    abbinamenti_filtrati = filtra_abbinamenti(matched_pairs)

    # Aggiorna il calendario con gli abbinamenti filtrati
    update_calendar_abbinamenti_day_button(app, abbinamenti_filtrati)
    
    return matched_pairs

def filtra_abbinamenti(abbinamenti):
    abbinamenti_filtrati = []
    abbinamenti_per_data = {}

    for abbinamento in abbinamenti:
        data = abbinamento[3]
        ora_inizio = abbinamento[4]
        ora_fine = abbinamento[5]

        # Crea un identificatore per l'abbinamento (data + orario)
        chiave = (data, ora_inizio, ora_fine)

        # Controlla se ci sono già abbinamenti per quella data e orario
        if chiave not in abbinamenti_per_data:
            abbinamenti_per_data[chiave] = abbinamento
        else:
            # Controlla se ci sono sovrapposizioni e conserva solo un abbinamento
            esistente = abbinamenti_per_data[chiave]
            # Verifica se i due abbinamenti si sovrappongono
            # Converti ora_inizio e ora_fine in stringa per il controllo delle sovrapposizioni
            if are_slots_overlapping(f"{ora_inizio}-{ora_fine}", f"{esistente[4]}-{esistente[5]}"):
                # Puoi implementare qui la logica per decidere quale abbinamento mantenere
                # Per esempio, mantieni solo il primo trovato
                continue
            else:
                # Se non si sovrappongono, puoi decidere di aggiungere il nuovo abbinamento
                abbinamenti_per_data[chiave] = abbinamento

    # Raccogli gli abbinamenti filtrati
    abbinamenti_filtrati = list(abbinamenti_per_data.values())
    return abbinamenti_filtrati

def do_time_slots_overlap(slot1: str, slot2: str) -> bool:
    start1, end1 = slot1.split('-')
    start2, end2 = slot2.split('-')

    start1 = datetime.strptime(start1, "%H:%M").time()
    end1 = datetime.strptime(end1, "%H:%M").time()
    start2 = datetime.strptime(start2, "%H:%M").time()
    end2 = datetime.strptime(end2, "%H:%M").time()

    return (start1 < end2 and start2 < end1)

def are_slots_overlapping(slot1, slot2):
    try:
        start1, end1 = map(lambda x: datetime.strptime(x, '%H:%M'), slot1.split('-'))
        start2, end2 = map(lambda x: datetime.strptime(x, '%H:%M'), slot2.split('-'))
    except ValueError as e:
        print(f"Error parsing slots: {slot1} or {slot2} - {e}")
        return False  # or raise an exception if you want to handle it differently

    return (start1 < end2) and (end1 > start2)

def process_day_availability(day, time_slots, selected_month, selected_year, person_id, tipo_luogo, filtered_availability):
    if day.isdigit():
        day_number = int(day)
        num_days_in_month = calendar.monthrange(selected_year, selected_month)[1]
        for day_of_month in range(1, num_days_in_month + 1):
            if datetime(selected_year, selected_month, day_of_month).weekday() == (day_number - 1):
                full_date = f"{selected_year}-{selected_month:02d}-{day_of_month:02d}"
                filtered_availability.setdefault(person_id, {}).setdefault(tipo_luogo, {})[full_date] = time_slots
    else:
        date_obj = datetime.strptime(day, "%Y-%m-%d").date()
        if date_obj.month == selected_month and date_obj.year == selected_year:
            filtered_availability.setdefault(person_id, {}).setdefault(tipo_luogo, {})[day] = time_slots

def can_match(same_gender_required: bool, person_id1: str, person_id2: str, app) -> bool:
    genere1 = app.person_schedule[person_id1].get('genere_status', {}).get('genere', "0")
    genere2 = app.person_schedule[person_id2].get('genere_status', {}).get('genere', "0")
    return genere1 == genere2 if same_gender_required else True

def match_availability(app, person_id1, availability1, person_id2, availability2, selected_tipologie, 
                       utilizzi, matched_pairs, max_utilizzi_mensile_pionieri, max_utilizzi_mensile_proclamatori, 
                       used_time_slots):
    for tipo_luogo_id in selected_tipologie:
        if tipo_luogo_id in availability1 and tipo_luogo_id in availability2:
            for day1, slots1 in availability1[tipo_luogo_id].items():
                if day1 in availability2[tipo_luogo_id]:
                    slots2 = availability2[tipo_luogo_id][day1]

                    for slot1 in slots1:
                        for slot2 in slots2:
                            if not do_time_slots_overlap(slot1, slot2):
                                # Se non ci sono sovrapposizioni, procedi con l'abbinamento
                                add_pairing_if_within_limits(app, person_id1, person_id2, tipo_luogo_id, day1, slot1, slot2, 
                                                              utilizzi, matched_pairs, 
                                                              max_utilizzi_mensile_pionieri, max_utilizzi_mensile_proclamatori)

def add_pairing_if_within_limits(app, person_id1, person_id2, tipo_luogo_id, day1, slot1, slot2, utilizzi, matched_pairs, 
                                   max_utilizzi_mensile_pionieri, max_utilizzi_mensile_proclamatori):
    genere1 = app.person_schedule[person_id1].get('genere_status', {}).get('genere', "0")
    genere2 = app.person_schedule[person_id2].get('genere_status', {}).get('genere', "0")

    if (genere1 == "0" and utilizzi['pionieri'][person_id1] < max_utilizzi_mensile_pionieri and
        (genere2 == "0" and utilizzi['pionieri'][person_id2] < max_utilizzi_mensile_pionieri or
         genere2 == "1" and utilizzi['proclamatori'][person_id2] < max_utilizzi_mensile_proclamatori)):
        matched_pairs.append((person_id1, person_id2, tipo_luogo_id, day1, slot1, slot2))
        utilizzi['pionieri'][person_id1] += 1
        if genere2 == "0":
            utilizzi['pionieri'][person_id2] += 1
        else:
            utilizzi['proclamatori'][person_id2] += 1

    elif (genere1 == "1" and utilizzi['proclamatori'][person_id1] < max_utilizzi_mensile_proclamatori and
          (genere2 == "0" and utilizzi['pionieri'][person_id2] < max_utilizzi_mensile_pionieri or
           genere2 == "1" and utilizzi['proclamatori'][person_id2] < max_utilizzi_mensile_proclamatori)):
        matched_pairs.append((person_id1, person_id2, tipo_luogo_id, day1, slot1, slot2))
        utilizzi['proclamatori'][person_id1] += 1
        if genere2 == "0":
            utilizzi['pionieri'][person_id2] += 1
        else:
            utilizzi['proclamatori'][person_id2] += 1

def get_appointments(abbinamento):
    if len(abbinamento) == 6:
        return []
    return abbinamento[6] if len(abbinamento) > 6 and isinstance(abbinamento[6], list) else []

def update_calendar_abbinamenti_day_button(app, abbinamenti):
    
    for abbinamento in abbinamenti:
        if len(abbinamento) != 6:
            print(f"Abbinamento incompleto o non valido: {abbinamento}")
            continue  # Skip incomplete matches

        person1_name = app.people.get(abbinamento[0], "Sconosciuto")
        person2_name = app.people.get(abbinamento[1], "Sconosciuto")
        tipo_luogo_id, day_str, orario, orario2 = abbinamento[2:6]

        print(f"Abbinamento: {person1_name} - {person2_name} | Luogo ID: {tipo_luogo_id} | Data: {day_str} | Orari: {orario}, {orario2}")

        # Parse and validate the date
        day = QDate.fromString(day_str, "yyyy-MM-dd")
        if not day.isValid():            
            continue  # Skip invalid dates

        # Retrieve the button for the specific day
        button = app.day_buttons.get(day)
        if not button:
            continue

        # Use the helper function to get appointments
        appointments = get_appointments(abbinamento)        

        # Check if appointments are empty and use abbinamento data directly
        if not appointments:
            info_text = f"{tipo_luogo_id} \n {person1_name}-{person2_name} \n Orario: {orario}"
        else:
            # Prepare info text for non-empty appointments
            info_text = "\n".join(
                f"{appt.get('tipologia', 'Nessuna tipologia')} - {appt.get('fascia', '')} - {', '.join(appt.get('proclamatori', []) or [''])}"
                for appt in appointments if isinstance(appt, dict)
            )        

        # Create a QLabel for appointments
        appointments_label = QLabel(info_text)
        appointments_label.setAlignment(Qt.AlignCenter)
        appointments_label.setWordWrap(True)

        # Clear existing layout items
        layout = button.layout()
        if layout:
            while layout.count() > 0:
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        # Create and configure the day label
        day_label = QLabel(str(day.day()))
        day_label.setStyleSheet("background-color: white; border: 1px solid black;")
        day_label.setAlignment(Qt.AlignCenter)

        # Ensure layout is initialized
        if layout is None:
            layout = QVBoxLayout(button)
            button.setLayout(layout)

        # Add day and appointment labels to the layout
        layout.addWidget(day_label)
        layout.addWidget(appointments_label)

        # Set button styles
        button.setMaximumWidth(100)
        button.setStyleSheet("background-color: lightgray; border: 1px solid black; padding: 5px;")

def update_day_button(app, date):
    if date in app.day_buttons:
        button = app.day_buttons[date]
        appointments = app.person_schedule.get(date, [])

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

        button.layout().addWidget(day_label)
        button.layout().addWidget(appointments_label)

        button.setMaximumWidth(100)
        button.setStyleSheet("background-color: lightgray; border: 1px solid black; padding: 5px;")

def clear_layout(layout):
    if layout:
        while layout.count() > 0:
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

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
