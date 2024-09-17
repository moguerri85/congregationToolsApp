from bs4 import BeautifulSoup

retrieve_content_js_testimonianza_pubbl = """
function getContent() {
    return document.getElementById('mainContent').innerHTML;
}
getContent();
"""

click_button_with_delay_js_testimonianza_pubbl = """
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

click_toggle_js_testimonianza_pubbl = """
var div = document.querySelector('div.d-flex.mt-1.align-items-center.gap-2');
if (div) {
    var buttons = div.querySelectorAll('button');
    if (buttons.length >= 3) {
        buttons[2].click();  // Indice 2 corrisponde al terzo pulsante
    }
}
"""

def retrieve_content_testimonianza_pubbl(self, index):
    """Recupera il contenuto dell'elemento mainContent e lo aggiunge all'array."""
    self.view.page().runJavaScript(retrieve_content_js_testimonianza_pubbl, 
        lambda content: add_content_to_array_testimonianza_pubbl(self, content, index))
    
def add_content_to_array_testimonianza_pubbl(self, content, index):
    """Aggiunge il contenuto recuperato all'array e aggiorna la barra di progresso."""
    if content:
        self.content_array.append(content)

    # Calcola la percentuale di avanzamento
    progress = int(((index + 1) / self.num_clicks) * 100)
    self.progress_bar.setValue(progress)
    if index < self.num_clicks:
        perform_click_testimonianza_pubbl(self)

def perform_click_testimonianza_pubbl(self):
    """Esegue il clic sul pulsante con la classe 'bi bi-arrow-right-square'."""
    self.view.page().runJavaScript(click_button_with_delay_js_testimonianza_pubbl)

def combine_html_testimonianza_pubbl(html):    
    html_content = manipulateHTML_testimonianza_pubbl(html)
    return html_content 

def manipulateHTML_testimonianza_pubbl(html):

    htmlAll = BeautifulSoup("", 'html.parser')

    parsed_html_list = []  # Lista per memorizzare gli HTML modificati
    
    for card_div_HTML in html:
        # Converte la stringa HTML in un oggetto BeautifulSoup
        soup = BeautifulSoup(card_div_HTML, 'html.parser')
        
        # Trova e rimuove i div con la classe specificata
        for divIntestazione1 in soup.find_all("div", class_="d-flex flex-row justify-content-between align-items-end mb-4"):
            divIntestazione1.extract()

        for divIntestazione2 in soup.find_all("div", class_="mt-4 d-flex align-items-end nav nav-tabs"):
            divIntestazione2.extract()

        for divIntestazione3 in soup.find_all("div", class_="mt-4 nav nav-tabs"):
            divIntestazione3.extract()

        for divIntestazione4 in soup.find_all("div", class_="mt-2 d-flex justify-content-center"):
            divIntestazione4.extract()

        for divIntestazione5 in soup.find_all("div", class_="d-flex mt-1 align-items-center gap-2"):
            divIntestazione5.extract()

        for leggenda in soup.find_all("div", class_="row row-cols-auto"):
            leggenda.extract()
        
        for svg in soup.find_all('svg'):
            svg.extract()    
        
        for button in soup.find_all('button'):  # alcuni bottoni hanno i nominativi                
            button.replace_with(button.text)

        # Rimuove l'attributo style dalla tabella con classe pw-table
        for table in soup.find_all('table', class_='pw-table'):
            if table.has_attr('style'):
                del table['style']

            # Modifica la larghezza delle colonne
            thead = table.find('thead')
            if thead:
                ths = thead.find_all('th')
                if ths:
                    ths[0]['class'] = ths[0].get('class', []) + ['colonna_data']
                    del ths[0]['style']
                    # Imposta la larghezza dei restanti <th>
                    for th in ths[1:]:
                        th['class'] = th.get('class', []) + ['colonna_postazione']
                        del th['style']

            # Modifica le classi dei <td> nel <tbody>
            tbody = table.find('tbody')
            if tbody:
                for tr in tbody.find_all('tr'):
                    tds = tr.find_all('td')
                    if tds:
                        # Aggiungi la classe colonna_data al primo <td>
                        tds[0]['class'] = 'colonna_data'
                        # Aggiungi la classe colonna_postazione ai restanti <td>
                        for td in tds[1:]:
                            td['class'] = 'colonna_postazione'


        htmlAll.append(BeautifulSoup(f'{soup}', 'html.parser'))


    # Trova tutti i div con lo stile overflow-x: auto
    cards = htmlAll.find_all('div', style='overflow-x: auto;')
    for card in cards:
        card['class'] = 'row'

    # Limita il numero di div in ogni lista a 3
    chunk_size = 5
    card_lists = [cards[i:i + chunk_size] for i in range(0, len(cards), chunk_size)]

    # Crea l'HTML per ciascuna lista di div
    html_results = []
    for card_list in card_lists:
        # Unisci i div in una stringa HTML
        joined_cards = ''.join(str(card) for card in card_list)
        html_content = f"<div class='page'><div class='flex-grow-1 mainContent'><div class='mb-3 card'>{joined_cards}</div></div></div>"
        html_results.append(html_content)


    # Join all the HTML results as a single string
    string_html_content = "\n".join(html_results)
        
    return string_html_content

