from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
                             QPushButton, QTabWidget, QWidget, QCalendarWidget,
                             QTextEdit, QGridLayout,  QRadioButton, QButtonGroup, 
                             QSizePolicy, QScrollArea, QGroupBox, QSpinBox)
from PyQt5.QtCore import Qt, QSize, QDate

from espositore.espositore_tab_gestione import add_tipo_luogo, aggiorna_genere_sino, aggiorna_numero_utilizzi, fix_orari, fix_proclamatori, modify_selected_tipo_luogo, remove_tipo_luogo
from espositore.espositore_tab_proclamatore import add_person, aggiorna_genere, aggiorna_status_pioniere, display_person_details, remove_person, show_availability_dialog
from espositore.espositore_tab_programmazione import handle_autoabbinamento, update_calendar
from espositore.espositore_utils import create_next_icon, create_prev_icon, import_disponibilita, on_tab_changed, update_week_display_and_data
from utils.auth_utility import load_espositore_data_from_dropbox
from utils.logging_custom import logging_custom

def setup_espositore_tab(app):
    if not hasattr(app, 'tabs') or not isinstance(app.tabs, QTabWidget):
        raise RuntimeError("app.tabs must be a QTabWidget instance")

    espositore_tab = QWidget()
    main_layout = QVBoxLayout(espositore_tab)  # Cambiato da QHBoxLayout a QVBoxLayout per aggiungere le righe sopra i tab

    # --- Righe per data e ora ultimo caricamento e ultima modifica ---
    app.last_import_hourglass_label = QLabel(f"Ultimo import disponibilità: nessuna modifica")
    app.last_modification_label = QLabel("Ultima modifica effettuata: nessuna modifica")

    # Crea il pulsante "Importa"
    #import_button = QPushButton("Importa da Hourglass")
    #import_button.setFixedSize(QSize(120, 30))  # Opzionale: dimensioni fisse per il pulsante

    # Collega il pulsante a una funzione (da definire) per gestire l'importazione
    #import_button.clicked.connect(lambda: import_disponibilita(app))
    #main_layout.addWidget(import_button)
    
    main_layout.addWidget(app.last_import_hourglass_label)
    main_layout.addWidget(app.last_modification_label)

    # --- Tab widget ---
    tab_widget = QTabWidget()
    main_layout.addWidget(tab_widget)

    app.people = {}
    app.tipo_luogo_schedule = {}
    app.tipologie = {}
    app.day_buttons = {} #utilizzato per il calendario degli appuntamenti
    app.person_schedule = {}
    app.last_import_hourglass = {}
    app.autoabbinamento_gender_sino = {}
    app.numero_utilizzi = {}

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
    app.detail_label = QLabel("Dettaglio del Proclamatore")
    app.detail_label.setAlignment(Qt.AlignCenter)
    scroll_area_layout.addWidget(app.detail_label)

    app.detail_text = QTextEdit()
    app.detail_text.setReadOnly(True)
    scroll_area_layout.addWidget(app.detail_text)

    # --- Genere
    genere_group_box = QGroupBox("Fratello\\Sorella")
    genere_layout = QVBoxLayout()  # Layout per i radio buttons all'interno del GroupBox

    # Create radio buttons
    app.radio_group_genere = QButtonGroup()
    app.fratello_radio = QRadioButton("Fratello")
    app.sorella_radio = QRadioButton("Sorella")

    # Add buttons to the button group
    app.radio_group_genere.addButton(app.fratello_radio)
    app.radio_group_genere.addButton(app.sorella_radio)
    

    # Add radio buttons to the layout
    genere_layout.addWidget(app.fratello_radio)
    genere_layout.addWidget(app.sorella_radio)

    # Set the layout for the GroupBox
    genere_group_box.setLayout(genere_layout)

    # Add the GroupBox to the main layout
    scroll_area_layout.addWidget(genere_group_box)
    
    app.fratello_radio.toggled.connect(lambda checked: aggiorna_genere(app) if checked else None)
    app.sorella_radio.toggled.connect(lambda checked: aggiorna_genere(app) if checked else None)

    # --- Add GroupBox for Pioniere Status ---
    pioniere_group_box = QGroupBox("Stato Pioniere")
    pioniere_layout = QVBoxLayout()  # Layout per i radio buttons all'interno del GroupBox

    # Create radio buttons
    app.radio_group_pioniere = QButtonGroup()
    app.no_pioniere_radio = QRadioButton("No Pioniere")
    app.ausiliare_radio = QRadioButton("Pioniere Ausiliare")
    app.regolare_radio = QRadioButton("Pioniere Regolare")

    # Add buttons to the button group
    app.radio_group_pioniere.addButton(app.regolare_radio)
    app.radio_group_pioniere.addButton(app.ausiliare_radio)
    app.radio_group_pioniere.addButton(app.no_pioniere_radio)

    # Add radio buttons to the layout
    pioniere_layout.addWidget(app.regolare_radio)
    pioniere_layout.addWidget(app.ausiliare_radio)
    pioniere_layout.addWidget(app.no_pioniere_radio)

    # Set the layout for the GroupBox
    pioniere_group_box.setLayout(pioniere_layout)

    # Add the GroupBox to the main layout
    scroll_area_layout.addWidget(pioniere_group_box)

    # Load the current status if available
    # Connect the toggled signal to aggiorna_status_pioniere function
    app.no_pioniere_radio.toggled.connect(lambda checked: aggiorna_status_pioniere(app) if checked else None)
    app.ausiliare_radio.toggled.connect(lambda checked: aggiorna_status_pioniere(app) if checked else None)
    app.regolare_radio.toggled.connect(lambda checked: aggiorna_status_pioniere(app) if checked else None)

    # --- Add GroupBox for Week or Specific Days Selection ---
    giorni_group_box = QGroupBox("Scelta della Disponibilità")
    giorni_layout = QVBoxLayout()  # Layout per i radio buttons all'interno del GroupBox

    # Create radio buttons
    app.radio_uguale_tutte_settimane = QRadioButton("Uguale a tutte le settimane")
    app.radio_specifica_giorni = QRadioButton("Specifica i giorni")

    # Add buttons to the button group
    app.radio_group_disponibilita = QButtonGroup()
    app.radio_group_disponibilita.addButton(app.radio_uguale_tutte_settimane)
    app.radio_group_disponibilita.addButton(app.radio_specifica_giorni)

    # Connect the toggled signal to the toggle_week_or_calendar function
    app.radio_uguale_tutte_settimane.toggled.connect(lambda: toggle_week_or_calendar(app))
    app.radio_specifica_giorni.toggled.connect(lambda: toggle_week_or_calendar(app))

    # Add radio buttons to the layout
    giorni_layout.addWidget(app.radio_uguale_tutte_settimane)
    giorni_layout.addWidget(app.radio_specifica_giorni)


    # Dopo aver creato i radio button, disabilitali inizialmente
    # Disabilita i radio button all'inizio
    for button in app.radio_group_pioniere.buttons():
        button.setEnabled(False)

    for button in app.radio_group_genere.buttons():
        button.setEnabled(False)

    for button in app.radio_group_disponibilita.buttons():
        button.setEnabled(False)

    # Set the layout for the GroupBox
    giorni_group_box.setLayout(giorni_layout)

    # Add the GroupBox to the main layout
    scroll_area_layout.addWidget(giorni_group_box)


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
    tipo_luogo_tab = QWidget()
    gestione_layout = QVBoxLayout(tipo_luogo_tab)

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

    app.tipo_luogo_table = QWidget()
    app.tipo_luogo_table.setLayout(QVBoxLayout())
    scroll_area_layout.addWidget(app.tipo_luogo_table)

    app.week_display_and_data = QWidget()
    app.week_display_and_data.setLayout(QVBoxLayout())
    scroll_area_layout.addWidget(app.week_display_and_data)

    scroll_area.setWidget(scroll_area_content)  # Imposta il contenuto della scroll area
    gestione_layout.addWidget(scroll_area)  # Aggiungi la scroll area al layout principale

    tab_widget.addTab(tipo_luogo_tab, "Tipologia, Luogo e Fascia")
    
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

    # Aggiungi le immagini ai pulsanti
    app.prev_month_button = QPushButton()
    app.prev_month_button.setIcon(create_prev_icon(30))  # Utilizza un'icona di 40x40 pixel
    app.prev_month_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # Dimensione fissa
    app.prev_month_button.clicked.connect(lambda: change_month(app, -1))
    navigation_layout.addWidget(app.prev_month_button)

    app.current_month_label = QLabel()  # Label per mostrare il mese corrente
    app.current_month_label.setAlignment(Qt.AlignCenter)
    navigation_layout.addWidget(app.current_month_label)

    app.next_month_button = QPushButton()
    app.next_month_button.setIcon(create_next_icon(30))  # Utilizza un'icona di 40x40 pixel
    app.next_month_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # Dimensione fissa
    app.next_month_button.clicked.connect(lambda: change_month(app, 1))
    navigation_layout.addWidget(app.next_month_button)

    scroll_area_layout.addLayout(navigation_layout)

    # Sezione per l'autocompleta e la lista delle tipologie
    tipologie_layout = QHBoxLayout()  # Layout orizzontale per il tasto e la lista

    # Autocompleta Button
    app.autoabbinamento_button = QPushButton("Auto abbinamento")
    app.autoabbinamento_button.clicked.connect(lambda: handle_autoabbinamento(app))
    tipologie_layout.addWidget(app.autoabbinamento_button)  # Aggiungi il pulsante al layout

    # Multi-selection for tipologie using QListWidget
    app.multi_tipologie = QListWidget()
    app.multi_tipologie.setSelectionMode(QListWidget.MultiSelection)  # Enable multi-selection

    tipologie_layout.addWidget(QLabel("Seleziona Tipologie:"))  # Aggiungi etichetta per le tipologie
    tipologie_layout.addWidget(app.multi_tipologie)  # Aggiungi la QListWidget al layout

    scroll_area_layout.addLayout(tipologie_layout)  # Aggiungi il layout delle tipologie alla scroll area

    # Layout del calendario personalizzato
    app.custom_calendar_layout = QGridLayout()
    app.day_buttons = {}
    app.current_date = QDate.currentDate()  # Data corrente iniziale

    update_calendar(app)  # Funzione per aggiornare il calendario

    scroll_area_layout.addLayout(app.custom_calendar_layout)

    scroll_area.setWidget(scroll_area_content)  # Imposta il contenuto della scroll area
    programmazione_layout.addWidget(scroll_area)  # Aggiungi la scroll area al layout principale

    tab_widget.addTab(programmazione_tab, "Programmazione")
    tab_widget.currentChanged.connect(lambda index: on_tab_changed(app, index, tab_widget))


    # --- Nuovo Tab Gestione --- 
    gestione_tab = QWidget()
    gestione_layout = QVBoxLayout(gestione_tab)

    # Creazione della scroll area per il nuovo tab
    gestione_scroll_area = QScrollArea()
    gestione_scroll_area.setWidgetResizable(True)  # Permette al widget di ridimensionarsi
    gestione_scroll_area_content = QWidget()  # Widget contenitore per il layout della scroll area
    gestione_scroll_area_layout = QVBoxLayout(gestione_scroll_area_content)

    # Pulsante "Importa" da aggiungere qui
    import_button = QPushButton("Importa da Hourglass")
    import_button.setFixedSize(QSize(120, 30))  # Opzionale: dimensioni fisse per il pulsante
    import_button.clicked.connect(lambda: import_disponibilita(app))
    gestione_scroll_area_layout.addWidget(import_button)  # Aggiungi il pulsante al layout

    # --- Genere
    genere_sino_group_box = QGroupBox("Autocompletamento tra lo stesso genere")
    genere_sino_layout = QVBoxLayout()  # Layout per i radio buttons all'interno del GroupBox

    # Create radio buttons
    app.radio_group_genere_sino = QButtonGroup()
    app.genere_si_radio = QRadioButton("Si")
    app.genere_no_radio = QRadioButton("No")

    # Add buttons to the button group
    app.radio_group_genere_sino.addButton(app.genere_si_radio)
    app.radio_group_genere_sino.addButton(app.genere_no_radio)

    # Add radio buttons to the layout
    genere_sino_layout.addWidget(app.genere_si_radio)
    genere_sino_layout.addWidget(app.genere_no_radio)

    # Set the layout for the GroupBox
    genere_sino_group_box.setLayout(genere_sino_layout)

    # Add the GroupBox to the scroll area layout
    gestione_scroll_area_layout.addWidget(genere_sino_group_box)

    # --- Numero di utilizzi mensile ---

    # GroupBox per il numero di utilizzi
    utilizzo_mensile_group_box = QGroupBox("Numero di utilizzi mensile")
    utilizzo_mensile_layout = QVBoxLayout()

    # Label e spinbox per pionieri
    pionieri_label = QLabel("Pionieri:")
    app.pionieri_mensile_spinbox = QSpinBox()
    app.pionieri_mensile_spinbox.setRange(0, 7)  # Imposta il range (0-7)
           
    # Aggiungi label e spinbox al layout
    utilizzo_mensile_layout.addWidget(pionieri_label)
    utilizzo_mensile_layout.addWidget(app.pionieri_mensile_spinbox)

    # Label e spinbox per proclamatori
    proclamatori_label = QLabel("Proclamatori:")
    app.proclamatori_mensile_spinbox = QSpinBox()
    app.proclamatori_mensile_spinbox.setRange(0, 7)  # Imposta il range (0-7)
    
    # Aggiungi label e spinbox al layout
    utilizzo_mensile_layout.addWidget(proclamatori_label)
    utilizzo_mensile_layout.addWidget(app.proclamatori_mensile_spinbox)
    
    # Imposta il layout del GroupBox
    utilizzo_mensile_group_box.setLayout(utilizzo_mensile_layout)

    # Aggiungi il GroupBox al layout della scroll area
    gestione_scroll_area_layout.addWidget(utilizzo_mensile_group_box)

    # --- Numero di utilizzi settimanale ---

    # GroupBox per il numero di utilizzi
    utilizzo_settimanale_group_box = QGroupBox("Numero di utilizzi settimanale")
    utilizzo_settimanale_layout = QVBoxLayout()

    # Label e spinbox per pionieri
    pionieri_label = QLabel("Pionieri:")
    app.pionieri_settimanale_spinbox = QSpinBox()
    app.pionieri_settimanale_spinbox.setRange(0, 7)  # Imposta il range (0-7)
    
    # Aggiungi label e spinbox al layout
    utilizzo_settimanale_layout.addWidget(pionieri_label)
    utilizzo_settimanale_layout.addWidget(app.pionieri_settimanale_spinbox)

    # Label e spinbox per proclamatori
    proclamatori_label = QLabel("Proclamatori:")
    app.proclamatori_settimanale_spinbox = QSpinBox()
    app.proclamatori_settimanale_spinbox.setRange(0, 7)  # Imposta il range (0-7)    

    # Aggiungi label e spinbox al layout
    utilizzo_settimanale_layout.addWidget(proclamatori_label)
    utilizzo_settimanale_layout.addWidget(app.proclamatori_settimanale_spinbox)

    # Imposta il layout del GroupBox
    utilizzo_settimanale_group_box.setLayout(utilizzo_settimanale_layout)

    # Aggiungi il GroupBox al layout della scroll area
    gestione_scroll_area_layout.addWidget(utilizzo_settimanale_group_box)
        
    app.pionieri_mensile_spinbox.valueChanged.connect(lambda value: aggiorna_numero_utilizzi("pionieri_mes", value, app))
    app.proclamatori_mensile_spinbox.valueChanged.connect(lambda value: aggiorna_numero_utilizzi("proclamatori_mes", value, app))
    
    app.pionieri_settimanale_spinbox.valueChanged.connect(lambda value: aggiorna_numero_utilizzi("pionieri_sett", value, app))
    app.proclamatori_settimanale_spinbox.valueChanged.connect(lambda value: aggiorna_numero_utilizzi("proclamatori_sett", value, app))

    # Imposta il contenuto della scroll area
    gestione_scroll_area.setWidget(gestione_scroll_area_content)
    gestione_layout.addWidget(gestione_scroll_area)  # Aggiungi la scroll area al layout principale

    # Collegamento dei radio buttons a una funzione per aggiornare lo stato
    app.genere_si_radio.toggled.connect(lambda checked: aggiorna_genere_sino(app) if checked else None)
    app.genere_no_radio.toggled.connect(lambda checked: aggiorna_genere_sino(app) if checked else None)

    # Aggiungi il nuovo tab al QTabWidget
    tab_widget.addTab(gestione_tab, "Gestione")

    app.tabs.addTab(espositore_tab, "Espositore")
    app.tabs.currentChanged.connect(lambda index: load_espositore_data_from_dropbox(app) if index == app.tabs.indexOf(espositore_tab) else None)

    app.week_widget.hide()
    app.calendar.hide()


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
