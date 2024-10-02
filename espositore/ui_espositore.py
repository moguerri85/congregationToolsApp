from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton, QTabWidget, QWidget, QCalendarWidget,
                             QTextEdit, QMessageBox, QRadioButton, QButtonGroup, QSizePolicy, QComboBox)
from PyQt5.QtCore import Qt, QSize, QDateTime

from espositore.espositore_tab_gestione import add_tipo_luogo, display_person_details, modify_selected_tipo_luogo, remove_tipo_luogo
from espositore.espositore_tab_proclamatore import add_person, remove_person, show_availability_dialog
from espositore.espositore_utils import update_week_display


def setup_espositore_tab(app):
    if not hasattr(app, 'tabs') or not isinstance(app.tabs, QTabWidget):
        raise RuntimeError("app.tabs must be a QTabWidget instance")

    espositore_tab = QWidget()
    main_layout = QVBoxLayout(espositore_tab)  # Cambiato da QHBoxLayout a QVBoxLayout per aggiungere le righe sopra i tab

    # --- Righe per data e ora ultimo caricamento e ultima modifica ---
    app.last_load_label = QLabel(f"Ultimo import disponibilità: {QDateTime.currentDateTime().toString('dd/MM/yyyy HH:mm:ss')}")
    app.last_modification_label = QLabel("Ultima modifica effettuata: nessuna modifica")

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

    app.radio_uguale_tutte_settimane = QRadioButton("Uguale a tutte le settimane")
    app.radio_specifica_giorni = QRadioButton("Specifica i giorni")

    app.radio_group = QButtonGroup()
    app.radio_group.addButton(app.radio_uguale_tutte_settimane)
    app.radio_group.addButton(app.radio_specifica_giorni)

    app.radio_uguale_tutte_settimane.toggled.connect(lambda: toggle_week_or_calendar(app))
    app.radio_specifica_giorni.toggled.connect(lambda: toggle_week_or_calendar(app))

    right_layout.addWidget(app.radio_uguale_tutte_settimane)
    right_layout.addWidget(app.radio_specifica_giorni)

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

    right_layout.addWidget(app.week_widget)
    setup_week_layout(app)

    if not hasattr(app, 'calendar'):
        app.calendar = QCalendarWidget()
        app.calendar.clicked.connect(lambda date: show_availability_dialog(app, date))
    right_layout.addWidget(app.calendar)

    proclamatore_layout.addLayout(left_layout)
    proclamatore_layout.addLayout(right_layout)
    proclamatore_tab.setLayout(proclamatore_layout)

    tab_widget.addTab(proclamatore_tab, "Proclamatore")

    # --- Tab Turni ---
    gestione_tab = QWidget()
    gestione_layout = QVBoxLayout(gestione_tab)

    app.tipologie_list = QListWidget()
    app.tipologie_list.setSelectionMode(QListWidget.SingleSelection)
    app.tipologie_list.itemClicked.connect(lambda item: update_week_display(app, item.text()))
    gestione_layout.addWidget(app.tipologie_list)

    app.add_tipo_luogo_button = QPushButton("Aggiungi Tipologia\\Luogo")
    app.add_tipo_luogo_button.clicked.connect(lambda: add_tipo_luogo(app))
    gestione_layout.addWidget(app.add_tipo_luogo_button)

    app.modify_tipo_luogo_button = QPushButton("Modifica Tipologia\\Luogo")
    app.modify_tipo_luogo_button.clicked.connect(lambda: modify_selected_tipo_luogo(app))
    gestione_layout.addWidget(app.modify_tipo_luogo_button)

    app.remove_tipo_luogo_button = QPushButton("Rimuovi Tipologia\\Luogo")
    app.remove_tipo_luogo_button.clicked.connect(lambda: remove_tipo_luogo(app))
    gestione_layout.addWidget(app.remove_tipo_luogo_button)

    app.gestione_table = QWidget()
    app.gestione_table.setLayout(QVBoxLayout())
    gestione_layout.addWidget(app.gestione_table)

    app.week_display = QWidget()
    app.week_display.setLayout(QHBoxLayout())
    gestione_layout.addWidget(app.week_display)

    tab_widget.addTab(gestione_tab, "Gestione Espositori")

    app.tabs.addTab(espositore_tab, "Espositore")

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
