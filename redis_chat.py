import redis
import os

# inizializzazione utente logged-in. Si potrebbe aggiungere una cache per memorizzarlo anche se si esce dall'esecuzione.
active_user = None

r = redis.Redis(
                    host="localhost",
                    port=6379,
                    db=0,
                    decode_responses=True
                )

# wrapper per le differenti schermate
def schermata(funzione):
    def wrapper(*args):
        if os.name == 'nt':
            # Per Windows
            os.system('cls')
        else:
            # Per Unix/Linux/macOS
            os.system('clear')

        print("Utente attivo: ", active_user if active_user != None else "guest")
        funzione()

    return wrapper

@schermata
def menu_iniziale():

    scelta = input("Scegli un'opzione:\n1- Registrazione \n2- Login \n3- Logout\n4- Chat\n5- Contatti\nq- Esci dal programma\n:")

    match scelta:
        case "1":
            registrazione()
        case "2":
            login()
        case "3":
            logout()
        case "4":
            ...
        case "5":
            contatti()
        case "q":
            exit(0)
        case _:
            pass

@schermata
def registrazione():

    print("Se vuoi uscire in qualunque momento, inserisci 'q'")

    # ciclo pe rinserimento del numero di telefono
    while True:
        nome_utente = input("Inserisci il tuo nuovo nome utente: ")

        # verifica se l'utente vuole uscire
        if nome_utente == "q":
            return

        # verifica sulla lunghezza minima e massima del nome utente
        lunghezza_nomeutente = len(nome_utente)
        if lunghezza_nomeutente < 3 or lunghezza_nomeutente > 20:
            print("Il nome utente deve avere una lunghezza compresa tra 3 e 20 (compresi)")
            continue

        # verifica dell'esistenza pregressa del nome utente
        output = r.hget("users", nome_utente)
        if output == None:
            break
        
        print("Nome utente già inserito.")

    
    # ciclo per inserimento corretto del numero di telefono
    while True:
        # ciclo per verifica della formattazione del numero di telefono    
        while True:
            numero_telefono = input("Inserisci il tuo numero di telefono: +")

            # verifica se l'utente vuole uscire
            if numero_telefono == "q":
                return

            try:
                
                # verifica della lunghezza del numero
                lunghezza_numero = len(numero_telefono)    
                if lunghezza_numero < 12 or lunghezza_numero > 13:
                    print("Il numero di telefono deve avere 12/13 cifre (incluso il prefisso).")
                    continue 

                # tentativo di casting a numero intero per verifica presenza caratteri non numerici
                numero_telefono = int(numero_telefono)
                break
            
            except ValueError:
                print("Il numero di telefono contiene simboli oltre ai numeri.")

        # verifica dell'esistenza pregressa del numero di telefono
        output = r.hget("phone_number", numero_telefono)
        if output == None:
            break

        print("Numero già registrato.")

    
    # input della password
    password = input("Inserisci la tua nuova password: ")
    
    # verifica se l'utente vuole uscire
    if password == "q":
        return
    
    # aggiunta delle chiavi all'hashmap Redis
    r.hset("users", nome_utente, password)
    r.hset("phone_number", numero_telefono, nome_utente)

@schermata
def login():

    print("Se vuoi uscire in qualunque momento, inserisci 'q'")

    # inserimento del nome utente
    nome_utente = input("Inserisci il tuo nome utente: ")

    # esci se l'utente inserisce "q"
    if nome_utente == "q":
        return

    # inserimento della password
    password = input("Inserisci la password: ")

    # esci se l'utente inserisce "q"
    if password == "q":
        return
    
    # verifica della correttezza della password / esistenza dell'utente inserito
    output = r.hget("users", nome_utente)

    if output == password and output != None :
        global active_user
        active_user = nome_utente

@schermata
def logout():

    global active_user

    if active_user != None:

        decisione = input("Sei sicuro di voler effettuare il logout?\ny=Sì\nn=No\n")

        if decisione == "y":
            active_user = None

def aggiungi_contatto():
    global active_user

    # inserimento da tastiera del nome da ricercare
    nome_utente_ricercato = input("Inserisci il nome utente del contatto da aggiungere: ")

    # scannerizzo la stringa inserita dall'utente
    _, keys = r.hscan("users", cursor=0, match=f'{nome_utente_ricercato}*', count = 10)

    # calcolo numero di risultati
    numero_risultati = len(keys)
    
    # creazione oggetto enumerate per mostrare risultati
    risultati_contati = list(enumerate(keys.items()))

    # azioni in base ai risultati
    match numero_risultati:

        # caso in cui non ci sono risultati
        case 0:
            print("Nessun risultato trovato")
            input("Premi 'invio' per continuare...")
            return

        # caso in cui c'è solo un risultato
        case 1:
            key, _ = risultati_contati[0][1]  # Estrai la chiave dalla lista
            output = r.sadd(f"{active_user}:contatti", key)
            nome_utente_ricercato = key

        # caso in cui ci sono più risultati
        case _:
            print("Scegli uno dei risultati:")

            # stampa dei risultati
            [print(i+1, key) for i, (key,_) in risultati_contati]

            # while per far scegliere all'utente il risultato senza errori
            while True:
                try:
                    i = int(input(": ")) - 1

                    if i < 0 or i >= len(risultati_contati):
                        print("Scelta non valida, riprova.")
                        continue

                    key, _ = risultati_contati[i][1]  # Estrai la chiave dalla lista
                    output = r.sadd(f"{active_user}:contatti", key)

                    nome_utente_ricercato = key
                    break

                except ValueError:
                    print("Numero non valido.")

    # stampa in base all'output del'add di redis
    if output == 0:
        print(f"L'utente {nome_utente_ricercato} è già nei contatti.")
    if output == 1:
        print(f"Utente {nome_utente_ricercato} aggiunto ai contatti.")

    input("Premi 'invio' per continuare...")

@schermata
def contatti():
    global active_user
    if active_user == None:
        return

    scelta = input("Scegli un'opzione: \n1- Aggiungi contatto \n2- Elimina contatto\n3- Visualizza contatti\nq- Torna al menù\n:")

    match scelta:
        case "q":
            return
        case "1":
            aggiungi_contatto()
        case "2":
            ...


if __name__ == "__main__":

    while True:
        menu_iniziale()
    