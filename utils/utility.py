from PyQt5.QtWidgets import QMessageBox

def show_alert(testo):
    """Mostra un messaggio di avviso."""
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setText(testo)
    msg.setWindowTitle("Avviso")
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec()
    