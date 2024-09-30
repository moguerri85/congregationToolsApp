import os
import logging

def logging_custom(self, tipo, message):
    # Ottieni il percorso della directory AppData specifica per l'applicazione
    appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp')

    # Verifica se la directory esiste, altrimenti creala
    if not os.path.exists(appdata_path):
        os.makedirs(appdata_path)

    # Configura il file di log all'interno della directory specifica
    log_file = os.path.join(appdata_path, 'app.log')

    # Configura il logger solo se non è già configurato
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

    if tipo == "debug":
        logging.debug(message)
    elif tipo == "info":    
        logging.info(message)
    elif tipo == "warning":    
        logging.warning(message)
    elif tipo == "error":    
        logging.error(message)
    elif tipo == "critical":        
        logging.critical(message)
