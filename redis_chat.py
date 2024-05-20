import redis
import os

# wrapper per le differenti schermate
def schermata(funzione):
    def wrapper(*args, **kwargs):
        if os.name == 'nt':
            # Per Windows
            os.system('cls')
        else:
            # Per Unix/Linux/macOS
            os.system('clear')
        return funzione(*args, **kwargs)
    return wrapper

class Manager:
    def __init__(
        self
    ):
        self.r = redis.Redis(
            host="localhost",
            port=8765,
            db=0,
            decode_responses=True
        )
        self.active_user = None
    

    @schermata
    def menu_iniziale(self):
        print("Utente attivo:", self.active_user if self.active_user != None else "guest", end='\n')
        print()
        
        print("""Scegli un'opzione:
1- Registrazione 
2- Login 
3- Logout
4- Chat
5- Contatti
q- Esci dal programma""")
        
        scelta = input("\nScelta: ")

        match scelta:
            case "1":
                self.registrazione()
            case "2":
                self.login()
            case "3":
                self.logout()
            case "4":
                ...
            case "5":
                self.contatti()
            case "q":
                exit(0)
            case _:
                pass

    @schermata
    def registrazione(self):
        print("Utente attivo:", self.active_user if self.active_user != None else "guest", end='\n')
        print()
        
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
            output = self.r.hget("users", nome_utente)
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
            output = self.r.hget("phone_number", numero_telefono)
            if output == None:
                break

            print("Numero già registrato.")

        
        # input della password
        password = input("Inserisci la tua nuova password: ")
        
        # verifica se l'utente vuole uscire
        if password == "q":
            return
        
        # aggiunta delle chiavi all'hashmap Redis
        self.r.hset("users", nome_utente, password)
        self.r.hset("phone_number", numero_telefono, nome_utente)

        self.active_user = nome_utente

    @schermata
    def login(self):
        print("Utente attivo:", self.active_user if self.active_user != None else "guest", end='\n')
        print()
        
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
        output = self.r.hget("users", nome_utente)

        if output == password and output != None :
            self.active_user = nome_utente

    @schermata
    def logout(self):
        print("Utente attivo:", self.active_user if self.active_user != None else "guest")
        print()

        if self.active_user != None:

            decisione = input("\nSei sicuro di voler effettuare il logout?\ny=Sì\nn=No\n")

            if decisione == "y":
                self.active_user = None
        

    def aggiungi_contatto(self):
        # print("Utente attivo:", self.active_user if self.active_user != None else "guest", end='\n')

        # inserimento da tastiera del nome da ricercare
        nome_utente_ricercato = input("Inserisci il nome utente del contatto da aggiungere: ")

        # scannerizzo la stringa inserita dall'utente
        _, keys = self.r.hscan("users", cursor=0, match=f'{nome_utente_ricercato}*', count = 10)

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
                output = self.r.sadd(f"user:{self.active_user}:contatti", key)
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
                        output = self.r.sadd(f"user:{self.active_user}:contatti", key)

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
    def rimuovi_contatto(self):
        print("Utente attivo:", self.active_user if self.active_user != None else "guest", end='\n')
        print()

        amicizie = self.r.smembers(f"user:{self.active_user}:contatti")
        for i, amico in enumerate(amicizie):
            print(f'{i+1}. {amico}')
        
        scelta = input(': ')
        
        try:
            scelta = int(scelta)
            if scelta < 1 or scelta > len(amicizie):
                raise ValueError
        except ValueError:
            print('Scelta non valida')
            return

        nome_utente = list(amicizie)[scelta - 1]
        self.r.srem(f"user:{self.active_user}:contatti", nome_utente)
        
    @schermata
    def contatti(self):
        print("Utente attivo:", self.active_user if self.active_user != None else "guest", end='\n')
        print()
        
        if self.active_user == None:
            return

        scelta = input("Scegli un'opzione: \n1- Aggiungi contatto \n2- Elimina contatto\n3- Visualizza contatti\nq- Torna al menù\n:")

        match scelta:
            case "q":
                return
            case "1":
                self.aggiungi_contatto()
            case "2":
                self.rimuovi_contatto()
                # pass

if __name__ == "__main__":
    manager = Manager()   
    
    while True:
        manager.menu_iniziale()
    