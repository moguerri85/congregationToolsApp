from bs4 import BeautifulSoup

def combine_html_pulizie(html):
    soup = BeautifulSoup(html, 'html.parser')
    html = soup.find_all("div", {"class": "mb-4 align-items-center row"})

    html_content = manipulateHTML_pulizie(html)
    return html_content

def manipulateHTML_pulizie(html):

    htmlAll = BeautifulSoup("", 'html.parser')

    intestazione = (BeautifulSoup('<div class="mb-4 align-items-center row contentRow"><div class="text-center col-md-2 col-3 altezzaRigaPUL"></div><div class="text-center col-xl-3 col-lg-4 col-12"><b>Pulizie Ordinarie</b></div><div class="text-center col-xl-3 col-lg-4 col-12"><b>Pulizie Generali</b></div><div class="text-center col-xl-3 col-lg-4 col-12"><b>Pulizie Generali + Lavatrice</b></div></div>','html.parser'))    
    
    htmlAll.append(intestazione)

    current_inner_html = ""
    for divRiga in html:
        for col1 in divRiga.find_all("div", class_='col-1'):
            col1.extract()
        current_inner_html = divRiga.decode_contents()
        divRiga.extract()
        htmlAll.append(BeautifulSoup('<div class="contentRow">'+current_inner_html+'</div><hr>', 'html.parser'))    
        

    for htmlPUL in htmlAll:
        for avvisiPUL in htmlPUL.find_all("span", class_='me-1'):
            avvisiPUL.extract()
        
        for calendarPUL in htmlPUL.find_all("input", class_='date-picker-input'):
            htmlPUL.extract()

        for buttonPUL in htmlPUL.find_all('button'): #alcuni bottoni hanno i nominativi                
            buttonPUL.replace_with(buttonPUL.text) 

        for i_PUL in htmlPUL.find_all('i'): #alcuni bottoni hanno i nominativi                
            i_PUL.extract()       

        for value in htmlPUL.find_all("div", class_="dropdown-bounded mt-1 dropdown"):
            #dropdown-bounded mt-1 dropdown
            if "Nessuna selezione" in value.text:  
                value.extract()
        
        # Trova l'elemento <div> con l'id 'mainContent'
        div = htmlAll.find('div', id='mainContent')

        # Converti l'id in una classe
        if div:
            # Aggiungi la classe 'mainContent'
            div['class'].append('mainContent')
            # Rimuovi l'id
            del div['id']
    
    string_html_content = "\n".join(str(x) for x in htmlAll)
        
    return string_html_content