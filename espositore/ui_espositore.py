from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton, QTabWidget, QWidget, QCalendarWidget,
                             QTextEdit, QGridLayout, QRadioButton, QButtonGroup, QSizePolicy, QScrollArea)
from PyQt5.QtCore import Qt, QSize, QDate

from espositore.espositore_tab_gestione import add_tipo_luogo, fix_orari, fix_proclamatori, modify_selected_tipo_luogo, remove_tipo_luogo
from espositore.espositore_tab_proclamatore import add_person, display_person_details, remove_person, show_availability_dialog
from espositore.espositore_tab_programmazione import show_programmazione_dialog
from espositore.espositore_utils import import_disponibilita, update_week_display_and_data
from utils.auth_utility import load_espositore_data_from_dropbox
from utils.logging_custom import logging_custom

def setup_espositore_tab(app):
    if not hasattr(app, 'tabs') or not isinstance(app.tabs, QTabWidget):
        raise RuntimeError("app.tabs must be a QTabWidget instance")

    espositore_tab = QWidget()
    main_layout = QVBoxLayout(espositore_tab)  # Cambiato da QHBoxLayout a QVBoxLayout per aggiungere le righe sopra i tab

    # --- Righe per data e ora ultimo caricamento e ultima modifica ---
    app.last_load_label = QLabel(f"Ultimo import disponibilità: nessuna modifica")
    app.last_modification_label = QLabel("Ultima modifica effettuata: nessuna modifica")

    # Crea il pulsante "Importa"
    import_button = QPushButton("Importa da Hourglass")
    import_button.setFixedSize(QSize(120, 30))  # Opzionale: dimensioni fisse per il pulsante

    # Collega il pulsante a una funzione (da definire) per gestire l'importazione
    import_button.clicked.connect(lambda: import_disponibilita(app))
    main_layout.addWidget(import_button)
    
    main_layout.addWidget(app.last_load_label)
    main_layout.addWidget(app.last_modification_label)

    # --- Tab widget ---
    tab_widget = QTabWidget()
    main_layout.addWidget(tab_widget)

    app.people = {}
    app.tipo_luogo_schedule = {}
    app.tipologie = {}
    app.person_schedule = {}

    # --- Tab Proclamatore ---
    proclamatore_tab = QWidget()
    proclamatore_layout = QHBoxLayout(proclamatore_tab)

    # Layout sinistro
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

    # Creazione della scroll area per il layout destro
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area_content = QWidget()  # Widget contenitore per la scroll area
    scroll_area_layout = QVBoxLayout(scroll_area_content)

    # Layout destro
    app.detail_label = QLabel("Dettagli del Proclamatore")
    app.detail_label.setAlignment(Qt.AlignCenter)
    scroll_area_layout.addWidget(app.detail_label)

    app.detail_text = QTextEdit()
    app.detail_text.setReadOnly(True)
    scroll_area_layout.addWidget(app.detail_text)

    app.radio_uguale_tutte_settimane = QRadioButton("Uguale a tutte le settimane")
    app.radio_specifica_giorni = QRadioButton("Specifica i giorni")

    app.radio_group = QButtonGroup()
    app.radio_group.addButton(app.radio_uguale_tutte_settimane)
    app.radio_group.addButton(app.radio_specifica_giorni)

    app.radio_uguale_tutte_settimane.toggled.connect(lambda: toggle_week_or_calendar(app))
    app.radio_specifica_giorni.toggled.connect(lambda: toggle_week_or_calendar(app))

    scroll_area_layout.addWidget(app.radio_uguale_tutte_settimane)
    scroll_area_layout.addWidget(app.radio_specifica_giorni)

    # Setup del layout dei giorni della settimana
    if not hasattr(app, 'week_widget'):
        app.week_widget = QWidget()
        app.week_layout = QHBoxLayout(app.week_widget)

    days_of_week = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

    for day in days_of_week:
        day_widget = QWidget()
        day_layout = QVBoxLayout(day_widget)

        day_label = QLabel(day)
        day_layout.addWidget(day_label)

        square_button = QPushButton()
        square_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        square_button.setFixedSize(QSize(60, 60))
        square_button.setStyleSheet("background-color: lightgray; border: 1px solid black;")
        day_layout.addWidget(square_button)

        day_widget.setLayout(day_layout)
        app.week_layout.addWidget(day_widget)

    scroll_area_layout.addWidget(app.week_widget)
    setup_week_layout(app)

    # Calendario
    if not hasattr(app, 'calendar'):
        app.calendar = QCalendarWidget()
        app.calendar.clicked.connect(lambda date: show_availability_dialog(app, date))
    scroll_area_layout.addWidget(app.calendar)

    # Imposta la scroll area
    scroll_area.setWidget(scroll_area_content)

    # Aggiungi il layout sinistro e la scroll area al layout principale
    proclamatore_layout.addLayout(left_layout)
    proclamatore_layout.addWidget(scroll_area)  # Aggiungi la scroll area nel layout destro
    proclamatore_tab.setLayout(proclamatore_layout)

    tab_widget.addTab(proclamatore_tab, "Proclamatore")

    # --- Tab Tipologia, Luogo e Fascia ---
    gestione_tab = QWidget()
    gestione_layout = QVBoxLayout(gestione_tab)

    # Creazione della scroll area
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)  # Permette al widget di ridimensionarsi
    scroll_area_content = QWidget()  # Widget contenitore per il layout della scroll area
    scroll_area_layout = QVBoxLayout(scroll_area_content)

    app.tipologie_list = QListWidget()
    app.tipologie_list.setSelectionMode(QListWidget.SingleSelection)
    app.tipologie_list.setMaximumHeight(100)  # Sostituisci 100 con l'altezza desiderata
    app.tipologie_list.itemClicked.connect(lambda item: update_week_display_and_data(app, item.text()))
    scroll_area_layout.addWidget(app.tipologie_list)

    app.add_tipo_luogo_button = QPushButton("Aggiungi Tipologia\\Luogo")
    app.add_tipo_luogo_button.clicked.connect(lambda: add_tipo_luogo(app))
    scroll_area_layout.addWidget(app.add_tipo_luogo_button)

    app.modify_tipo_luogo_button = QPushButton("Modifica Tipologia\\Luogo")
    app.modify_tipo_luogo_button.clicked.connect(lambda: modify_selected_tipo_luogo(app))
    scroll_area_layout.addWidget(app.modify_tipo_luogo_button)

    app.remove_tipo_luogo_button = QPushButton("Rimuovi Tipologia\\Luogo")
    app.remove_tipo_luogo_button.clicked.connect(lambda: remove_tipo_luogo(app))
    scroll_area_layout.addWidget(app.remove_tipo_luogo_button)

    app.fix_orari_button = QPushButton("Fix Orari Mancanti")
    app.fix_orari_button.clicked.connect(lambda: fix_orari(app))  # Add your logic in fix_orari
    scroll_area_layout.addWidget(app.fix_orari_button)

    app.fix_proclamatori_button = QPushButton("Fix Disponibilità Proclamatori")
    app.fix_proclamatori_button.clicked.connect(lambda: fix_proclamatori(app))  # Add your logic in fix_proclamatori_button
    scroll_area_layout.addWidget(app.fix_proclamatori_button)

    app.gestione_table = QWidget()
    app.gestione_table.setLayout(QVBoxLayout())
    scroll_area_layout.addWidget(app.gestione_table)

    app.week_display_and_data = QWidget()
    app.week_display_and_data.setLayout(QVBoxLayout())
    scroll_area_layout.addWidget(app.week_display_and_data)

    scroll_area.setWidget(scroll_area_content)  # Imposta il contenuto della scroll area
    gestione_layout.addWidget(scroll_area)  # Aggiungi la scroll area al layout principale

    tab_widget.addTab(gestione_tab, "Tipologia, Luogo e Fascia")
    
    # --- Tab Programmazione --- 
    programmazione_tab = QWidget()
    programmazione_layout = QVBoxLayout(programmazione_tab)

    # Creazione della scroll area
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)  # Permette al widget di ridimensionarsi
    scroll_area_content = QWidget()  # Widget contenitore per il layout della scroll area
    scroll_area_layout = QVBoxLayout(scroll_area_content)

    # Pulsanti di navigazione per il mese
    navigation_layout = QHBoxLayout()

    app.prev_month_button = QPushButton("Mese Precedente")
    app.prev_month_button.clicked.connect(lambda: change_month(app, -1))
    navigation_layout.addWidget(app.prev_month_button)

    app.current_month_label = QLabel()  # Label per mostrare il mese corrente
    navigation_layout.addWidget(app.current_month_label)

    app.next_month_button = QPushButton("Mese Successivo")
    app.next_month_button.clicked.connect(lambda: change_month(app, 1))
    navigation_layout.addWidget(app.next_month_button)

    scroll_area_layout.addLayout(navigation_layout)

    # Layout del calendario personalizzato
    app.custom_calendar_layout = QGridLayout()
    app.day_buttons = {}
    app.current_date = QDate.currentDate()  # Data corrente iniziale

    update_calendar(app)  # Funzione per aggiornare il calendario

    scroll_area_layout.addLayout(app.custom_calendar_layout)

    # Lista per visualizzare le assegnazioni confermate
    app.programmazione_list = QListWidget()
    scroll_area_layout.addWidget(app.programmazione_list)

    scroll_area.setWidget(scroll_area_content)  # Imposta il contenuto della scroll area
    programmazione_layout.addWidget(scroll_area)  # Aggiungi la scroll area al layout principale

    tab_widget.addTab(programmazione_tab, "Programmazione")

    app.tabs.addTab(espositore_tab, "Espositore")
    app.tabs.currentChanged.connect(lambda index: load_espositore_data_from_dropbox(app) if index == app.tabs.indexOf(espositore_tab) else None)

    app.week_widget.hide()
    app.calendar.hide()

def update_calendar(app):
    # Pulisci la griglia dei giorni
    while app.custom_calendar_layout.count():
        item = app.custom_calendar_layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()

    # Ottieni il mese corrente
    days_in_month = app.current_date.daysInMonth()
    first_day_of_month = app.current_date.addDays(-app.current_date.day() + 1)  # Primo giorno del mese corrente
    start_day_of_week = first_day_of_month.dayOfWeek()  # 1 = Lun, 2 = Mar, ..., 7 = Dom

    # Aggiorna l'etichetta del mese corrente
    app.current_month_label.setText(app.current_date.toString("MMMM yyyy"))  # Mostra mese e anno

    # Riempie i giorni del mese nella griglia
    for day in range(1, days_in_month + 1):
        day_date = QDate(app.current_date.year(), app.current_date.month(), day)
        grid_row = (start_day_of_week + day - 2) // 7  # Calcola la riga in base al giorno della settimana
        grid_column = (start_day_of_week + day - 2) % 7  # Calcola la colonna in base al giorno della settimana
        
        button = QPushButton(str(day))
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        button.setFixedSize(80, 80)
        button.setStyleSheet("background-color: lightgray; border: 1px solid black;")
        
        # Collega il pulsante alla funzione per mostrare i dettagli del giorno
        button.clicked.connect(lambda _, d=day_date: show_programmazione_dialog(app, d))
        
        app.custom_calendar_layout.addWidget(button, grid_row, grid_column)
        app.day_buttons[day_date] = button  # Memorizza il riferimento al pulsante

def change_month(app, increment):
    # Cambia il mese corrente
    app.current_date = app.current_date.addMonths(increment)
    update_calendar(app)  # Aggiorna il calendario con la nuova data

def setup_week_layout(app):
    # Questo metodo potrebbe essere vuoto ora se non è necessario
    pass

def toggle_week_or_calendar(app):
    if app.radio_uguale_tutte_settimane.isChecked():
        app.week_widget.show()
        app.calendar.hide()
    elif app.radio_specifica_giorni.isChecked():
        app.week_widget.hide()
        app.calendar.show()
    else:
        app.week_widget.hide()
        app.calendar.hide()
