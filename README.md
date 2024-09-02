# English

## Congregation Tools App

Congregation Tools App (Scra - ViGeo) is a PyQt5-based application designed to help manage congregation schedules and tasks. The application provides tools for generating HTML reports for various congregation activities such as weekend schedules, midweek schedules, AV attendants, cleaning tasks, and service groups. It integrates web content scraping, local HTML viewing, and file download handling, all within an easy-to-use GUI.

## Features

- **Multi-tab Interface**: Organizes various functionalities into different tabs.
- **Web Content Integration**: Loads external web pages using `QWebEngineView` and injects custom JavaScript to monitor link clicks and scrape content.
- **HTML Generation**: Generates printable HTML reports for different congregation activities such as weekend schedules, midweek schedules, AV attendant schedules, and cleaning tasks.
- **Progress Tracking**: Displays a progress bar to track the progress of tasks like content scraping and report generation.
- **File Handling**: Handles file downloads and saves generated HTML content to appropriate directories depending on the operating system (e.g., Desktop folder).
- **Cross-Platform Support**: Works on Windows, macOS, and Linux, with specific file handling logic for different OS environments.
- **Auto-Update Checking**: Checks for application updates at startup using GitHub API.

## Requirements

- Python 3.x
- PyQt5
- PyQtWebEngine

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/your-username/congregationToolsApp.git
   cd congregationToolsApp

2. **Install Dependencies:**
    pip install -r requirements.txt

3. **Run the Application:**
    python congregationToolsApp.py

4. **Contributing:**
    1. Fork the repository.
    2. Create your feature branch (git checkout -b feature/my-feature).
    3. Commit your changes (git commit -m 'Add some feature').
    4. Push to the branch (git push origin feature/my-feature).
    5. Open a pull request.


# Italiano

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
