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

Apri una shell nella cartella in cui vuoi eseguire il progetto ed esegui il comando:
### Windows
```bash
    python -m venv NOME_ENVIRONMENT
``` 

### macOS
``` bash
    python3 -m venv myenv
``` 

## 3. Attivazione virtual environment
### Windows Powershell
``` bash
    {path_directory_venv_progetto}\Scripts\Activate.ps1
``` 
### macOS
``` bash
    source {path_directory_venv_progetto}/bin/activate
``` 

# Clonazione della repo di GitHub
``` bash
    git clone https://github.com/GhislandiGiulio/progetto_redis.git .
``` 

# Installazione delle dipendenze
Installazione moduli richiesti per eseguire lo script python:
``` bash
    pip install requirements.txt
```
# Installazione di Redis server con Docker
Se non già installato, scarica l'eseguibile di Docker dal [sito ufficiale](https://www.docker.com/products/docker-desktop/).
Una volta installato, fai il pull dell'imagine di Redis:
``` bash
    docker pull redis 
```
Adesso crea un container con port-forwarding:
``` bash
    docker run --name NOME_CONTAINER -p 6379:6379 redis -d 
```

## Ora puoi eseguire il progetto! 