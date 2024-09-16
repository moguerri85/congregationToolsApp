from PyQt5.QtWidgets import  QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit
from PyQt5.QtCore import Qt

def setup_weekend(self):
    self.vertical_layout = QVBoxLayout()
    button = QPushButton("Genera Stampa Fine Settimana")
    button.setFixedWidth(200)
    button.setFixedHeight(30)
    button.clicked.connect(self.call_load_schedule_fineSettimana)
    self.vertical_layout.addWidget(button)
    self.vertical_layout.setAlignment(Qt.AlignCenter)
    self.web_layout.addLayout(self.vertical_layout)
    
def setup_infra_week(self):
    self.vertical_layout = QVBoxLayout()
    button = QPushButton("Genera Stampa Infrasettimanale")
    add_text_field(self, "Numero di settimane:")
    button.setFixedWidth(200)
    button.setFixedHeight(30)
    button.clicked.connect(lambda: self.call_load_schedule_infraSettimanale(self.text_field))
    self.vertical_layout.addWidget(button)
    self.vertical_layout.setAlignment(Qt.AlignCenter)
    self.web_layout.addLayout(self.vertical_layout)

def setup_av_attendant(self):
    self.vertical_layout = QVBoxLayout()
    add_text_field(self, "Numero di mesi:")
    button = QPushButton("Genera Stampa Incarchi")
    button.setFixedWidth(200)
    button.setFixedHeight(30)
    button.clicked.connect(lambda: self.call_load_schedule_av_uscieri(self.text_field))
    self.vertical_layout.addWidget(button)
    self.vertical_layout.setAlignment(Qt.AlignCenter)
    self.web_layout.addLayout(self.vertical_layout)

def setup_cleaning(self):
    self.vertical_layout = QVBoxLayout()
    add_text_field(self, "Numero di mesi:")
    button = QPushButton("Genera Stampa Pulizie")
    button.setFixedWidth(200)
    button.setFixedHeight(30)
    button.clicked.connect(lambda: self.call_load_schedule_pulizie(self.text_field))
    self.vertical_layout.addWidget(button)
    # Center the horizontal layout within the web layout
    self.vertical_layout.setAlignment(Qt.AlignCenter)
    self.web_layout.addLayout(self.vertical_layout)

def setup_testimonianza_pubblica(self):
    self.vertical_layout = QVBoxLayout()
    add_text_field(self, "Numero di mesi:")
    button = QPushButton("Genera Stampa Testimonianza Pubblica")
    button.setFixedWidth(200)
    button.setFixedHeight(30)
    button.clicked.connect(lambda: self.call_load_schedule_testimonianza_pubblica(self.text_field))
    self.vertical_layout.addWidget(button)
    self.vertical_layout.setAlignment(Qt.AlignCenter)
    self.web_layout.addLayout(self.vertical_layout)

def setup_groups(self):
    from hourglass.hourglass_manager import load_schedule_gruppi_servizio
    button = QPushButton("Genera Stampa Gruppi di Servizio")
    button.setFixedWidth(200)
    button.setFixedHeight(30)
    button.clicked.connect(load_schedule_gruppi_servizio(self))
    self.vertical_layout.addWidget(button)

def add_text_field(self, label_text):
    self.text_field_layout = QVBoxLayout()  # Layout per il campo di testo
    self.text_field = QLineEdit()  # Crea il campo di testo
    self.text_field.setPlaceholderText(label_text)  # Imposta il testo di segnaposto
    self.text_field.setFixedWidth(200)  # Imposta la larghezza fissa
    self.text_field.setFixedHeight(30)  # Imposta l'altezza fissa
    self.text_field_layout.addWidget(self.text_field)  # Aggiungi il campo di testo al layout
    self.text_field_layout.setAlignment(Qt.AlignCenter)
    self.web_layout.addLayout(self.text_field_layout)  # Aggiungi il layout del campo di testo al layout principale
