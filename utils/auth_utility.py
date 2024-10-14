import requests
import base64
import hashlib
import pickle
import os
import dropbox
import json

from PyQt5.QtWidgets import (QMessageBox)

from utils.logging_custom import logging_custom

# Funzioni per PKCE
def generate_code_verifier(self):
    return base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')

def generate_code_challenge(self, code_verifier):
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode('utf-8').rstrip('=')
    return code_challenge

def save_tokens(self, access_token, refresh_token):
    appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp')
    local_file_pkl= appdata_path+'/tokens.pkl'
    with open(local_file_pkl, "wb") as f:
        pickle.dump((access_token, refresh_token), f)

def load_tokens(self):
    appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp')
    local_file_pkl= appdata_path+'/tokens.pkl'
    try:
        with open(local_file_pkl, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None, None

# Funzioni per l'autenticazione con Dropbox
def initiate_authentication(self, client_id, code_challenge):
    redirect_uri = "http://localhost:5000/callback"
    auth_url = (
        f"https://www.dropbox.com/oauth2/authorize?client_id={client_id}&response_type=code&"
        f"redirect_uri={redirect_uri}&code_challenge={code_challenge}&"
        f"scope=account_info.read+files.metadata.write+files.metadata.read+files.content.write+files.content.read+sharing.write+sharing.read&"
        f"code_challenge_method=S256&token_access_type=offline"
    )
    return auth_url

def exchange_code_for_tokens(self, client_id, code_verifier, code, redirect_uri):
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": client_id,
        "code_verifier": code_verifier,
        "redirect_uri": redirect_uri
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        tokens = response.json()
        return tokens.get("access_token"), tokens.get("refresh_token")
    except requests.exceptions.RequestException as e:
        logging_custom(self, "error", f"Errore durante lo scambio del codice di autorizzazione: {e}")
        if e.response is not None:
            logging_custom(self, "error", f"Risposta dell'errore: {e.response.text}")
        return None, None

def refresh_access_token(self, client_id, refresh_token):
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": refresh_token
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        tokens = response.json()
        if tokens:
            logging_custom(self, "debug", f"Nuovo Access Token: {tokens}")
    
        return tokens.get("access_token")
    except requests.exceptions.RequestException as e:
        logging_custom(self, "error", "Il refresh token non ha funzionato.")
        logging_custom(self, "error", f"Errore durante il refresh del token di accesso: {e}")
        return None

# Funzione per ottenere informazioni dell'account dell'utente
def get_user_info(self, access_token):
    url = "https://api.dropboxapi.com/2/users/get_current_account"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        user_info = response.json()
        given_name = user_info.get("name", {}).get("given_name", "")
        surname = user_info.get("name", {}).get("surname", "")
        return given_name, surname

    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            logging_custom(self, "error", "Errore 401: Access token non valido o scaduto.")
            # Prova a rinnovare il token
            new_access_token = refresh_access_token(self, "4purifuc7efvwld", self.refresh_token)
            if new_access_token:
                self.access_token = new_access_token
                save_tokens(self, new_access_token, self.refresh_token)
                return get_user_info(self, new_access_token)  # Riprova con il nuovo 
            else:
                logging_custom(self, "error", f"Errore HTTP 2 : {e}")        
        logging_custom(self, "error", f"Errore HTTP: {e}")
        return "", ""

def save_to_dropbox(self, local_file_path, SAVE_FILE):
    self.access_token, self.refresh_token = load_tokens(self)
    self.logged_in = self.access_token is not None

    if self.logged_in:
        dbx = dropbox.Dropbox(self.access_token)
        dropbox_file_path = f"/{SAVE_FILE}"

        logging_custom(self, "debug", f"Controllo esistenza file: {dropbox_file_path}")

        # Prova a caricare il file locale
        try:
            with open(local_file_path, "rb") as f:
                dbx.files_upload(f.read(), dropbox_file_path, mode=dropbox.files.WriteMode.overwrite)
            logging_custom(self, "debug", "File caricato su Dropbox.")
        except dropbox.exceptions.ApiError as err:
            if isinstance(err.error, dropbox.files.LookupError) and err.get_path().is_not_found():
                logging_custom(self, "debug", "Il file non esiste. Creazione di un file vuoto.")
                # Crea un file vuoto se non esiste
                try:
                    dbx.files_upload(b"", dropbox_file_path)  # Carica un file vuoto
                    logging_custom(self, "debug", "File vuoto creato su Dropbox.")
                    
                    # Riprova a caricare il file locale
                    with open(local_file_path, "rb") as f:
                        dbx.files_upload(f.read(), dropbox_file_path, mode=dropbox.files.WriteMode.overwrite)
                    logging_custom(self, "debug", "File caricato su Dropbox.")
                except dropbox.exceptions.ApiError as e:
                    logging_custom(self, "error", f"Errore nella creazione del file vuoto: {e}")
            else:
                logging_custom(self, "error", f"Errore imprevisto: {err}")
    else:
        logging_custom(self, "error", "Accesso a Dropbox non riuscito. Verifica i token.")

def file_exists(self, dbx, dropbox_file_path):
    try:
        dbx.files_get_metadata(dropbox_file_path)
        return True
    except dropbox.exceptions.ApiError as err:
        if isinstance(err.error, dropbox.files.LookupError) and err.get_path().is_not_found():
            return False
        logging_custom(self, "error", f"Errore imprevisto durante il controllo dell'esistenza del file: {err}")
        raise 

def load_espositore_data_from_dropbox(app):
    from espositore.espositore_utils import load_data

    """Load data from the espositore_data.json file on Dropbox and save it locally."""
    try:
        app.access_token, app.refresh_token = load_tokens(app)
        app.logged_in = app.access_token is not None

        if app.logged_in:
            # Your Dropbox access token
            dbx = dropbox.Dropbox(app.access_token)

            # Path to the file in Dropbox
            dropbox_file_path = '/espositore_data.json'

            # Download the file from Dropbox
            metadata, res = dbx.files_download(dropbox_file_path)
            data = json.loads(res.content.decode('utf-8'))

            # Save the downloaded data locally
            appdata_path = os.path.join(os.getenv('APPDATA'), 'CongregationToolsApp')
            local_file_path = os.path.join(appdata_path, 'espositore_data.json')

            # Ensure the directory exists
            os.makedirs(appdata_path, exist_ok=True)

            with open(local_file_path, 'w', encoding='utf-8') as local_file:
                json.dump(data, local_file, ensure_ascii=False, indent=4)

            # Populate the application data
            app.people = data.get('people', {})
            app.person_schedule = data.get('person_schedule', {})
            app.tipo_luogo_schedule = data.get('tipo_luogo_schedule', {})
            
            app.tipologie = data.get('tipologie', {})
            app.last_import_hourglass = data.get('last_import_hourglass', {})
            app.autocomplete_gender_sino = data.get('autocomplete_gender_sino', {})

            # Update the UI with the loaded data
            load_data(app)
            logging_custom(app, "debug", "Dati espositore caricati con successo da Dropbox e salvati localmente!")

    except dropbox.exceptions.HttpError as e:
        QMessageBox.critical(app, "Errore", f"Errore nel caricamento dei dati da Dropbox: {str(e)}")
    except Exception as e:
        QMessageBox.critical(app, "Errore", f"Si è verificato un errore durante il caricamento dei dati da Dropbox: {str(e)}")