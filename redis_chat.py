import redis
import os
import json

## wrapper per le differenti schermate
def schermata(funzione):
    def wrapper(*args, **kwargs):
        if os.name == 'nt':
            ## Per Windows
            os.system('cls')
        else:
            ## Per Unix/Linux/macOS
            os.system('clear')

        return funzione(*args, **kwargs)

    return wrapper

@schermata
def menu_iniziale(r: redis.Redis, user: str) -> bool|str|None:
    '''Ritorna True se l'utente vuole uscire dal programma
Ritorna False se l'utente ha sbagliato la scelta o è uscito da una funzione
Ritorna None o str in tutti gli altri casi, è il valore dell'utente attivo aggiornato.'''
    print("Benvenuto", user if user != None else "anonimo")
    
    try:
        print("""
Scegli un'opzione:
1. Registrazione
2. Login 
3. Logout
4. Esci dal programma""")
        if user != None:
            print('''5. Chat
6. Aggiungi un contatto
''')
        scelta = int(input(': '))
        if scelta < 1 or scelta > 6:
            raise ValueError
    except ValueError:
        return False

    match scelta:
        case 1:
            user = registrazione(r)
        case 2:
            user = login(r)
        case 3:
            user = logout(r)
            # return True ## fate sapere se secondo voi dopo il logout dovrebbe anche uscire dal programma o no?
        case 4:
            return True
        case 5:
            ## TODO: implementare la chat
            # menu_chat(r, user)
            pass
        case 6:
            aggiungi_contatto(r, user)
    
    return user

@schermata
def registrazione(r: redis.Redis):

    print("Se vuoi uscire in qualunque momento, inserisci 'q'")

    ## ciclo pe rinserimento del numero di telefono
    while True:
        nome_utente = input("Inserisci il tuo nuovo nome utente: ")

        ## verifica se l'utente vuole uscire
        if nome_utente == "q":
            return False

        ## verifica sulla lunghezza minima e massima del nome utente
        lunghezza_nomeutente = len(nome_utente)
        if lunghezza_nomeutente < 3 or lunghezza_nomeutente > 20:
            print("Il nome utente deve avere una lunghezza compresa tra 3 e 20 (compresi)")
            continue

        ## verifica dell'esistenza pregressa del nome utente
        output = r.hget("users", nome_utente)
        if output == None:
            break
        
        print("Nome utente già inserito.")

    
    ## ciclo per inserimento corretto del numero di telefono
    while True:
        ## ciclo per verifica della formattazione del numero di telefono    
        while True:
            numero_telefono = input("Inserisci il tuo numero di telefono: +")
            
            ## verifica se l'utente vuole uscire
            if numero_telefono == "q":
                return False

            ## rimozione degli spazi
            numero_telefono = numero_telefono.replace(" ", "")

            try:
                ## verifica della lunghezza del numero
                lunghezza_numero = len(numero_telefono)
                if lunghezza_numero < 12 or lunghezza_numero > 13:
                    print("Il numero di telefono deve avere 12/13 cifre (incluso il prefisso).")
                    continue 

                ## tentativo di casting a numero intero per verifica presenza caratteri non numerici
                numero_telefono = int(numero_telefono)
                break
            
            except ValueError:
                print("Il numero di telefono contiene simboli oltre ai numeri.")

        ## verifica dell'esistenza pregressa del numero di telefono
        output = r.hget("phone_number", numero_telefono)
        if output == None:
            break

        print("Numero già registrato.")
    
    ## input della password
    password = input("Inserisci la tua nuova password: ")
    
    ## verifica se l'utente vuole uscire
    if password == "q":
        return False
    
    ## aggiunta delle chiavi all'hashmap Redis
    r.hset("users", nome_utente, password)
    r.hset(f"user:{nome_utente}", mapping={
        "password": password,
        "phone_number": numero_telefono,
        "friends": "[]"
    })

    return nome_utente

@schermata
def login(r: redis.Redis):
    print("Se vuoi uscire in qualunque momento, inserisci 'q'")

    ## inserimento del nome utente
    nome_utente = input("Inserisci il tuo nome utente: ")

    ## esci se l'utente inserisce "q"
    if nome_utente == "q":
        return False

    ## inserimento della password
    password = input("Inserisci la password: ")

    ## esci se l'utente inserisce "q"
    if password == "q":
        return False
    
    ## verifica della correttezza della password / esistenza dell'utente inserito
    actual_password = r.hget("users", nome_utente)

    if actual_password == password and actual_password != None :
        return nome_utente

@schermata
def logout(user: str|None):
    if user != None:
        decisione = input("Sei sicuro di voler effettuare il logout?\ny=Sì\nn=No\n")

        if decisione == "y":
            return None
        else:
            return user

@schermata
def aggiungi_contatto(r: redis.Redis, user):
    # @schermata
    def ricerca(r: redis.Redis, user: str):
        contatto = input('Inserisci il nome utente del contatto che desidere aggiungere\n: ')
        utenti = r.hkeys('users')
        
        corrispondenze = []
        for utente in utenti:
            if utente in contatto or contatto in utente:
                corrispondenze.append(utente)
                
            if utente == contatto:
                amici = json.loads(r.hget(f"user:{user}", "friends"))
                amici.append(contatto)
                r.hset(f"user:{user}", "friends", json.dumps(amici) )
                print(f"Aggiunto {contatto} come amico")
                
                return True
        
        for i, utente in enumerate(corrispondenze):
            print(f"{i+1}. {utente}")
        print('q. Quit')
        
        opzione = input('\nInserisci l\'indice dell\'utente da aggiungere\n: ')
        if opzione.lower() == 'q':
            return True
    
        try: 
            opzione = int(opzione)
            contatto = corrispondenze[opzione-1]
        except:
            return False
        
        amici = json.loads(r.hget(f"user:{user}", "friends"))
        amici.append(contatto)
        r.hset(f"user:{user}", "friends", json.dumps(amici) )
        print(f"Aggiunto {contatto} come amico")
                
        return True
        
        
    while True:
        if ricerca(r, user): break

if __name__ == "__main__":
    ## inizializzazione utente logged-in. Si potrebbe aggiungere una cache per memorizzarlo anche se si esce dall'esecuzione.
    user = None
    r = redis.Redis(
        host="localhost",
        port=8765,
        db=0,
        decode_responses=True
    )

    while True:
        output = menu_iniziale(r, user)
        input(output)

        if type(output) in [str, type(None)]:
            user = output
            continue
        
        if output:
            print('\nTerminando l\'esecuzione.')
            break