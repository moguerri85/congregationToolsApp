document.addEventListener('DOMContentLoaded', () => {
    const fileInputConfini = document.getElementById('fileInputConfini');
    const fileInputDB = document.getElementById('fileInputDB');
    const saveButton = document.getElementById('saveButton');
    const exportExcelButton = document.getElementById('exportExcelButton');
    const componentiList = document.getElementById('componentiList');
    const gruppiServizioList = document.getElementById('gruppiServizioList');
    const componenteForm = document.getElementById('componenteForm');
    const gruppiServizioForm = document.getElementById('gruppiServizioForm');
    const ragruppamentiGruppiList = document.getElementById('ragruppamentiGruppi');
    const drawPolygonBtn = document.getElementById('drawPolygonBtn');
    const getPolygonBtn = document.getElementById('getCoordinatesBtn');
    const toggleRemove = document.getElementById('toggleRemove');

    const hide = document.getElementById('hide');
    const show = document.getElementById('show');
    const map = L.map('map').setView([41.8719, 12.5674], 6); // Centro Italia
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        //attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    let componente = [];
    let jsonTemp = [];
    let gruppiServizio = [{ "id": 1, "name": "ND", "color": "0" }];
    let comboGruppiServizioHTML = "";


    let comboColorGruppiServizio = [{ "id": "0", "nome": "Nero", "color": "Black" }, { "id": "1", "nome": "Blu", "color": "Navy" }, { "id": "2", "nome": "Rosso", "color": "Red" }, { "id": "3", "nome": "Giallo", "color": "Yellow" }, { "id": "4", "nome": "Verde", "color": "Green" }, { "id": "5", "nome": "Marrone", "color": "Brown" }, { "id": "6", "nome": "arancio", "color": "orange" }, { "id": "7", "nome": "Viola", "color": "Purple" }, { "id": "8", "nome": "Rosa", "color": "Pink" }, { "id": "8", "nome": "Grigio", "color": "Grey" }]
    let comboColorGruppiServizioHTML = "";

    let confineCongregazione = [];

    renderGruppiServizio();
    
    drawPolygonBtn.addEventListener('click', handleDraw);
    getPolygonBtn.addEventListener('click', handleGetCoordinateRitrovo);
    toggleRemove.addEventListener('click', handleRemoveRitrovo);

    fileInputConfini.addEventListener('change', handleFileSelectConfini);
    fileInputDB.addEventListener('change', handleFileSelectDB);
    hide.addEventListener('click', handleHide);
    show.addEventListener('click', handleShow);
    aggiungiComponente.addEventListener('click', handleAddComponente);
    modificaComponente.addEventListener('click', handleModifyComponente);
    eliminaComponente.addEventListener('click', handleDeleteComponente);
    aggiungiGruppiServizio.addEventListener('click', handleAddGruppiServizio);
    modificaGruppiServizio.addEventListener('click', handleModifyGruppiServizio);
    eliminaGruppiServizio.addEventListener('click', handleDeleteGruppiServizio);
    addGruppiServizioButton.addEventListener('click', addGruppiServizio);
    addComponeteButton.addEventListener('click', addComponete);

    saveButton.addEventListener('click', saveFile);
    exportExcelButton.addEventListener('click', () => exportExcel(jsonTemp));

    document.getElementById("defaultOpen").click();

    comboColorGruppiServizioHTML = "<option value='1'>blu</option>"
    comboColorGruppiServizioHTML += "<option value='2'>rosso</option>"
    comboColorGruppiServizioHTML += "<option value='3'>giallo</option>"
    comboColorGruppiServizioHTML += "<option value='4'>verde</option>"
    comboColorGruppiServizioHTML += "<option value='5'>oro</option>"
    comboColorGruppiServizioHTML += "<option value='6'>arancio</option>"
    comboColorGruppiServizioHTML += "<option value='7'>viola</option>"

    document.getElementById("colorGruppiServizio").innerHTML = comboColorGruppiServizioHTML;

    function clearFileInput(idInput) {
        try {
            document.getElementById(idInput).value = null;
        } catch(ex) { }
        if (document.getElementById(idInput).value) {
            document.getElementById(idInput).parentNode.replaceChild(document.getElementById(idInput).cloneNode(true), document.getElementById(idInput));
        }
      }

    let drawingEnabled = false;
    let removeEnabled = false;
    let currentPolygon = [];
    let puntiRitrovo = [];  // Array per i multipoligoni

    function handleDraw(event) {
        drawingEnabled = !drawingEnabled;
        this.textContent = drawingEnabled ? "Disabilita disegno Punto di Ritrovo" : "Abilita disegno Punto di Ritrovo";
    }

    function handleRemoveRitrovo(event) {
        for(i in map._layers) {
            if(map._layers[i]._path != undefined) {
                try {                        
                    map.removeLayer(map._layers[i]);
                    puntiRitrovo = [];
                    confineCongregazione = [];
                }
                catch(e) {
                    console.log("problem with " + e + map._layers[i]);
                }
            }
        }

    }    

    // Gestisci il click sulla mappa per disegnare il poligono
    map.on('click', function(e) {
        if (drawingEnabled) {
            let latlng = e.latlng;
            currentPolygon.push([latlng.lat, latlng.lng]);

            if (currentPolygon.length > 2) {
                L.polygon(currentPolygon, { color: 'red' }).addTo(map);              
            }
        }
    });

    // Salva il poligono corrente come un multipoligono e resetta per il prossimo poligono
    // Recupera le coordinate di tutti i poligoni disegnati
    function handleGetCoordinateRitrovo(event) {
        if (drawingEnabled && currentPolygon.length > 2) {
            puntiRitrovo.push(currentPolygon);
            currentPolygon = [];  // Resetta per iniziare un nuovo poligono
        }
        
        if (puntiRitrovo.length > 0) {
            puntiRitrovo.forEach((polygon, index) => {                
                L.polygon([polygon],
                        {
                            color: 'red',
                            fillColor: 'red',
                            fillOpacity: 0.1
                        }).addTo(map);
            });
        } 
    }

    function handleFileSelectConfini(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                const kmlText = event.target.result;
                const parser = new DOMParser();
                const xmlDoc = parser.parseFromString(kmlText, "application/xml");
                const coordinatesElementsPoligono = xmlDoc.getElementsByTagName('coordinates');
    
                if (coordinatesElementsPoligono.length > 0) {
                    const coordinatesText = coordinatesElementsPoligono[0].textContent.trim();
                    const coordinates = coordinatesText.split(/\s+/).map(coord => {
                        const [longitude, latitude] = coord.split(',').map(Number);
                        return [latitude, longitude];
                    }).filter(Boolean);
    
                    confineCongregazione.push(coordinates);

                    // Create a polygon
                    const polygon = L.polygon(coordinates, {
                        color: 'darkgreen',
                        fillColor: 'green',
                        fillOpacity: 0.1
                    }).addTo(map);
    
                    // Get the bounds of the polygon and fit the map to those bounds
                    const bounds = polygon.getBounds();
                    map.fitBounds(bounds);
                }
            };
            reader.readAsText(file);
            clearFileInput("fileInputConfini");
        }
    }
    
    function handleFileSelectDB(event) {
        // Chiedi conferma all'utente
        const file = event.target.files[0];

        const userConfirmed = confirm(`Si stanno modificando i dati esistenti. Vuoi proseguire a caricare il file: ${file.name}?`);

        if (file && file.type === 'application/json') {
            if (userConfirmed) {
                if (file) {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        try {
                            jsonTemp = JSON.parse(e.target.result);

                            /* Gestione dei colori per i Gruppi di Servizio */
                            //re-inizializzo la comboGruppiServizioHTML
                            comboGruppiServizioHTML = ""
                            comboColorGruppiServizio.forEach(({ id, nome, color }) => {
                                comboGruppiServizioHTML += "<option value=" + id + ">" + nome + "</option>";
                            });
                            document.getElementById("colorGruppiServizio").innerHTML = comboGruppiServizioHTML;

                            /* Gestione del Singolo Componente */
                            var countComponente = 1;
                            if(jsonTemp.congregazione.componenti != undefined){
                                jsonTemp.congregazione.componenti.forEach(({ id, name, address, cap, city, group, p_regolare, p_sorvegliante, p_assistente, lat, lon }) => {
                                    const completeAddress = address + ", " + cap + " " + city + " Italy";

                                    if ((lat === undefined && lon === undefined) || (lat === "" && lon === "")) {
                                        // Geocode address to coordinates
                                        fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${completeAddress}`)
                                            .then(response => response.json())
                                            .then(data => {

                                                if (data.length > 0) {
                                                    const { lat, lon } = data[0];
                                                    id = countComponente;
                                                    componente.push({ id, name, address, cap, city, group, p_regolare, p_sorvegliante, p_assistente, lat, lon });
                                                    renderComponente();
                                                    componenteForm.reset();
                                                    countComponente++;
                                                } else {
                                                    alert('Indirizzo non trovato di ' + name);
                                                }
                                            })
                                            .catch(error => alert('Errore nella geocodifica dell\'indirizzo di ' + name));
                                    } else {
                                        id = countComponente;
                                        componente.push({ id, name, address, cap, city, group, p_regolare, p_sorvegliante, p_assistente, lat, lon });
                                        renderComponente();
                                        componenteForm.reset();
                                        countComponente++;
                                    }
                                });
                            }

                            /* Gestione dei Gruppi di Servizio */
                            if(jsonTemp.congregazione.gruppiDiServizio != undefined){
                                jsonTemp.congregazione.gruppiDiServizio.forEach(({ id, name, color }) => {
                                    if (name != "ND") {
                                        gruppiServizio.push({ id, name, color });
                                    }
                                    renderGruppiServizio();
                                    gruppiServizioForm.reset();
                                });
                            }
                          
                            comboGruppiServizioHTML = ""
                            for (var key in gruppiServizio) {
                                comboGruppiServizioHTML += "<option value=" + gruppiServizio[key].id + ">" + gruppiServizio[key].name + "</option>"
                            }
                            document.getElementById("serviceGroup").innerHTML = comboGruppiServizioHTML;

                            /* Gestione dei Confini */
                            if(jsonTemp.congregazione.confineDiCongregazione != undefined){
                                jsonTemp.congregazione.confineDiCongregazione.forEach((coordinateSet) => {
                                    // Trasformiamo le coordinate in un array di array di coordinate
                                    confineCongregazione = []
                                    
                                    confineCongregazione.push([coordinateSet[0], coordinateSet[1]]);
                                    
                                    // `coordinateSet` è l'array di coordinate per un singolo poligono
                                    if (coordinateSet.length > 0) {
                                        const polygon = L.polygon(coordinateSet, {
                                            color: 'darkgreen',
                                            fillColor: 'green',
                                            fillOpacity: 0.1
                                        }).addTo(map);
                                    }
                                });
                            }

                            /* Gestione dei Punti Ritrovo */
                            if (jsonTemp.congregazione.puntiDiRitrovo !== undefined) {
                                jsonTemp.congregazione.puntiDiRitrovo.forEach((coordinate) => {
                                    // Trasformiamo le coordinate in un array di array di coordinate
                                    puntiRitrovo = [];
                                    for (var key in coordinate) {
                                        puntiRitrovo.push([coordinate[key][0], coordinate[key][1]]);
                                    }
                            
                                    // Aggiungiamo il poligono solo se abbiamo coordinate valide
                                    if (puntiRitrovo.length > 0) {
                                        L.polygon(puntiRitrovo, {
                                            color: 'red',
                                            fillColor: 'red',
                                            fillOpacity: 0.1
                                        }).addTo(map);
                                    }
                                });
                            }
                          
                        } catch (error) {
                            console.log(error);
                            alert('Errore nel parsing del file JSON.');
                        }

                    };

                    reader.readAsText(file);
                    clearFileInput("fileInputDB");
                }
            }else {
                // Se l'utente annulla, resettare l'input file (opzionale)
                event.target.value = '';
                alert('Caricamento del file annullato.');
            }
        } else {
            alert('Per favore, carica un file JSON valido.');
        }    
    }

    function handleShow(event){
        document.getElementById('header').style.display = "revert-layer";
        show.style.display = "none";
        hide.style.display = "revert-layer";
    }
    
    function handleHide(event){
        document.getElementById('header').style.display = "none";
        hide.style.display = "none";
        show.style.display = "revert-layer";
    }
    
    function handleAddComponente(event) {
        event.preventDefault();
        const name = document.getElementById('name').value;
        const address = document.getElementById('address').value;
        const cap = document.getElementById('cap').value;
        const city = document.getElementById('city').value;
        const group = document.getElementById('serviceGroup').value;
        const lat = document.getElementById('lat').value;
        const lon = document.getElementById('lon').value;
        const p_regolare = document.getElementById('p_regolare').checked;
        const p_sorvegliante = document.getElementById('p_sorvegliante').checked;
        const p_assistente = document.getElementById('p_assistente').checked;

        var id = componente.length + 1;

        const completeAddress = address + " " + cap + " " + city;
        if ((lat == undefined && lon == undefined) || (lat == "" && lon == "")) {
            // Geocode address to coordinates
            fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${completeAddress}`)
                .then(response => response.json())
                .then(data => {
                    if (data.length > 0) {
                        const { lat, lon } = data[0];
                        componente.push({ id, name, address, cap, city, group, p_regolare, p_sorvegliante, p_assistente, lat, lon });
                        renderComponente();
                        componenteForm.reset();
                    } else {
                        alert('Indirizzo non trovato.');
                    }
                })
                .catch(error => {
                    alert('Errore nella geocodifica dell\'indirizzo.');
                    console.log(error);
                });
        } else {
            componente.push({ id, name, address, cap, city, group, p_regolare, p_sorvegliante, p_assistente, lat, lon });
            renderComponente();
            componenteForm.reset();
        }
    }

    function handleModifyComponente(event) {
        event.preventDefault();
        const name = document.getElementById('name').value;
        const address = document.getElementById('address').value;
        const cap = document.getElementById('cap').value;
        const city = document.getElementById('city').value;
        const group = document.getElementById('serviceGroup').value;
        const lat = document.getElementById('lat').value;
        const lon = document.getElementById('lon').value;
        const p_regolare = document.getElementById('p_regolare').checked;
        const p_sorvegliante = document.getElementById('p_sorvegliante').checked;
        const p_assistente = document.getElementById('p_assistente').checked;
        const idComponente = document.getElementById('idComponente').value;

        componente.forEach((item) => {
            if (item.id == idComponente) {
                item.name = name;
                item.address = address;
                item.cap = cap;
                item.city = city;
                item.group = group;
                item.lat = lat;
                item.lon = lon;
                item.p_regolare = p_regolare;
                item.p_sorvegliante = p_sorvegliante;
                item.p_assistente = p_assistente;
            }
        });

        renderComponente();
    }

    function handleDeleteComponente(event) {
        event.preventDefault();
        const id = document.getElementById('idComponente').value;
        if (id != "") {
            removeObjectWithId(componente, id);
            renderComponente();
            componenteForm.reset();
            $("#componenteModal").dialog("close");
        }
    }

    function handleAddGruppiServizio(event) {
        event.preventDefault();
        const name = document.getElementById('nameGruppiServizio').value;
        const color = document.getElementById('colorGruppiServizio').value;
        const id = gruppiServizio.length + 1;

        gruppiServizio.push({ id, name, color });
        renderGruppiServizio();
        renderComponente();
        gruppiServizioForm.reset();
    }

    function handleModifyGruppiServizio(event) {
        event.preventDefault();
        const nameGruppiServizio = document.getElementById('nameGruppiServizio').value;
        const colorGruppiServizio = document.getElementById('colorGruppiServizio').value;
        const idGruppiServizio = document.getElementById('idGruppiServizio').value;

        gruppiServizio.forEach((item) => {
            if (item.id == idGruppiServizio) {
                item.name = nameGruppiServizio;
                item.color = colorGruppiServizio;
                item.id = idGruppiServizio;
            }
        });
        renderGruppiServizio();
        renderComponente();
    }

    function handleDeleteGruppiServizio(event) {
        event.preventDefault();
        const idGruppiServizio = document.getElementById('idGruppiServizio').value;
        if (idGruppiServizio != "") {
            removeObjectWithId(gruppiServizio, idGruppiServizio);
            renderGruppiServizio();
            gruppiServizioForm.reset();
            $("#gruppiServizioModal").dialog("close");
        }
        renderComponente();
    }

    function removeObjectWithId(arr, id) {
        const objWithIdIndex = arr.findIndex((obj) => obj.id === id);
        arr.splice(objWithIdIndex, 1);
        return arr;
    }

    function addComponete(event) {
        componenteForm.reset();
        $("#modificaComponente").hide();
        $("#eliminaComponente").hide();
        $("#aggiungiComponente").show();
        $("#componenteModal").dialog("open");
    }

    function addGruppiServizio(event) {
        gruppiServizioForm.reset();
        $("#aggiungiGruppiServizio").show();
        $("#modificaGruppiServizio").hide();
        $("#eliminaGruppiServizio").hide();
        $("#gruppiServizioModal").dialog("open");
    }

    function renderComponente() {
        componentiList.innerHTML = '';
        map.eachLayer(layer => {
            if (layer instanceof L.Marker) {
                map.removeLayer(layer);
            }
        });

        const positionMap = {};

        componente.sort(function (a, b) {
            if (a.name < b.name) {
                return -1;
            }
            if (a.name > b.name) {
                return 1;
            }
            return 0;
        });

        // Raggruppa i marker per posizione
        componente.forEach(({ lat, lon }, index) => {
            const positionKey = `${lat},${lon}`;
            if (!positionMap[positionKey]) {
                positionMap[positionKey] = [];
            }
            positionMap[positionKey].push(index);
        });


        componente.forEach(({ id, name, address, cap, city, group, p_regolare, p_sorvegliante, p_assistente, lat, lon }, index) => {

            const li = document.createElement('li');

            var coloreMaker = "grey";
            var nomeGruppo = "ND";

            if (group == "" || group == undefined) { group = 0; }
            if (p_sorvegliante == "" || p_sorvegliante == undefined) { p_sorvegliante = false; }
            if (p_assistente == "" || p_assistente == undefined) { p_assistente = false; }
            if (p_regolare == "" || p_regolare == undefined) { p_regolare = false; }

            if (group != 1) {
                gruppiServizio.forEach((item) => {
                    if (item.id == group) {
                        nomeGruppo = item.name;
                        coloreMaker = comboColorGruppiServizio[item.color].color;
                    }
                })
            }

            var selectedTypes = Array.from(document.querySelectorAll('.filter:checked')).map(function (cb) {
                return cb.value;
            });

            comboGruppiServizioHTML = ""
            for (var key in gruppiServizio) {
                comboGruppiServizioHTML += "<option value=" + gruppiServizio[key].id + ">" + gruppiServizio[key].name + "</option>"
            }

            // Se ci sono più marker con la stessa posizione, calcola un offset per affiancarli
            const positionKey = `${lat},${lon}`;
            const duplicates = positionMap[positionKey];
            let offsetLat = 0;
            let offsetLon = 0;

            if (duplicates.length > 1) {
                const offsetFactor = 0.0003; // Offset di base per separare i marker
                const positionIndex = duplicates.indexOf(index);
                // Distribuisci i marker in un piccolo cerchio attorno alla posizione centrale
                offsetLat = offsetFactor * Math.cos(2 * Math.PI * positionIndex / duplicates.length);
                offsetLon = offsetFactor * Math.sin(2 * Math.PI * positionIndex / duplicates.length);
            }

            var popupContent = `
                <div>
                    <span class="namePopup"><h4>${name}</h4></span>
                    <span class="indirizzoPopup"><h4>${address}</h4> <h4>${city}</h4></span>
                    <span class="gruppoPopup">
                        <h4>Gruppo di servizio</h4>
                        <select id="selectOptions_${id}" name="selectOptions" style="margin-top: 1.33em;">
                        ${comboGruppiServizioHTML}
                        </select>
                    </span>
					<span class="sogPopup"><h4>Sorvegliante di Gruppo</h4><input type="checkbox" id="p_sorvegliante_${id}" style="margin-top: 1.33em;" /></span>
					<span class="assPopup"><h4>Assisitente</h4><input type="checkbox" id="p_assistente_${id}" style="margin-top: 1.33em;" /></span>
					<span class="regPopup"><h4>Pioniere Regolare</h4><input type="checkbox" id="p_regolare_${id}" style="margin-top: 1.33em;" /></span>
                </div>`;

            var marker = "";
            li.onclick = function () {
                if (selectedTypes.includes(group)) {
                    marker = L.marker([parseFloat(lat) + parseFloat(offsetLat), parseFloat(lon) + parseFloat(offsetLon)], { draggable: true , icon: getColorByType(coloreMaker, p_regolare, p_sorvegliante, p_assistente) }).addTo(map)
                        .bindPopup(`${popupContent}`).openPopup();
                    $('#selectOptions_' + id).val(group);
                    $('#p_regolare_' + id).attr('checked', p_regolare);
                    $('#p_sorvegliante_' + id).attr('checked', p_sorvegliante);
                    $('#p_assistente_' + id).attr('checked', p_assistente);

                    // Aggiorna le coordinate e l'indirizzo quando il marker viene rilasciato
                    marker.on('dragend', function (event) {
                        const position = marker.getLatLng();
                        componente[index].lat = position.lat;
                        componente[index].lon = position.lng;
                        renderComponente();
                    }),

                    $('#selectOptions_' + id).on('change', function () {
                        componente.forEach((item) => {
                            if (item.id == id) {
                                item.group = this.value;
                            }
                        });
                        renderComponente();
                    });

                    $('#p_sorvegliante_' + id).on('change', function () {
                        componente.forEach((item) => {
                            if (item.id == id) {
                                if ($(this).prop("checked")) {
                                    item.p_sorvegliante = true;
                                } else { item.p_sorvegliante = false; }
                            }
                        });
                        renderComponente();
                    });
                    $('#p_assistente_' + id).on('change', function () {
                        componente.forEach((item) => {
                            console.log($(this).prop("checked") +" "+ item.id+" "+ id)
                            if (item.id == id) {
                                if ($(this).prop("checked")) {
                                    item.p_assistente = true;
                                } else { item.p_assistente = false; }
                            }
                        });
                        renderComponente();
                    });
                    $('#p_regolare' + id).on('change', function () {
                        componente.forEach((item) => {
                            if (item.id == id) {                                
                                if ($(this).prop("checked")) {
                                    item.p_regolare = true;
                                } else { item.p_regolare = false; }
                            }
                        });
                        renderComponente();
                    });

                }
            };
            
            
            if (selectedTypes.includes(group)) {
                marker = L.marker([parseFloat(lat) + parseFloat(offsetLat), parseFloat(lon) + parseFloat(offsetLon)], { draggable: true , icon: getColorByType(coloreMaker, p_regolare, p_sorvegliante, p_assistente) }).addTo(map)
                    .bindPopup(`${popupContent}`);

                // Aggiorna le coordinate e l'indirizzo quando il marker viene rilasciato
                marker.on('dragend', function (event) {
                    const position = marker.getLatLng();
                    componente[index].lat = position.lat;
                    componente[index].lon = position.lng;
                    renderComponente();
                });
                
                marker.on('popupopen', function () {
                    $('#selectOptions_' + id).val(group);
                    $('#selectOptions_' + id).on('change', function () {                    
                        componente.forEach((item) => {
                            if (item.id == id) {
                                item.group = this.value;
                            }
                        });
                        renderComponente();
                    });

                    $('#p_regolare_' + id).attr('checked', p_regolare);
                    $('#p_sorvegliante_' + id).attr('checked', p_sorvegliante);
                    $('#p_assistente_' + id).attr('checked', p_assistente);

                    $('#p_sorvegliante_' + id).on('change', function () {
                        componente.forEach((item) => {
                            if (item.id == id) {                               
                                if ($(this).prop("checked")) {
                                    item.p_sorvegliante = true;
                                } else { item.p_sorvegliante = false; }
                            }
                        });
                        renderComponente();
                    });

                    $('#p_assistente_' + id).on('change', function () {
                        componente.forEach((item) => {
                            console.log($(this).prop("checked") +" "+ item.id+" "+ id)
                            if (item.id == id) {
                                if ($(this).prop("checked")) {
                                    item.p_assistente = true;
                                } else { item.p_assistente = false; }
                            }
                        });
                        renderComponente();
                    });

                    $('#p_regolare_' + id).on('change', function () {
                        componente.forEach((item) => {
                            if (item.id == id) {                                
                                if ($(this).prop("checked")) {
                                    item.p_regolare = true;
                                } else { item.p_regolare = false; }
                                
                            }
                        });
                        renderComponente();
                    });
                });
            }
                
            li.ondblclick = function () {
                componenteForm.reset();
                $("#idComponente").val(id);
                $("#name").val(name);
                $("#address").val(address);
                $("#city").val(city);
                $("#cap").val(cap);
                $("#serviceGroup").val(group);
                $("#lat").val(lat);
                $("#lon").val(lon);

                $("#p_regolare").attr('checked', p_regolare);
                $("#p_sorvegliante").attr('checked', p_sorvegliante);
                $("#p_assistente").attr('checked', p_assistente);

                $("#aggiungiComponente").hide();
                $("#modificaComponente").show();
                $("#eliminaComponente").show();
                $("#componenteModal").dialog("open");
            };
            var simbolo = "&#10140;";
            var classStyle = "";
            if (group == 1 || group == "") {
                simbolo = "&#10006;";
                classStyle = "blink_text";
            }
            var proc = "<span style='color:" + coloreMaker + "' class='" + classStyle + "'>" + simbolo + "</span>" + name
            li.textContent = "";
            li.innerHTML = proc;

            componentiList.appendChild(li);
            document.getElementById("countProclamatori").innerHTML = "NumeroProclamatori: " + componente.length;

        });
        if (componente.length > 0) {
            const firstAddress = componente[0];
            map.setView([firstAddress.lat, firstAddress.lon], 13);
        }

        raggruppaGruppiServizio();
    }

    function getColorByType(coloreMaker, p_regolare, p_sorvegliante, p_assistente) {

        // Define the custom icon with HTML
        var customIcon = L.divIcon({
            html: `
            <div style="position: relative; display: flex; align-items: center;">
                <i class="fa-solid fa-location-dot fa-2xl" style="color:${coloreMaker}; -webkit-text-stroke: 1px white; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);" aria-hidden="true"></i>                
            </div>
            `,
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41], // Anchor the icon to its location
            className: '' // Add a custom class if you need additional styling
        });





        if (p_regolare === true) {
            customIcon = L.divIcon({
                html: `
				<div style="position: relative; display: flex; align-items: center;">
					<i class="fa-solid fa-briefcase fa-2xl" style="color: ${coloreMaker}; -webkit-text-stroke: 1px white; text-shadow: 2px 2px 4px rgba(0, 0, 0, 1.5);"></i>
				</div>
				`,
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41],
                className: '' // Add a custom class if you need additional styling
            });
        }

        if (p_assistente === true) {
            customIcon = L.divIcon({
                html: `
				<div style="position: relative; display: flex; align-items: center;">
					<i class="fa-solid fa-handshake fa-2xl" style="color: ${coloreMaker}; -webkit-text-stroke: 1px white; text-shadow: 2px 2px 4px rgba(0, 0, 0, 1.5);"></i>
				</div>
				`,
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41],
                className: '' // Add a custom class if you need additional styling
            });
        }
        if (p_sorvegliante === true) {
            customIcon = L.divIcon({
                html: `
				<div style="position: relative; display: flex; align-items: center;">
					<i class="fa-solid fa-user fa-2xl" style="color: ${coloreMaker}; -webkit-text-stroke: 1px white; text-shadow: 2px 2px 4px rgba(0, 0, 0, 1.5);"></i>
				</div>
				`,
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41],
                className: '' // Add a custom class if you need additional styling
            });
        }

        return customIcon;
    }

    function renderGruppiServizio() {
        gruppiServizioList.innerHTML = '';

        gruppiServizio.forEach(({ id, name, color }) => {
            const li = document.createElement('li');
            var colorSpan = "grey";
            comboColorGruppiServizio.forEach((item) => {
                if (item.id == color) { colorSpan = item.color; }
            })
            var proc = "<span style='color:" + colorSpan + "'>&#10140;</span>" + name
            li.textContent = "";
            li.innerHTML = proc;
            li.ondblclick = function () {
                gruppiServizioForm.reset();
                $("#idGruppiServizio").val(id);
                $("#nameGruppiServizio").val(name);
                $("#colorGruppiServizio").val(color);
                $("#aggiungiGruppiServizio").hide();
                $("#modificaGruppiServizio").show();
                $("#eliminaGruppiServizio").show();
                $("#gruppiServizioModal").dialog("open");
            };

            gruppiServizioList.appendChild(li);

        });

        var filtro = "";
        comboGruppiServizioHTML = ""
        for (var key in gruppiServizio) {
            comboGruppiServizioHTML += "<option value=" + gruppiServizio[key].id + ">" + gruppiServizio[key].name + "</option>"
            filtro += '<label><input type="checkbox" class="filter" value="' + gruppiServizio[key].id + '" checked> ' + gruppiServizio[key].name + ' </label>'
        }
        document.getElementById("serviceGroup").innerHTML = comboGruppiServizioHTML;


        document.getElementById("filters").innerHTML = filtro;

        renderComponente();
        raggruppaGruppiServizio();

        document.querySelectorAll('.filter').forEach(function (cb) {
            cb.addEventListener('change', renderComponente);

        });

        gruppiServizio.sort(function (a, b) {
            if (a.name < b.name) {
                return -1;
            }
            if (a.name > b.name) {
                return 1;
            }
            return 0;
        });

        const objWithIdIndex = gruppiServizio.findIndex((obj) => obj.name === "Nessun Gruppo");
        if (objWithIdIndex > -1) {
            gruppiServizio.splice(objWithIdIndex, 1);
        }

    }

    function raggruppaGruppiServizio() {
        var temp;
        ragruppamentiGruppiList.innerHTML = '';
        gruppiServizio.forEach(({ id, name, color }) => {
            var divHeaderInterno;
            var ulInterno;
            var liInterno;
            temp = document.createElement('div');
            temp.id = id + "_" + name;
            var idGruppo = id;
            temp.className = 'results';

            divHeaderInterno = document.createElement('div');
            ulInterno = document.createElement('ul');

            //divHeaderInterno.style['-webkit-text-stroke'] = "1px #88ff05";

            var countProcl = 0;
            componente.forEach(({ id, name, address, cap, city, group, p_regolare, p_sorvegliante, p_assistente, lat, lon }) => {
                if (idGruppo == group) {
                    countProcl++;
                    // Create new LI
                    liInterno = document.createElement("li");
                    pre = document.createElement("pre");
                    if (p_regolare)
                        liInterno.style.fontWeight = "bold";
                    // Append the spelling word
                    var sigla = "   ";
                    if (p_sorvegliante) { sigla = "(S)" }
                    if (p_assistente) { sigla = "(A)" }
                    pre.append(sigla + " " + name)
                    liInterno.append(pre);

                    // Add to list
                    ulInterno.append(liInterno);
                }
            });

            var colorSpan = "grey";
            comboColorGruppiServizio.forEach((item) => {
                if (item.id == color) { colorSpan = item.color; }
            })
            var span = "<span style='font-size: 3rem;color:" + colorSpan + "'>&#9632;</span>"

            ragruppamentiGruppiList.append(temp);

            $("#" + temp.id).append(divHeaderInterno);
            $("#" + temp.id).append(ulInterno);

            divHeaderInterno.innerHTML = span + " Gruppo " + name + " (" + countProcl + ")";



        });
    }

    function saveFile() {

        var dataRows = getDati();

        const blob = new Blob([JSON.stringify(dataRows, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;

        const today = new Date();
        const yyyy = today.getFullYear();
        let mm = today.getMonth() + 1; // Months start at 0!
        let dd = today.getDate();
        let hh = today.getHours();
        let min = today.getMinutes();

        a.download = 'data_' + yyyy + '' + mm + '' + dd + '_' + hh + '' + min + '.json';
        a.click();
        URL.revokeObjectURL(url);
    }

    function exportExcel(json) {
        let dataRows = getDati();

        var wb = XLSX.utils.book_new();


        // Aggiungi i dati dei componenti                
        var wsComponenti = XLSX.utils.json_to_sheet(dataRows.congregazione.componenti);
        XLSX.utils.book_append_sheet(wb, wsComponenti, "Componenti");
        /* fix headers */
        var wsComp = XLSX.utils.sheet_add_aoa(wsComponenti, [[" ", "Nome", "Indirizzo", "CAP", "Citta'", "Pioniere", "Gruppo di Servizio", "Latitudine", "Longitudine"]], { origin: "A1" });

        var countCompRow = 2;
        dataRows.congregazione.componenti.forEach((comp) => {

            var p_regolare_mod = "";
            if (comp.p_regolare === true) { p_regolare_mod = "SI"; }
            var p_gruppo_name = "";
            gruppiServizio.forEach((gds) => {
                if (comp.group == gds.id) {
                    p_gruppo_name = gds.name;
                }
            });
            wsGruppi = XLSX.utils.sheet_add_aoa(wsComponenti, [["", comp.name, comp.address, comp.cap, comp.city, p_regolare_mod, p_gruppo_name, comp.lat, comp.lon]], { origin: "A" + countCompRow });
            countCompRow++;

        });

        var wscolsComp = [
            { wch: 6 }, //ID
            { wch: 25 }, //Nome Cognome
            { wch: 25 },//Indirizzo
            { wch: 10 }, //CAP
            { wch: 20 }, //Città
            { wch: 6 }, //Pioniere
            { wch: 15 }, //Gruppo di servizio
            { wch: 10 }, //LAT
            { wch: 10 } //LON
        ];
        wsComp['!cols'] = wscolsComp;


        // Aggiungi i dati dei gruppi di servizio
        var wsGruppiDiServizio = XLSX.utils.json_to_sheet(dataRows.congregazione.gruppiDiServizio);

        XLSX.utils.book_append_sheet(wb, wsGruppiDiServizio, "GruppiDiServizio");
        var wsGruppi = XLSX.utils.sheet_add_aoa(wsGruppiDiServizio, [["", "Gruppo di Servizio", ""]], { origin: "A1" });

        let countRow = 2;
        dataRows.congregazione.gruppiDiServizio.forEach((gds) => {
            wsGruppi = XLSX.utils.sheet_add_aoa(wsGruppiDiServizio, [["Gruppo:" + gds.name, "Nome Proclamatore", "Pioniere Regolare"]], { origin: "A" + countRow });

            countRow++;
            dataRows.congregazione.componenti.forEach((comp) => {
                if (comp.group == gds.id) {
                    var p_regolare_mod = "";
                    if (comp.p_regolare === true) { p_regolare_mod = "SI"; }
                    var sigla = "    ";
                    if (comp.p_sorvegliante === true) { sigla = "(S)" }
                    if (comp.p_assistente === true) { sigla = "(A)" }
                    wsGruppi = XLSX.utils.sheet_add_aoa(wsGruppiDiServizio, [["", sigla + " " + comp.name, p_regolare_mod]], { origin: "A" + countRow });
                    countRow++;
                }
            });

        });
        var wscolsGruppi = [
            { wch: 30 }, //Nome Gruppo
            { wch: 30 }, //Nome Componente
            { wch: 6 } //ID Gruppo
        ];

        wsGruppi['!cols'] = wscolsGruppi

        const today = new Date();
        const yyyy = today.getFullYear();
        let mm = today.getMonth() + 1; // Months start at 0!
        let dd = today.getDate();
        let hh = today.getHours();
        let min = today.getMinutes();

        // Scrivi il file Excel
        XLSX.writeFile(wb, "Congregazione_" + yyyy + "" + mm + "" + dd + "_" + hh + "" + min + ".xlsx");
    }

    function getDati() {
        var componenti = [];
        var gruppiDiServizio = [];
        var confineDiCongregazione = [];
        var puntiDiRitrovo = [];

        var dataRows = {
            congregazione: {}
        };

        componente.forEach((item) => {
            if (item.group == "" || item.group == undefined) { item.group = 1; }
            if (item.p_sorvegliante == "" || item.p_sorvegliante == undefined) { item.p_sorvegliante = false; }
            if (item.p_assistente == "" || item.p_assistente == undefined) { item.p_assistente = false; }
            if (item.p_regolare == "" || item.p_regolare == undefined) { item.p_regolare = false; }
            componenti.push(item);
        });

        gruppiServizio.forEach((item) => {
            gruppiDiServizio.push(item);
        });

        confineCongregazione.forEach((item) => {
            confineDiCongregazione.push(item);
        });

        puntiRitrovo.forEach((item) => {
            puntiDiRitrovo.push(item);
        });

        dataRows.congregazione.componenti = componenti;
        dataRows.congregazione.gruppiDiServizio = gruppiDiServizio;
        dataRows.congregazione.confineDiCongregazione = confineDiCongregazione;
        dataRows.congregazione.puntiDiRitrovo = puntiDiRitrovo;
        return dataRows;
    }

});

$(function () {
    $("#componenteModal").dialog({
        autoOpen: false,
        show: {
            effect: "blind",
            duration: 1000
        },
        hide: {
            effect: "explode",
            duration: 1000
        }
    });

    $("#gruppiServizioModal").dialog({
        autoOpen: false,
        show: {
            effect: "blind",
            duration: 1000
        },
        hide: {
            effect: "explode",
            duration: 1000
        }
    });

});

function openTab(evt, idTab) {
    // Declare all variables
    var i, tabcontent, tablinks;

    // Get all elements with class="tabcontent" and hide them
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    // Get all elements with class="tablinks" and remove the class "active"
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    // Show the current tab, and add an "active" class to the button that opened the tab
    document.getElementById(idTab).style.display = "block";
    evt.currentTarget.className += " active";
}
