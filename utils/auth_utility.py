import requests
import base64
import hashlib
import pickle
import os

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
        print(f"Errore durante lo scambio del codice di autorizzazione: {e}")
        if e.response is not None:
            print(f"Risposta dell'errore: {e.response.text}")
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
            print(f"Nuovo Access Token: {tokens}")
    
        return tokens.get("access_token")
    except requests.exceptions.RequestException as e:
        print("Il refresh token non ha funzionato.")
        print(f"Errore durante il refresh del token di accesso: {e}")
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
            print("Errore 401: Access token non valido o scaduto.")
            # Prova a rinnovare il token
            new_access_token = self.refresh_access_token("4purifuc7efvwld", self.refresh_token)
            if new_access_token:
                self.access_token = new_access_token
                self.save_tokens(new_access_token, self.refresh_token)
                return self.get_user_info(new_access_token)  # Riprova con il nuovo 
            else:
                print(f"Errore HTTP 2 : {e}")        
        print(f"Errore HTTP: {e}")
        return "", ""
