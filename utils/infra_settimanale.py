from bs4 import BeautifulSoup

def combine_html_infrasettimale(html):
    soup = BeautifulSoup(html, 'html.parser')
         
    #Ogni 2 adunanze, partendo da quella infrasettimanale, suddivido la settimana con una linea
    html = soup.find_all("div", {"class": "card"})
    html = [v for i, v in enumerate(html) if i % 2 == 0]    
     
    for hrAppend in html:
        hrAppend.append(BeautifulSoup("<hr>",'html.parser'))
            
    html_content = manipulateHTML_infrasettimanale(html)
    return html_content 

def manipulateHTML_infrasettimanale(html):
    countProFs = 0 
    #inner_html = ""
    
    for html_manipulate in html: 
        for avvisiAVU in html_manipulate.find_all("svg"):
            avvisiAVU.extract()
            
        for grid in html_manipulate.find_all("div", class_="d-flex flex-column gap-2 card-body"):
            grid.append(BeautifulSoup("<div id='sezione1'></div>",'html.parser'))
            
            for week_grid in html_manipulate.find_all("div", class_="week-grid"):
                    inner_html = week_grid.encode_contents()
                    inner_soup = BeautifulSoup(inner_html, 'html.parser')
                    week_grid.extract()
                    
                    
            #append della data
            for sezione1 in html_manipulate.find_all("div", id="sezione1"):
                for inner in inner_soup.find_all("div", class_="calendar-day me-2 align-self-start card"): 
                    # Trova tutti i div con la classe specificata
                    divs = inner.find_all('div', class_='bg-secondary text-white text-center text-uppercase fw-bold py-1 px-4 card-header')
                    for single_div in divs:
                        single_div['class'] = 'bg-primary text-white text-center text-uppercase fw-bold py-1 px-4 card-header'
                    inner_calendar = str(divs)
                sezione1.append(BeautifulSoup(str(inner),'html.parser')) 
                sezione1.append(BeautifulSoup("<div id='partiAssegnazioni'>",'html.parser')) 
             
            
            for partiAssegnazioni in html_manipulate.find_all("div", id="partiAssegnazioni"):
                presidente_preghiera = inner_soup.find_all("div", class_="mm_part") 
                for pp in presidente_preghiera:
                    partiAssegnazioni.append(BeautifulSoup(str(pp),'html.parser'))   
            
        
            for buttonProInfra in html_manipulate.find_all('button'): #alcuni bottoni hanno i nominativi
                buttonProInfra.replace_with(buttonProInfra.text)
    
    string_html_content = "\n".join(str(x) for x in html)
        
    return string_html_content