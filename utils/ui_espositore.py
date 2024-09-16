from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton, QTabWidget,
                             QWidget, QComboBox, QCalendarWidget, QTextEdit, QInputDialog, QMessageBox, QGridLayout)
from PyQt5.QtCore import Qt

def setup_espositore_tab(app):
    # Ensure app.tabs is a QTabWidget
    if not hasattr(app, 'tabs') or not isinstance(app.tabs, QTabWidget):
        raise RuntimeError("app.tabs must be a QTabWidget instance")

    # --- Espositore Tab ---
    espositore_tab = QWidget()
    main_layout = QHBoxLayout(espositore_tab)
    espositore_tab.setLayout(main_layout)
    
    tab_widget = QTabWidget()
    main_layout.addWidget(tab_widget)

    # --- Tab Proclamatore ---
    proclamatore_tab = QWidget()
    proclamatore_layout = QHBoxLayout(proclamatore_tab)

    left_layout = QVBoxLayout()
    app.person_list = QListWidget()
    app.person_list.itemClicked.connect(lambda item: display_person_details(app, item))
    left_layout.addWidget(app.person_list)

    app.add_button = QPushButton("Aggiungi Proclamatore")
    app.add_button.clicked.connect(lambda: add_person(app))
    left_layout.addWidget(app.add_button)

    app.remove_button = QPushButton("Elimina Proclamatore")
    app.remove_button.clicked.connect(lambda: remove_person(app))
    left_layout.addWidget(app.remove_button)

    right_layout = QVBoxLayout()
    app.detail_label = QLabel("Dettagli del Proclamatore")
    app.detail_label.setAlignment(Qt.AlignCenter)
    right_layout.addWidget(app.detail_label)

    app.detail_text = QTextEdit()
    app.detail_text.setReadOnly(True)
    right_layout.addWidget(app.detail_text)

    app.calendar = QCalendarWidget()
    app.calendar.clicked.connect(lambda date: show_availability_dialog(app, date))
    right_layout.addWidget(app.calendar)

    proclamatore_layout.addLayout(left_layout)
    proclamatore_layout.addLayout(right_layout)
    proclamatore_tab.setLayout(proclamatore_layout)

    tab_widget.addTab(proclamatore_tab, "Proclamatore")

    # --- Tab Turni ---
    turni_tab = QWidget()
    turni_layout = QVBoxLayout(turni_tab)

    app.tipologie_list = QListWidget()
    app.tipologie_list.setSelectionMode(QListWidget.SingleSelection)
    app.tipologie_list.itemClicked.connect(lambda item: update_week_display(app, item.text()))  # Connessione evento
    turni_layout.addWidget(app.tipologie_list)

    app.add_tipologia_button = QPushButton("Aggiungi Tipologia")
    app.add_tipologia_button.clicked.connect(lambda: add_tipologia(app))
    turni_layout.addWidget(app.add_tipologia_button)

    app.remove_tipologia_button = QPushButton("Rimuovi Tipologia")
    app.remove_tipologia_button.clicked.connect(lambda: remove_tipologia(app))
    turni_layout.addWidget(app.remove_tipologia_button)

    app.turni_table = QWidget()
    app.turni_table.setLayout(QVBoxLayout())
    turni_layout.addWidget(app.turni_table)

    # Initialize week_display
    app.week_display = QWidget()
    app.week_display.setLayout(QVBoxLayout())
    turni_layout.addWidget(app.week_display)

    tab_widget.addTab(turni_tab, "Turni")

    app.tabs.addTab(espositore_tab, "Espositore")

    app.tipologia_schedule = {}
    app.person_schedule = {}

def show_availability_dialog(app, date):
    try:
        # Crea una finestra di dialogo per selezionare la tipologia e le fasce orarie
        dialog = QWidget()
        dialog.setWindowTitle("Aggiungi Disponibilità")
        layout = QVBoxLayout(dialog)

        # Seleziona la tipologia
        tipologia_label = QLabel("Seleziona la tipologia:")
        layout.addWidget(tipologia_label)
        
        tipologia_combo = QComboBox()
        for item in app.tipologie_list.findItems("*", Qt.MatchWildcard):
            tipologia_combo.addItem(item.text())
        layout.addWidget(tipologia_combo)

        # Seleziona la fascia oraria
        fascia_label = QLabel("Seleziona la fascia oraria:")
        layout.addWidget(fascia_label)
        
        fascia_combo = QComboBox()
        layout.addWidget(fascia_combo)

        # Aggiorna le fasce orarie quando la tipologia cambia
        def update_fasce():
            selected_tipologia = tipologia_combo.currentText()
            if selected_tipologia in app.tipologia_schedule:
                fasce = [fascia for day in app.tipologia_schedule[selected_tipologia].values() for fascia in day]
                fascia_combo.clear()
                fascia_combo.addItems(fasce)

        tipologia_combo.currentIndexChanged.connect(update_fasce)
        update_fasce()  # Aggiorna le fasce orarie iniziali

        # Bottone per confermare
        confirm_button = QPushButton("Conferma")
        confirm_button.clicked.connect(lambda: update_person_availability(app, date, tipologia_combo.currentText(), fascia_combo.currentText(), dialog))
        layout.addWidget(confirm_button)

        dialog.setLayout(layout)
        dialog.show()

    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

def update_person_availability(app, date, tipologia, fascia_oraria, dialog):
    try:
        person_name = app.person_list.currentItem().text()
        if person_name not in app.person_schedule:
            app.person_schedule[person_name] = {}

        if date not in app.person_schedule[person_name]:
            app.person_schedule[person_name][date] = []

        app.person_schedule[person_name][date].append({
            'tipologia': tipologia,
            'fascia_oraria': fascia_oraria
        })
        
        dialog.close()
        display_person_details(app, app.person_list.currentItem())  # Aggiorna i dettagli del proclamatore
        update_turni_table(app)  # Aggiorna la tabella dei turni se necessario

    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

def add_person(app):
    try:
        text, ok = QInputDialog.getText(app, "Aggiungi Proclamatore", "Nome del Proclamatore:")
        if ok and text:
            app.person_list.addItem(text)
            app.person_schedule[text] = {}
            update_turni_table(app)  # Aggiorna la tabella dei turni
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

def remove_person(app):
    try:
        selected_item = app.person_list.currentItem()
        if selected_item:
            person_name = selected_item.text()
            app.person_list.takeItem(app.person_list.row(selected_item))
            if person_name in app.person_schedule:
                del app.person_schedule[person_name]
            update_turni_table(app)  # Aggiorna la tabella dei turni
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

def display_person_details(app, item):
    """Visualizza i dettagli del proclamatore selezionato e prepara l'interfaccia per aggiungere la disponibilità."""
    try:
        person_name = item.text()
        app.current_person = person_name  # Salva la persona selezionata
        
        if person_name in app.person_schedule:
            details = "\n".join([f"Data: {date}, Fasce Orarie: {', '.join([f['fascia_oraria'] for f in fasce])}" 
                                 for date, fasce in app.person_schedule[person_name].items()])
            app.detail_text.setText(details)
        else:
            app.detail_text.setText("Nessun dettaglio disponibile.")
        
        update_turni_table(app)  # Assicurati che il tab "Turni" sia aggiornato
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

def add_tipologia(app):
    new_tipologia, ok = QInputDialog.getText(app, 'Nuova Tipologia', 'Inserisci il nome della tipologia:')
    if ok and new_tipologia:
        app.tipologie_list.addItem(new_tipologia)
        app.tipologia_schedule[new_tipologia] = {}
        update_week_display(app, new_tipologia)  # Mostra la settimana per la nuova tipologia

def remove_tipologia(app):
    try:
        selected_item = app.tipologie_list.currentItem()
        if selected_item:
            tipologia_name = selected_item.text()
            app.tipologie_list.takeItem(app.tipologie_list.row(selected_item))
            if tipologia_name in app.tipologia_schedule:
                del app.tipologia_schedule[tipologia_name]
            update_turni_table(app)  # Aggiorna la tabella dei turni
            clear_week_display(app)  # Pulisci la visualizzazione della settimana
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

def update_turni_table(app):
    try:
        if app.turni_table.layout():
            while app.turni_table.layout().count():
                item = app.turni_table.layout().takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        main_layout = QVBoxLayout()
        for tipologia, settimane in app.tipologia_schedule.items():
            tipologia_layout = QVBoxLayout()

            tipologia_label = QLabel(f"Tipologia: {tipologia}")
            tipologia_label.setAlignment(Qt.AlignCenter)
            tipologia_layout.addWidget(tipologia_label)

            for settimana, giorni in settimane.items():
                settimana_label = QLabel(f"Settimana: {settimana}")
                settimana_label.setAlignment(Qt.AlignCenter)
                tipologia_layout.addWidget(settimana_label)

                settimana_layout = QGridLayout()
                days = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]

                for i, day in enumerate(days):
                    button = QPushButton(day)
                    button.setFixedSize(60, 60)
                    button.setStyleSheet("background-color: lightgrey; border: 1px solid black;")
                    settimana_layout.addWidget(button, i // 7, i % 7)

                    if day in giorni:
                        for fascia_oraria in giorni[day]:
                            button.setText(f"{day}\n{fascia_oraria}")

                settimana_frame = QWidget()
                settimana_frame.setLayout(settimana_layout)
                tipologia_layout.addWidget(settimana_frame)

            tipologia_widget = QWidget()
            tipologia_widget.setLayout(tipologia_layout)
            main_layout.addWidget(tipologia_widget)

        app.turni_table.setLayout(main_layout)
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

def save_fascia_oraria(app, tipologia, day, fascia_oraria):
    if tipologia not in app.tipologia_schedule:
        app.tipologia_schedule[tipologia] = {}
    if day not in app.tipologia_schedule[tipologia]:
        app.tipologia_schedule[tipologia][day] = []
    app.tipologia_schedule[tipologia][day].append(fascia_oraria)
    update_week_display(app, tipologia)  # Rende visibile la fascia oraria appena salvata

def update_week_display(app, tipologia):
    """Visualizza una settimana tipo (da lunedì a domenica) con le fasce orarie della tipologia selezionata."""
    clear_week_display(app)
    
    week_layout = QHBoxLayout()
    days_of_week = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

    day_buttons = {}
    for day in days_of_week:
        day_button = QPushButton(day)
        day_button.setFixedSize(100, 100)
        day_buttons[day] = day_button
        day_button.clicked.connect(lambda _, d=day: add_fascia_to_day(app, tipologia, d))
        week_layout.addWidget(day_button)

    week_display_widget = QWidget()
    week_display_widget.setLayout(week_layout)
    app.week_display.setLayout(QVBoxLayout())
    app.week_display.layout().addWidget(week_display_widget)

    if tipologia in app.tipologia_schedule:
        for day, fasce in app.tipologia_schedule[tipologia].items():
            for button in day_buttons.values():
                if button.text().startswith(day):
                    button.setText(f"{day}\n" + "\n".join(fasce))

def clear_week_display(app):
    """Pulisce la visualizzazione della settimana."""
    if app.week_display.layout() is not None:
        while app.week_display.layout().count():
            item = app.week_display.layout().takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

def add_fascia_to_day(app, tipologia, day):
    """Apre un dialogo per aggiungere una fascia oraria al giorno selezionato."""
    fascia_oraria, ok = QInputDialog.getText(app, f'Aggiungi Fascia Oraria per {day}', 'Inserisci la fascia oraria:')
    if ok and fascia_oraria:
        save_fascia_oraria(app, tipologia, day, fascia_oraria)
        update_week_display(app, tipologia)  # Rende visibile la fascia oraria appena aggiunta

