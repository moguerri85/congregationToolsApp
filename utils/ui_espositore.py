from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton, QTabWidget, QWidget, QCalendarWidget,
                             QTextEdit, QMessageBox, QRadioButton, QButtonGroup, QSizePolicy, QComboBox)
from PyQt5.QtCore import Qt, QSize

from utils.espositore_manager import add_person, add_tipologia, display_person_details, remove_person, remove_tipologia, update_person_availability, update_week_display

def setup_espositore_tab(app):
    if not hasattr(app, 'tabs') or not isinstance(app.tabs, QTabWidget):
        raise RuntimeError("app.tabs must be a QTabWidget instance")

    espositore_tab = QWidget()
    main_layout = QHBoxLayout(espositore_tab)
    espositore_tab.setLayout(main_layout)
    
    tab_widget = QTabWidget()
    main_layout.addWidget(tab_widget)

    # Inizializza la struttura centralizzata per le tipologie
    app.tipologia_schedule = {}
    app.person_schedule = {}

    # --- Tab Proclamatore ---
    proclamatore_tab = QWidget()
    proclamatore_layout = QHBoxLayout(proclamatore_tab)

    left_layout = QVBoxLayout()
    left_widget = QWidget()
    left_widget.setLayout(left_layout)
    left_widget.setFixedWidth(200)  # Imposta una larghezza fissa per la sezione a sinistra

    app.person_list = QListWidget()
    app.person_list.itemClicked.connect(lambda item: display_person_details(app, item))
    left_layout.addWidget(app.person_list)

    app.add_button = QPushButton("Aggiungi Proclamatore")
    app.add_button.clicked.connect(lambda: add_person(app))
    left_layout.addWidget(app.add_button)

    app.remove_button = QPushButton("Elimina Proclamatore")
    app.remove_button.clicked.connect(lambda: remove_person(app))
    left_layout.addWidget(app.remove_button)

    proclamatore_layout.addWidget(left_widget)

    right_layout = QVBoxLayout()

    # Dettagli del proclamatore
    app.detail_label = QLabel("Dettagli del Proclamatore")
    app.detail_label.setAlignment(Qt.AlignCenter)
    right_layout.addWidget(app.detail_label)

    app.detail_text = QTextEdit()
    app.detail_text.setReadOnly(True)
    right_layout.addWidget(app.detail_text)

    # RadioButton "Uguale a tutte le settimane" e "Specifica i giorni"
    app.radio_uguale_tutte_settimane = QRadioButton("Uguale a tutte le settimane")
    app.radio_specifica_giorni = QRadioButton("Specifica i giorni")
    
    app.radio_group = QButtonGroup()
    app.radio_group.addButton(app.radio_uguale_tutte_settimane)
    app.radio_group.addButton(app.radio_specifica_giorni)

    app.radio_uguale_tutte_settimane.toggled.connect(lambda: toggle_week_or_calendar(app))
    app.radio_specifica_giorni.toggled.connect(lambda: toggle_week_or_calendar(app))
    
    right_layout.addWidget(app.radio_uguale_tutte_settimane)
    right_layout.addWidget(app.radio_specifica_giorni)

    # Widget per la settimana tipo (7 giorni) - Disposti orizzontalmente
    if not hasattr(app, 'week_widget'):
        app.week_widget = QWidget()
        app.week_layout = QHBoxLayout(app.week_widget)  # Layout orizzontale principale
    
    # Crea un layout verticale per ogni giorno
    days_of_week = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
    
    app.day_buttons = {}  # Dizionario per memorizzare i pulsanti dei giorni

    for day in days_of_week:
        day_widget = QWidget()
        day_layout = QVBoxLayout(day_widget)  # Layout verticale per ogni giorno
        
        # Label del giorno
        day_label = QLabel(day)
        day_label.setAlignment(Qt.AlignCenter)
        day_layout.addWidget(day_label)
        
        # Quadrato per la tipologia
        square_button = QPushButton()
        square_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        square_button.setFixedSize(QSize(60, 60))  # Dimensione fissa
        square_button.setStyleSheet("background-color: lightgray; border: 1px solid black;")  # Stile del quadrato
        
        # Collega il clic del pulsante a una funzione
        square_button.clicked.connect(lambda _, d=day: show_day_dialog(app, d))
        
        day_layout.addWidget(square_button)
        
        day_widget.setLayout(day_layout)
        app.week_layout.addWidget(day_widget)
        app.day_buttons[day] = square_button

    right_layout.addWidget(app.week_widget)
    setup_week_layout(app)

    # Widget per il calendario
    if not hasattr(app, 'calendar'):
        app.calendar = QCalendarWidget()
        app.calendar.clicked.connect(lambda date: show_availability_dialog(app, date))
    right_layout.addWidget(app.calendar)

    proclamatore_layout.addLayout(right_layout)
    proclamatore_tab.setLayout(proclamatore_layout)

    tab_widget.addTab(proclamatore_tab, "Proclamatore")

    # --- Tab Turni ---
    turni_tab = QWidget()
    turni_layout = QVBoxLayout(turni_tab)

    app.tipologie_list = QListWidget()
    app.tipologie_list.setSelectionMode(QListWidget.SingleSelection)
    app.tipologie_list.itemClicked.connect(lambda item: update_week_display(app, item.text()))
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

    app.week_display = QWidget()
    app.week_display.setLayout(QVBoxLayout())
    turni_layout.addWidget(app.week_display)

    tab_widget.addTab(turni_tab, "Turni")

    app.tabs.addTab(espositore_tab, "Espositore")

    # All'inizio, nascondiamo la settimana tipo e il calendario
    app.week_widget.hide()
    app.calendar.hide()

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

def show_day_dialog(app, day):
    try:
        dialog = QWidget()
        dialog.setWindowTitle(f"Seleziona Tipologia e Fascia Oraria per {day}")
        layout = QVBoxLayout(dialog)

        # Tipologia
        tipologia_label = QLabel("Seleziona la tipologia:")
        layout.addWidget(tipologia_label)
        
        tipologia_combo = QComboBox()
        for tipologia in app.tipologia_schedule.keys():
            # Filtra le tipologie disponibili per il giorno
            if day in app.tipologia_schedule[tipologia]:
                tipologia_combo.addItem(tipologia)
        layout.addWidget(tipologia_combo)

        # Fascia oraria
        fascia_label = QLabel("Seleziona la fascia oraria:")
        layout.addWidget(fascia_label)
        
        fascia_combo = QComboBox()
        layout.addWidget(fascia_combo)

        def update_fasce():
            selected_tipologia = tipologia_combo.currentText()
            if selected_tipologia in app.tipologia_schedule and day in app.tipologia_schedule[selected_tipologia]:
                fasce = app.tipologia_schedule[selected_tipologia][day]
                fascia_combo.clear()
                fascia_combo.addItems(fasce)

        tipologia_combo.currentIndexChanged.connect(update_fasce)
        update_fasce()

        confirm_button = QPushButton("Conferma")
        confirm_button.clicked.connect(lambda: update_day_selection(app, day, tipologia_combo.currentText(), fascia_combo.currentText(), dialog))
        layout.addWidget(confirm_button)

        dialog.setLayout(layout)
        dialog.show()

    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

def update_day_selection(app, day, tipologia, fascia, dialog):
    try:
        # Esegui qui l'aggiornamento della selezione
        # ad esempio, salva la selezione per il giorno specificato
        print(f"Selezionato per {day}: Tipologia={tipologia}, Fascia={fascia}")
        dialog.accept()  # Chiudi il dialogo
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

def show_availability_dialog(app, date):
    try:
        dialog = QWidget()
        dialog.setWindowTitle("Aggiungi Disponibilità")
        layout = QVBoxLayout(dialog)

        tipologia_label = QLabel("Seleziona la tipologia:")
        layout.addWidget(tipologia_label)
        
        tipologia_combo = QComboBox()
        for tipologia in app.tipologia_schedule.keys():
            tipologia_combo.addItem(tipologia)
        layout.addWidget(tipologia_combo)

        fascia_label = QLabel("Seleziona la fascia oraria:")
        layout.addWidget(fascia_label)
        
        fascia_combo = QComboBox()
        layout.addWidget(fascia_combo)

        def update_fasce():
            selected_tipologia = tipologia_combo.currentText()
            if selected_tipologia in app.tipologia_schedule:
                fasce = [fascia for day in app.tipologia_schedule[selected_tipologia].values() for fascia in day]
                fascia_combo.clear()
                fascia_combo.addItems(fasce)

        tipologia_combo.currentIndexChanged.connect(update_fasce)
        update_fasce()

        confirm_button = QPushButton("Conferma")
        confirm_button.clicked.connect(lambda: update_person_availability(app, date, tipologia_combo.currentText(), fascia_combo.currentText(), dialog))
        layout.addWidget(confirm_button)

        dialog.setLayout(layout)
        dialog.show()

    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")
