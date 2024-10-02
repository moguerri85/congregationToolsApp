from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QFrame, QPushButton, QLineEdit
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt

def setup_hourglass_tab(self):
    self.hourglass_tab = QWidget()
    self.hourglass_layout = QVBoxLayout(self.hourglass_tab)

    # Crea e configura il QWebEngineView
    self.view = QWebEngineView()
    self.hourglass_layout.addWidget(self.view)

    # Imposta il layout per il tab
    self.hourglass_tab.setLayout(self.hourglass_layout)

    # Aggiungi il tab ai tab widget
    self.tabs.addTab(self.hourglass_tab, "Hourglass")

def setup_weekend(self):
    horizontal_layout = QHBoxLayout()
    horizontal_layout.setContentsMargins(0, 0, 0, 0)  # Rimuove i margini interni
    horizontal_layout.setSpacing(10)  # Spazio tra gli elementi

    # Crea e configura il pulsante
    button = QPushButton("Genera Stampa Fine Settimana")
    button.setFixedWidth(200)
    button.setFixedHeight(30)
    button.clicked.connect(self.call_load_schedule_fineSettimana)
    
    horizontal_layout.addWidget(button)
    horizontal_layout.setAlignment(Qt.AlignCenter)
    self.hourglass_layout.addLayout(horizontal_layout)

def setup_infra_week(self):
    horizontal_layout = QHBoxLayout()
    horizontal_layout.setContentsMargins(0, 0, 0, 0)
    horizontal_layout.setSpacing(10)

    # Aggiungi il campo di testo e il pulsante
    add_text_field(self, "Numero di settimane:", horizontal_layout)
    button = QPushButton("Genera Stampa Infrasettimanale")
    button.setFixedWidth(200)
    button.setFixedHeight(30)
    button.clicked.connect(lambda: self.call_load_schedule_infraSettimanale(self.text_field))
    
    horizontal_layout.addWidget(button)
    horizontal_layout.setAlignment(Qt.AlignCenter)
    self.hourglass_layout.addLayout(horizontal_layout)

def setup_av_attendant(self):
    horizontal_layout = QHBoxLayout()
    horizontal_layout.setContentsMargins(0, 0, 0, 0)
    horizontal_layout.setSpacing(10)

    # Aggiungi il campo di testo e il pulsante
    add_text_field(self, "Numero di mesi:", horizontal_layout)
    button = QPushButton("Genera Stampa Incarichi")
    button.setFixedWidth(200)
    button.setFixedHeight(30)
    button.clicked.connect(lambda: self.call_load_schedule_av_uscieri(self.text_field))
    
    horizontal_layout.addWidget(button)
    horizontal_layout.setAlignment(Qt.AlignCenter)
    self.hourglass_layout.addLayout(horizontal_layout)

def setup_cleaning(self):
    horizontal_layout = QHBoxLayout()
    horizontal_layout.setContentsMargins(0, 0, 0, 0)
    horizontal_layout.setSpacing(10)

    # Aggiungi il campo di testo e il pulsante
    add_text_field(self, "Numero di mesi:", horizontal_layout)
    button = QPushButton("Genera Stampa Pulizie")
    button.setFixedWidth(200)
    button.setFixedHeight(30)
    button.clicked.connect(lambda: self.call_load_schedule_pulizie(self.text_field))
    
    horizontal_layout.addWidget(button)
    horizontal_layout.setAlignment(Qt.AlignCenter)
    self.hourglass_layout.addLayout(horizontal_layout)

def setup_testimonianza_pubblica(self):
    horizontal_layout = QHBoxLayout()
    horizontal_layout.setContentsMargins(0, 0, 0, 0)
    horizontal_layout.setSpacing(10)

    # Aggiungi il campo di testo e il primo pulsante
    add_text_field(self, "Numero di mesi:", horizontal_layout)
    button = QPushButton("Genera Stampa Testimonianza Pubblica")
    button.setFixedWidth(200)
    button.setFixedHeight(30)
    button.clicked.connect(lambda: self.call_load_schedule_testimonianza_pubblica(self.text_field))
    
    horizontal_layout.addWidget(button)

    # Aggiungi una linea di separazione
    line = QFrame()
    line.setFrameShape(QFrame.VLine)
    line.setFrameShadow(QFrame.Sunken)
    horizontal_layout.addWidget(line)

    # Aggiungi un nuovo pulsante accanto alla linea
    disp_button = QPushButton("Scarica Disponibilità")
    disp_button.setFixedWidth(150)
    disp_button.setFixedHeight(30)
    disp_button.clicked.connect(self.call_load_disponibilita_testimonianza_pubblica) 
    horizontal_layout.addWidget(disp_button)

    horizontal_layout.setAlignment(Qt.AlignCenter)
    self.hourglass_layout.addLayout(horizontal_layout)

def setup_groups(self):
    horizontal_layout = QHBoxLayout()
    horizontal_layout.setContentsMargins(0, 0, 0, 0)
    horizontal_layout.setSpacing(10)

    # Crea e configura il pulsante
    button = QPushButton("Genera Stampa Gruppi di Servizio")
    button.setFixedWidth(200)
    button.setFixedHeight(30)
    button.clicked.connect(self.call_load_schedule_gruppi_servizio)
    
    horizontal_layout.addWidget(button)
    horizontal_layout.setAlignment(Qt.AlignCenter)
    self.hourglass_layout.addLayout(horizontal_layout)

def add_text_field(self, label_text, horizontal_layout):
    self.text_field = QLineEdit()
    self.text_field.setPlaceholderText(label_text)
    self.text_field.setFixedWidth(200)
    self.text_field.setFixedHeight(30)
    horizontal_layout.addWidget(self.text_field)
