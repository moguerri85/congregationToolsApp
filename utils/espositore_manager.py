from PyQt5.QtWidgets import (QInputDialog, QMessageBox, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QWidget, QGridLayout)
from PyQt5.QtCore import Qt

def add_person(app):
    try:
        text, ok = QInputDialog.getText(app, "Aggiungi Proclamatore", "Nome del Proclamatore:")
        if ok and text:
            app.person_list.addItem(text)
            app.person_schedule[text] = {}
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
            update_turni_table(app)
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

def display_person_details(app, item):
    try:
        person_name = item.text()
        if person_name in app.person_schedule:
            details = "\n".join([f"Data: {date}, Fasce Orarie: {', '.join([f['fascia_oraria'] for f in fasce])}" 
                                 for date, fasce in app.person_schedule[person_name].items()])
            app.detail_text.setText(details)
        else:
            app.detail_text.setText("Nessun dettaglio disponibile.")
        update_turni_table(app)
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

def add_tipologia(app):
    new_tipologia, ok = QInputDialog.getText(app, 'Nuova Tipologia', 'Inserisci il nome della tipologia:')
    if ok and new_tipologia:
        app.tipologie_list.addItem(new_tipologia)
        update_week_display(app, new_tipologia)

def remove_tipologia(app):
    try:
        selected_item = app.tipologie_list.currentItem()
        if selected_item:
            tipologia_name = selected_item.text()
            app.tipologie_list.takeItem(app.tipologie_list.row(selected_item))
            if tipologia_name in app.tipologia_schedule:
                del app.tipologia_schedule[tipologia_name]
            update_turni_table(app)
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore: {str(e)}")

def update_turni_table(app):
    try:
        # Clear existing layout
        if app.turni_table.layout():
            for i in reversed(range(app.turni_table.layout().count())):
                widget = app.turni_table.layout().itemAt(i).widget()
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
    update_turni_table(app)

def update_week_display(app, tipologia):
    """Visualizza una settimana tipo (da lunedì a domenica) con possibilità di aggiungere fasce orarie."""
    clear_week_display(app)
    
    week_layout = QHBoxLayout()

    # Giorni della settimana
    days_of_week = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

    for day in days_of_week:
        day_button = QPushButton(day)
        day_button.setFixedSize(100, 100)
        day_button.clicked.connect(lambda _, d=day: add_fascia_to_day(app, tipologia, d))
        week_layout.addWidget(day_button)

    app.week_display.setLayout(week_layout)
    app.week_display.update()

def clear_week_display(app):
    """Pulisce la visualizzazione della settimana."""
    if app.week_display.layout():
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
