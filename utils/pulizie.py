from bs4 import BeautifulSoup
from datetime import datetime


retrieve_content_js_pulizie = """
function getContent() {
    return document.getElementById('mainContent').innerHTML;
}
getContent();
"""

click_button_with_delay_js_pulizie = """
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

def retrieve_content_pulizie(self, index):
    """Recupera il contenuto dell'elemento mainContent e lo aggiunge all'array."""
    self.view.page().runJavaScript(retrieve_content_js_pulizie, 
        lambda content: add_content_to_array_pulizie(self, content, index))
    
def add_content_to_array_pulizie(self, content, index):
    """Aggiunge il contenuto recuperato all'array e aggiorna la barra di progresso."""
    if content:
        self.content_array.append(content)

    # Calcola la percentuale di avanzamento
    progress = int(((index + 1) / self.num_clicks) * 100)
    self.progress_bar.setValue(progress)
    if index < self.num_clicks:
        perform_click_pulizie(self)

def perform_click_pulizie(self):
    """Esegue il clic sul pulsante con la classe 'bi bi-arrow-right-square'."""
    self.view.page().runJavaScript(click_button_with_delay_js_pulizie)

def combine_html_pulizie( html):    
    html_content = manipulateHTML_pulizie(html)
    return html_content 

def manipulateHTML_pulizie(html):

    htmlAll = BeautifulSoup("", 'html.parser')

    # Iterate through the list of HTML strings
    for card_div_HTML in html:
        # Convert the HTML string into a BeautifulSoup object
        soup = BeautifulSoup(card_div_HTML, 'html.parser')

        # Trova e rimuove i div con la classe specificata
        for divIntestazione1 in soup.find_all("div", class_="d-flex flex-row justify-content-between align-items-end mb-4"):
            divIntestazione1.extract()

        for divIntestazione2 in soup.find_all("div", class_="mt-4 d-flex align-items-end nav nav-tabs"):
            divIntestazione2.extract()
        
        for divIntestazione3 in soup.find_all("div", class_="d-flex justify-content-between mb-5"):
            divIntestazione3.extract()

        for col1 in soup.find_all("div", class_='col-1'):
            col1.extract()

        for i_PUL in soup.find_all('i'):  # alcuni bottoni hanno i nominativi                
            i_PUL.extract()

        for ns in soup.find_all("div", class_="dropdown-bounded mt-1 dropdown"):
            if "Nessuna selezione" in ns.text:
                ns.extract()

        for buttonAVU in soup.find_all('button'):  # alcuni bottoni hanno i nominativi                
            buttonAVU.replace_with(buttonAVU.text)

        for leggenda in soup.find_all("div", class_="row row-cols-auto"):
            leggenda.extract()

        # Trova l'elemento contenente la classe 'date-picker-input'
        date_picker_row = soup.find('input', class_='date-picker-input')
        
        # Se l'elemento è stato trovato, rimuovi la riga che lo contiene
        if date_picker_row:
            # Trova il genitore fino alla riga (row) contenente il date picker
            row = date_picker_row.find_parent('div', class_='row')
            if row:
                row.decompose()  # Rimuove completamente l'elemento dal documento

        # Aggiungi un elemento <hr> a ogni div con la classe 'mb-4 align-items-center row'
        for row_div in soup.find_all("div", class_="mb-4 align-items-center row"):
            # Estrai la data dal div
            date_div = row_div.find("div", class_="text-center col-md-2 col-3")
            if date_div:
                try:
                    # Estrai e converti la data in formato datetime
                    date_text = date_div.get_text(strip=True)
                    date_obj = datetime.strptime(date_text, "%d/%m/%Y")
                    # Ottieni la settimana dell'anno
                    week_number = date_obj.isocalendar()[1]

                    # Alterna lo sfondo in base alla settimana (pari o dispari)
                    if week_number % 2 == 0:
                        background_gradient = "linear-gradient(to right, rgba(255, 215, 0, 0), rgba(255, 215, 0, 0.5), rgba(255, 215, 0, 0.2), rgba(255, 215, 0, 0))"
                    else:
                        background_gradient = "linear-gradient(to right, rgba(255, 255, 255, 0), rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0))"

                    # Applica lo stile al div della riga
                    row_div['style'] = f"background: {background_gradient}; margin-right: unset; margin-left: unset;"

                except ValueError:
                    pass  # Ignora se la data non è valida

            # Controlla se il terzo o quarto div contiene un dropdown valorizzato
            div_list = row_div.find_all("div", class_="text-center col-xl-3 col-lg-4 col-12")
            if len(div_list) >= 3:  # Verifica se ci sono abbastanza div
                for i in [1]:  
                    for dropdown_div in div_list[i].find_all("div", class_="dropdown-bounded mt-1 dropdown"):                    
                        if dropdown_div.text:
                            # Cambia il colore di sfondo
                            row_div['style'] = "background: linear-gradient(to right, rgba(255, 215, 0, 0), rgb(255 0 0 / 24%), rgba(255, 215, 0, 0));margin-right: unset;margin-left: unset;"  # Colore speciale 
                for i in [2]:  
                    for dropdown_div in div_list[i].find_all("div", class_="dropdown-bounded mt-1 dropdown"):                    
                        if dropdown_div.text:
                            # Cambia il colore di sfondo
                            row_div['style'] = "background: linear-gradient(to right, rgba(255, 215, 0, 0), rgba(255 0 0 / 10%), rgb(255 0 0 / 24%));margin-right: unset;margin-left: unset;"  # Colore speciale 

            #hr_tag = soup.new_tag("hr")
            #row_div.append(hr_tag)  # Aggiunge l'elemento <hr> alla fine del div

        # Extract the inner HTML content after removing unwanted elements
        current_inner_html = soup.decode_contents()

        # Append the processed content to htmlAll
        htmlAll.append(BeautifulSoup(f'<div class="flex-grow-1 mainContent"><div class="mb-3 card">{current_inner_html}</div></div>', 'html.parser'))

    # Trova tutti i div con la classe 'mb-3 card'
    cards = htmlAll.find_all('div', class_='flex-grow-1 mainContent')

    # Limita il numero di div in ogni lista a 3
    chunk_size = 3
    card_lists = [cards[i:i + chunk_size] for i in range(0, len(cards), chunk_size)]
    
    # Crea l'HTML per ciascuna lista di div
    html_results = []
    for card_list in card_lists:
        # Unisci i div in una stringa HTML
        joined_cards = ''.join(str(card) for card in card_list)
        # Incapsula in un contenitore
        intestazione = BeautifulSoup(
            '<div class="mb-4 align-items-center row mb-3">'
            '<div class="text-center col-md-2 col-3"></div>'
            '<div class="text-center col-xl-3 col-lg-4 col-12_30"><b>Pulizie Ordinarie</b></div>'
            '<div class="text-center col-xl-3 col-lg-4 col-12_30"><b>Pulizie Generali</b></div>'
            '<div class="text-center col-xl-3 col-lg-4 col-12_30"><b>Pulizie Generali + Lavatrice</b></div>'
            '</div>', 
            'html.parser'
        )
        html_content = f"<div class='page'>{str(intestazione)}{joined_cards}</div>"
        html_results.append(html_content)

    # Join all the HTML results as a single string
    string_html_content = "\n".join(html_results)
        
    return string_html_content
