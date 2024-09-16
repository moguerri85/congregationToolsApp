import os
from PyQt5.QtCore import QUrl
from utils.utility import handle_download
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QVBoxLayout, QWidget


def setup_vigeo_tab(self):
        self.local_html_view = QWebEngineView()
        
        self.local_tab = QWidget()
        self.local_layout = QVBoxLayout(self.local_tab)
        self.local_layout.addWidget(self.local_html_view)
        self.local_tab.setLayout(self.local_layout)  # Imposta il layout del tab
        self.tabs.addTab(self.local_tab, "ViGeo")

        url = QUrl.fromLocalFile(os.path.abspath(os.path.join(os.path.dirname(__file__), "../ViGeo/index.html")))
        self.local_html_view.setUrl(url)
        
        # Collega il segnale di richiesta di download
        self.local_html_view.page().profile().downloadRequested.connect(handle_download)
