
# Pre-Requisiti
## (per Windows) Abilita esecuzione di script su PowerShell
``` bash
    set-executionpolicy remotesigned
``` 

## Creazione cartella
Crea una cartella apposita per il tuo progetto. Il nome non ha importanza.

Apri una shell nella cartella in cui vuoi eseguire il progetto ed esegui i seguenti comandi:
# Clonazione della repo di GitHub
``` bash
    git clone https://github.com/GhislandiGiulio/progetto_redis.git .
``` 

# Impostazione ambiente virtuale: venv

## 1. installazione interprete python

Se non è già installato, scarica Python 3.12. Se è già installato, assicurati che sia la versione attiva nel sistema di python.
Comandi per scaricare e installare Python 3.12:
### Windows:
```bash
    winget install -e --id Python.Python.3.12
```

### macOS (homebrew)
```bash
    brew install python@3.12
```

## 2. Creazione virtual environment

### Windows
```bash
    py -3.12 -m venv .venv
``` 

### macOS
``` bash
    python3.9 -m venv .venv
``` 

## 3. Attivazione virtual environment
### Windows Powershell
``` bash
    [PATH_DIRECTORY_PROGETTO]\.venv\Scripts\Activate.ps1
``` 
### macOS
``` bash
    source [PATH_DIRECTORY_PROGETTO]/.venv/bin/activate
``` 

# Installazione delle dipendenze
Installazione moduli richiesti per eseguire lo script python:
``` bash
    pip install -r requirements.txt
```
# Installazione di Redis server con Docker
Se non già installato, scarica l'eseguibile di Docker dal [sito ufficiale](https://www.docker.com/products/docker-desktop/).
Una volta installato, fai il pull dell'imagine di Redis:
``` bash
    docker pull redis 
```
Adesso crea un container con port-forwarding:
``` bash
    docker run -d --name NOME_CONTAINER -p 6379:6379 redis 
```

## Ora puoi eseguire il progetto! 
