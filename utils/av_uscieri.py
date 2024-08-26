from bs4 import BeautifulSoup



click_button_with_delay_js_av_uscieri = """
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

retrieve_content_js_av_uscieri = """
function getContent() {
    return document.getElementById('mainContent').innerHTML;
}
getContent();
"""
            
def perform_click_av_uscieri(self):
    """Esegue il clic sul pulsante con la classe 'bi bi-arrow-right-square'."""
    self.view.page().runJavaScript(click_button_with_delay_js_av_uscieri)

def retrieve_content_av_uscieri(self, index):
    """Recupera il contenuto dell'elemento mainContent e lo aggiunge all'array."""
    self.view.page().runJavaScript(retrieve_content_js_av_uscieri, 
        lambda content: add_content_to_array_av_uscieri(self, content, index))
    
def add_content_to_array_av_uscieri(self, content, index):
    """Aggiunge il contenuto recuperato all'array e aggiorna la barra di progresso."""
    if content:
        self.content_array.append(content)

    # Calcola la percentuale di avanzamento
    progress = int(((index + 1) / self.num_clicks) * 100)
    self.progress_bar.setValue(progress)
    if index < self.num_clicks:
        perform_click_av_uscieri(self)


def combine_html_av_uscieri( html):    
    html_content = manipulateHTML_av_uscieri(html)
    return html_content 

def manipulateHTML_av_uscieri(html):
    
    for card_div_HTML in html:
        # Converte la stringa HTML in un oggetto BeautifulSoup
        soup = BeautifulSoup(card_div_HTML, 'html.parser')

        # Trova e rimuove i div con la classe specificata
        for divIntestazione1 in soup.find_all("div", class_="d-flex flex-row justify-content-between align-items-end mb-4"):
            divIntestazione1.extract()

        for divIntestazione2 in soup.find_all("div", class_="mt-4 d-flex align-items-end nav nav-tabs"):
            divIntestazione2.extract()
        
        for divIntestazione3 in soup.find_all("div", class_="d-flex justify-content-between my-1 mb-3"):
            divIntestazione3.extract()

        for sezCongressoAssemblea in soup.find_all("div", class_="d-flex flex-column flex-grow-1"):
            for titleSpecial in sezCongressoAssemblea.find_all("h4", class_="fw-bold"):
                if "Adunanza del fine settimana" in titleSpecial.text:                
                    titleSpecial.extract()
                elif "Adunanza infrasettimanale" in titleSpecial.text:                
                    titleSpecial.extract()
                elif "Congresso di zona" in titleSpecial.text:
                        for sezElimina in sezCongressoAssemblea.find_all("div", class_="d-flex flex-wrap mt-2"):
                            sezElimina.extract()
                elif "Assemblea di circoscrizione" in titleSpecial.text:
                        for sezElimina in sezCongressoAssemblea.find_all("div", class_="d-flex flex-wrap mt-2"):
                            sezElimina.extract()
                else:
                    titleSpecial.append(BeautifulSoup("", 'html.parser'))

        for avvisiAVU in soup.find_all("span", class_='me-1'):
            avvisiAVU.extract()

        for buttonAVU in soup.find_all('button'): #alcuni bottoni hanno i nominativi                
            buttonAVU.replace_with(buttonAVU.text) 

        for leggenda in soup.find_all("div", class_="row row-cols-auto"):
            leggenda.extract()


        # Trova l'elemento <div> con la classe 'bg-secondary'
        div = soup.find('div', class_='bg-secondary')

        # Sostituisci la classe 'bg-secondary' con 'bg-primary'
        if div:
            div['class'] = [cls.replace('bg-secondary', 'bg-primary') for cls in div['class']]


        # Trova tutti i div con la classe 'mb-3 card'
        cards = soup.find_all('div', class_='mb-3 card')

        # Limita il numero di div in ogni lista a 5
        chunk_size = 5
        card_lists = [cards[i:i + chunk_size] for i in range(0, len(cards), chunk_size)]
        # Crea l'HTML per ciascuna lista di div
        html_results = []
        for card_list in card_lists:
            # Unisci i div in una stringa HTML
            joined_cards = ''.join(str(card) for card in card_list)
            # Incapsula in un contenitore
            html_content = f"<div class='flex-grow-1 mainContent'>{joined_cards}</div>"
            html_results.append(html_content)







    string_html_content = "\n".join(html_results)
        
    return string_html_content