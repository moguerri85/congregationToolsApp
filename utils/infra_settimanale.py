from bs4 import BeautifulSoup
from utils.utility import show_alert
from PyQt5.QtCore import QTimer


click_expand_js_infraSettimanale = """
    var expandElement = document.querySelector('svg.bi.bi-arrows-expand');
    if (expandElement) {
        // Trova il pulsante più vicino associato (usa .closest() se necessario)
        var button = expandElement.closest('button');
        if (button) {
            button.click();  // Simula il clic sul pulsante associato
        }
    }
    """

click_toggle_js_infraSettimanale = """
var toggleElement = document.querySelector('.bi.bi-toggle2-on');
if (toggleElement) {
    var navLink = toggleElement.closest('.nav-link');
    if (navLink) {
        navLink.click();
    }
}
"""

click_button_with_delay_js_infraSettimanale = """
var arrowButton = document.querySelector('.bi.bi-arrow-right-square');
if (arrowButton) {
    var clickableElement = arrowButton.closest('button, a');
    if (clickableElement) {
        clickableElement.click();
    } else {
        console.log("Nessun elemento cliccabile trovato vicino all'icona 'bi bi-arrow-right-square'.");
    }
} else {
    console.log("Elemento con classe 'bi bi-arrow-right-square' non trovato.");
}
"""

retrieve_content_js_infraSettimanale = """
function getContent() {
    return document.getElementById('mainContent').outerHTML;
}
getContent();
"""
            
def perform_click_infraSettimanale_tab(self):
    """Esegue il clic sul pulsante con la classe 'bi bi-arrow-right-square'."""
    self.view.page().runJavaScript(click_button_with_delay_js_infraSettimanale)

def retrieve_content_infraSettimanale_tab(self, index):
    """Recupera il contenuto dell'elemento mainContent e lo aggiunge all'array."""
    self.view.page().runJavaScript(retrieve_content_js_infraSettimanale, 
        lambda content: add_content_to_array_infraSettimanale_tab(self, content, index))
    
def add_content_to_array_infraSettimanale_tab(self, content, index):
    """Aggiunge il contenuto recuperato all'array e aggiorna la barra di progresso."""
    if content:
        self.content_array.append(content)

    # Calcola la percentuale di avanzamento
    progress = int(((index + 1) / self.num_clicks) * 100)
    self.progress_bar.setValue(progress)




def combine_html_infrasettimale(html):
    #soup = BeautifulSoup(html, 'html.parser')
            
    html_content = manipulateHTML_infrasettimanale(html)
    return html_content 

def manipulateHTML_infrasettimanale(html):
    parsed_html_list = []  # Lista per memorizzare gli HTML modificati
    
    for card_div_HTML in html:
        # Converte la stringa HTML in un oggetto BeautifulSoup
        soup = BeautifulSoup(card_div_HTML, 'html.parser')
        
        # Trova e rimuove i div con la classe specificata
        for divIntestazione1 in soup.find_all("div", class_="d-flex flex-row justify-content-between align-items-end mb-4"):
            divIntestazione1.extract()

        for divIntestazione2 in soup.find_all("div", class_="mt-4 d-flex align-items-end nav nav-tabs"):
            divIntestazione2.extract()
        
        for divIntestazione3 in soup.find_all("div", class_="d-flex justify-content-center mb-3 nav"):
            divIntestazione3.extract()

        for leggenda in soup.find_all("div", class_="mt-4 row"):
            leggenda.extract()

        for conferma in soup.find_all("div", class_="pb-2 d-flex flex-row align-items-center"):
            conferma.extract()    
        
        for svg in soup.find_all('svg'):
            svg.extract()    

        # Sostituisce il contenuto dei bottoni con il loro testo
        for buttonINF in soup.find_all('button'):
            buttonINF.replace_with(buttonINF.text)
        
        # Aggiungi l'HTML manipolato alla lista
        parsed_html_list.append(str(soup))
    
    # Unisce tutte le stringhe HTML modificate in un'unica stringa
    string_html_content = "\n".join(parsed_html_list)
        
    return string_html_content