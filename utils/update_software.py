import requests
from tkinter import ttk, messagebox, Menu

def check_for_updates(CURRENT_VERSION, GITHUB_RELEASES_API_URL):
    
    message = "check update"
    try:
        response = requests.get(GITHUB_RELEASES_API_URL)
        response.raise_for_status()
        latest_release = response.json()
        latest_version = latest_release['tag_name']        
        if is_newer_version(latest_version, CURRENT_VERSION):
            download_url = latest_release['html_url']
            if messagebox.askyesno("Aggiornamento Disponibile", f"Disponibile una nuova versione ({latest_version}). Vuoi scaricarla?"):
                download_update(download_url)
        else:            
            #self.label.config(text="Nessun aggiornamento disponibile.")
            message = "Nessun aggiornamento disponibile."
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            message = "Nessuna release trovata sul repository GitHub."
            #self.label.config(text="Nessuna release trovata sul repository GitHub.")
        else:
            print("errore {http_err}")
            message = f"Errore HTTP durante il controllo degli aggiornamenti: {http_err}"
            #self.label.config(text=f"Errore HTTP durante il controllo degli aggiornamenti: {http_err}")
    except requests.RequestException as e:
        message = f"Errore durante il controllo degli aggiornamenti: {e}"
        #self.label.config(text=f"Errore durante il controllo degli aggiornamenti: {e}")
        
    return message

def is_newer_version(latest_version, current_version):
    latest_version_tuple = tuple(map(int, latest_version.strip('v').split('.')))
    current_version_tuple = tuple(map(int, current_version.strip('v').split('.')))
    return latest_version_tuple > current_version_tuple

def download_update(url):
    import webbrowser
    webbrowser.open(url)
        