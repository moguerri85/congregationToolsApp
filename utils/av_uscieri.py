from bs4 import BeautifulSoup

def combine_html_av_uscieri(html):
    soup = BeautifulSoup(html, 'html.parser')
    html = soup.find_all("div", {"class": "mb-3 card"})

    # Ogni 2 adunanze, partendo da quella infrasettimanale, suddivido la settimana con una linea
    countSpecial = 1
    for divAppend in html:
        for titleSpecial in divAppend.find_all("h4", class_="fw-bold"):
            if "Adunanza del fine settimana" in titleSpecial.text:
                divAppend.append(BeautifulSoup("<hr>", 'html.parser'))
            if "Congresso di zona" in titleSpecial.text:
                if countSpecial % 2 == 0:
                    divAppend.append(BeautifulSoup("<hr>", 'html.parser'))
                else:
                    countSpecial += 1
            if "Assemblea di circoscrizione" in titleSpecial.text:
                if countSpecial % 2 == 0:
                    divAppend.append(BeautifulSoup("<hr>", 'html.parser'))
                else:
                    countSpecial += 1

    html_content = manipulateHTML_av_uscieri(html)
    return html_content

def manipulateHTML_av_uscieri(html):
    countProFs = 0  
        
    for htmlAVU in html:
        for avvisiAVU in htmlAVU.find_all("span", class_='me-1'):
            avvisiAVU.extract()
                    
        for buttonAVU in htmlAVU.find_all('button'): #alcuni bottoni hanno i nominativi                
            buttonAVU.replace_with(buttonAVU.text) 
            
            
        for title in htmlAVU.find_all("h4", class_="fw-bold"):
            for content in htmlAVU.find_all("div", class_="d-flex flex-column flex-grow-1"):
                if "Congresso di zona" in title.text:    
                    content.replace_with(BeautifulSoup("<div class='special d-flex'><h3 class='fw-bolder'>"+title.text+"</h3></div>",'html.parser'))
                elif "Assemblea di circoscrizione" in title.text:
                    content.replace_with(BeautifulSoup("<div class='special d-flex'><h3 class='fw-bolder'>"+title.text+"</h3></div>",'html.parser'))
            title.extract()
            
        for row in htmlAVU.find_all("div", class_="col-12 col-sm-6 col-lg-3 text-center"):
            for b_title in row.find_all('b'):
                if "Consolle A/V" in b_title.text: 
                    row.append(BeautifulSoup('<div class="rowIncarichi"><b>Audio:</b> '+str(row.find_all("div", class_="dropdown-bounded dropdown")[0])+'</div>','html.parser'))
                    row.append(BeautifulSoup('<div class="rowIncarichi"><b>Video:</b> '+str(row.find_all("div", class_="dropdown-bounded dropdown")[1])+'</div>','html.parser'))
                if "Podio" in b_title.text: 
                    row.append(BeautifulSoup('<div class="rowIncarichi">'+str(row.find_all("div", class_="dropdown-bounded dropdown")[0])+'</div>','html.parser'))
                if "Microfoni" in b_title.text: 
                    row.append(BeautifulSoup('<div class="rowIncarichi"><b>Blu:</b> '+str(row.find_all("div", class_="dropdown-bounded dropdown")[0])+'</div>','html.parser'))    
                    row.append(BeautifulSoup('<div class="rowIncarichi"><b>Rosso:</b> '+str(row.find_all("div", class_="dropdown-bounded dropdown")[1])+'</div>','html.parser'))    
                if "Usciere" in b_title.text: 
                    row.append(BeautifulSoup('<div class="rowIncarichi"><b>Auditorium:</b> '+str(row.find_all("div", class_="dropdown-bounded dropdown")[0])+'</div>','html.parser'))    
                    row.append(BeautifulSoup('<div class="rowIncarichi"><b>Ingresso:</b> '+str(row.find_all("div", class_="dropdown-bounded dropdown")[1])+'</div>','html.parser'))       
            row.find("div", class_="d-flex flex-column gap-1 pe-1 pb-3").extract()
                

        # Trova tutti i div con la classe specificata
        divs = htmlAVU.find_all('div', class_='col-12 col-sm-6 col-lg-3 text-center')

        # Modifica il secondo div trovato
        if len(divs) >= 2:
            second_div = divs[1]
            second_div['class'] = 'col-10 col-sm-6 col-lg-3 text-center'  # Sostituisci con la classe che desideri
    
    string_html_content = "\n".join(str(x) for x in html)
        
    return string_html_content