# Solo per la gestione in Italiano

## Congregation Tools App

Congregation Tools App (Scra - ViGeo) è un'applicazione basata su PyQt5 progettata per aiutare nella gestione degli orari e delle attività della congregazione. L'app fornisce strumenti per generare report HTML per varie attività della congregazione, come programmi del fine settimana, programmi infrasettimanali, incarichi AV, attività di pulizia e gruppi di servizio. Integra lo scraping dei contenuti web, la visualizzazione di HTML locali e la gestione dei download di file, il tutto all'interno di una GUI facile da usare.

## Funzionalità

- **Interfaccia Multi-Tab**: Organizza varie funzionalità in diversi tab.
- **Integrazione di Contenuti Web**: Carica pagine web esterne utilizzando `QWebEngineView` e inietta JavaScript personalizzato per monitorare i clic sui link e fare scraping dei contenuti.
- **Generazione di HTML**: Genera report HTML stampabili per diverse attività della congregazione, come programmi del fine settimana, programmi infrasettimanali, incarichi AV e pulizie.
- **Monitoraggio del Progresso**: Mostra una barra di avanzamento per monitorare il progresso di attività come lo scraping dei contenuti e la generazione dei report.
- **Gestione File**: Gestisce i download dei file e salva i contenuti HTML generati nelle directory appropriate a seconda del sistema operativo (ad esempio, nella cartella Desktop).
- **Supporto Multipiattaforma**: Funziona su Windows, macOS e Linux, con logica di gestione dei file specifica per i diversi ambienti OS.
- **Verifica Aggiornamenti Automatica**: Controlla aggiornamenti dell'app all'avvio utilizzando l'API di GitHub.

## Requisiti

- Python 3.x
- PyQt5
- PyQtWebEngine

## Installazione

1. **Clona il Repository:**

   ```bash
   git clone https://github.com/your-username/congregationToolsApp.git
   cd congregationToolsApp

2. **Installa le librerie Python richieste:**
    pip install -r requirements.txt

3. **Esegui l'Applicazione:**
    python congregationToolsApp.py

4. **Contribuire:**
    1. Fai un fork del repository.
    2. Crea il tuo branch per la nuova funzionalità (git checkout -b feature/my-feature).
    3. Esegui il commit delle tue modifiche (git commit -m 'Aggiungi una nuova funzionalità').
    4. Effettua il push sul branch (git push origin feature/my-feature).
    5. Apri una pull request.
