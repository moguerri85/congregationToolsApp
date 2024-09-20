from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

def setup_benvenuto_tab(self):
    self.benvenuto_tab = QWidget()
    self.benvenuto_layout = QVBoxLayout(self.benvenuto_tab)

    # Inizializza l'etichetta di benvenuto
    self.welcome_label = QLabel("Benvenuto! Effettua il login con Dropbox per continuare.")
    self.welcome_label.setAlignment(Qt.AlignCenter)
    self.welcome_label.setStyleSheet("font-size: 18px; color: grey;")

    self.benvenuto_layout.addWidget(self.welcome_label)

    # Aggiungi il tab di benvenuto
    self.tabs.addTab(self.benvenuto_tab, "Benvenuto")
