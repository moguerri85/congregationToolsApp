from bs4 import BeautifulSoup

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
            
def perform_click_infraSettimanale(self):
    """Esegue il clic sul pulsante con la classe 'bi bi-arrow-right-square'."""
    self.view.page().runJavaScript(click_button_with_delay_js_infraSettimanale)

def retrieve_content_infraSettimanale(self, index):
    """Recupera il contenuto dell'elemento mainContent e lo aggiunge all'array."""
    self.view.page().runJavaScript(retrieve_content_js_infraSettimanale, 
        lambda content: add_content_to_array_infraSettimanale(self, content, index))
    
def add_content_to_array_infraSettimanale(self, content, index):
    """Aggiunge il contenuto recuperato all'array e aggiorna la barra di progresso."""
    if content:
        self.content_array.append(content)

    # Calcola la percentuale di avanzamento
    progress = int(((index + 1) / self.num_clicks) * 100)
    self.progress_bar.setValue(progress)
    if index < self.num_clicks:
        perform_click_infraSettimanale(self)

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

                    
        for div1 in soup.find_all('div', class_='core_row mm_part'):
            for divPreghiera in div1.find_all('p', class_='fw-bold mb-1 text-muted'):
                if "Preghiera" in divPreghiera.text:    
                    # Aggiungi la classe 'flex-row'
                    if divPreghiera:
                        divPreghiera['class'].append('flex-row')

                for divPresidente in div1.find_all('p', class_='fw-bold mb-1 text-muted'):
                    if "Presidente" in divPresidente.text:    
                        # Aggiungi la classe 'flex-row'
                        if divPresidente:
                            divPresidente['class'].append('flex-row')
                            
                # Trova il <div> senza classi e rimuovilo
                for child_div in div1.find_all('div'):
                    # Se il figlio <div> non ha attributo 'class', rimuovilo
                    if 'class' not in child_div.attrs:
                        child_div.unwrap()
                    for div2 in div1.find_all('div', class_='col'):
                        div2.unwrap()
                    for div2 in div1.find_all('div', class_='classrooms-group'):
                        div2.unwrap()

        for div3 in soup.find_all('div', class_='lac_row mm_part'):
            for divLettore in div3.find_all('p', class_='fw-bold mb-1 text-muted'):
                if "Lettore" in divLettore.text:    
                    # Aggiungi la classe 'flex-row'
                    if divLettore:
                        divLettore['class'].append('flex-row')
                    
                # Trova il <div> senza classi e rimuovilo
                for child_div in div3.find_all('div'):
                    # Se il figlio <div> non ha attributo 'class', rimuovilo
                    if 'class' not in child_div.attrs:
                        child_div.unwrap()

            for divDiscPreregistrato in div3.find_all("h4", class_="mt-1"):
                divDiscPreregistrato.name = "h6"  # converto h4 in h6 dei discorsi

        for div_format_fm_row in soup.find_all('div', class_='fm_row mm_part'):
            for span_fm_row in div_format_fm_row.find_all('span'):
                # Modifica il testo all'interno dello span e aggiungilo come nuovi <div>
                parts = format_text(span_fm_row.string)
                span_fm_row.clear()  # Pulisce il contenuto esistente
                for part in parts:
                    new_div = BeautifulSoup(f'<div><i>{part}</i></div>', 'html.parser')
                    span_fm_row.append(new_div)

        # Sostituisce il contenuto dei bottoni con il loro testo
        for buttonINF in soup.find_all('button'):
            buttonINF.replace_with(buttonINF.text)
        
        # Trova l'elemento <div> con la classe 'bg-secondary'
        div = soup.find('div', class_='bg-secondary')

        # Sostituisci la classe 'bg-secondary' con 'bg-primary'
        if div:
            div['class'] = [cls.replace('bg-secondary', 'bg-primary') for cls in div['class']]

        # Trova l'elemento <div> con l'id 'mainContent'
        div = soup.find('div', id='mainContent')

        # Converti l'id in una classe
        if div:
            # Aggiungi la classe 'mainContent'
            div['class'].append('mainContent')
            # Rimuovi l'id
            del div['id']

        # Aggiungi l'HTML manipolato alla lista
        parsed_html_list.append(str(soup))

    # Unisce tutte le stringhe HTML modificate in un'unica stringa
    string_html_content = "\n".join(parsed_html_list)
        
    return string_html_content

def format_text(text):
    if text:
        # Rimuove le virgolette e divide il testo dopo il primo punto
        text = text.replace('"', '')  # Rimuove le virgolette
        parts = text.split('.', 1)    # Divide il testo dopo il primo punto
        # Aggiunge un ritorno a capo dopo il primo punto
        if len(parts) > 1:
            parts[0] += '.'  # Ripristina il punto nel primo pezzo
            parts[1] = parts[1].strip()  # Rimuove spazi inutili
        return parts
