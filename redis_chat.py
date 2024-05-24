import redis
import os
from datetime import datetime
from database import Database
import time

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
        self,
        porta: str
    ):
        self.db = Database(porta)
        self.active_user = None

    @schermata
    def menu_iniziale(self):
        print("Utente attivo:", self.active_user if self.active_user != None else "guest", end='\n')
        print()
        
        ## LOGIN, CHAT E CONTATTI devono essere disonibili solo una volta avcer efettuto l'accesso
        print("""Scegli un'opzione:
1- Registrazione 
2- Login """)
        if self.active_user:
            print("""3- Logout
4- Chat
5- Contatti
6- Imposta modalità non disturbare""")

        print('q- Esci dal programma')
        
        scelta = input("\nScelta: ")

        match scelta:
            case "1":
                self.registrazione()
            case "2":
                self.login()
            case "3":
                self.logout()
            case "4":
                self.menu_chat()
            case "5":
                self.contatti()
            case "6":
                self.non_disturbare()
            case "q":
                exit(0)
            case _:
                print('\nScelta non valida,')
                input('Premi invio per continuare.')
    
    @schermata
    def non_disturbare(self):
        if self.active_user == None: return
        print("Utente attivo:", self.active_user if self.active_user != None else "guest", end='\n')
        print()
            
        modalita = self.db.get_non_disturbare(self.active_user)
        if modalita == None or modalita == 'off':
            print("Modalità non disturbare disattivata")

            decisione = input("Vuoi attivare la modalità? (y/n)\n:")

            if decisione == "y":
                self.db.set_non_disturbare(self.active_user, 'on')
        else:
            print("Modalità non disturbare attiva")

            decisione = input("Vuoi disattivare la modalità? (y/n)\n:")

            if decisione == "y":
                self.db.set_non_disturbare(self.active_user, 'off')

        input('\nPremi invio per continuare...')

    @schermata
    def menu_chat(self):
        print("Utente attivo:", self.active_user if self.active_user != None else "guest", end='\n')
        print()
        contatti = self.db.get_contatti(self.active_user)
        
        # controllo esistenza di almeno un contatto
        if not contatti:
            print("Non hai ancora chat aperte. Aggiungi un contatto per iniziare una chat.")
            input('Premi invio per continuare...')
            return
        
        print("Se vuoi uscire in qualunque momento, inserisci 'q'")
        
        for i, utente in enumerate(contatti):
            print(f"{i+1}. chat con {utente}")
        
        scelta = input("\nInserisci l'indice della chat da aprire: ")

        if scelta.lower() == "q":
            return
        
        try:
            scelta = int(scelta)
            if scelta < 1 or scelta > len(contatti):
                raise ValueError
        except ValueError:
            print('\nRisposta errata,')
            input('Premere invio per continuare...')
            return
        
        contatto = list(contatti)[scelta-1]
        self.chat(contatto)

    @schermata
    def mostra_chat(self, contatto):
                        
            # estrazione dei messaggi dal db
            messaggi = self.db.get_conversazione(self.active_user, contatto)
            
            # print nel caso in cui non ci siano ancora messaggi
            if not messaggi: 
                print('Sembra che al momento non siano presenti messaggi, manda un saluto al tuo contatto!')
            
            # print dei messaggi con timestamp
            else:
                for messaggio in messaggi:
                    messagio_split = messaggio.split(':') 
                    data = datetime.fromtimestamp(float(messagio_split[0]))
                    messaggio = messagio_split[1].replace(self.active_user, 'Io') + ':' + "".join(messagio_split[2:])
                    print(f'[{str(data).split(".")[0]}]{messaggio}')

    def chat(self, contatto):

        while True:

            # stampa della chat
            self.mostra_chat(contatto)

            # inserimento del messaggio
            nuovo_messaggio = input('\nScrivi (lascia vuoto per uscire): ')

            # controllo messaggio vuoto per uscire
            if nuovo_messaggio == "":
                break
            
            # disattivazione della DnD se l'utente che ce l'ha attiva invia un messaggio
            if self.db.get_non_disturbare(self.active_user) == "on":
                self.db.set_non_disturbare(self.active_user, "off") 

            ## controllo della modalità non disturbare
            non_disturbare = self.db.get_non_disturbare(contatto)
            if non_disturbare == 'on':
                print('\nLa persona con cui stai provando a comunicare ha la modalità non disturbare attiva!')
                input('Premi invio per continuare...')
            else:    
                t = time.time()
                # date = ":".join(str(datetime.fromtimestamp(t)).split(':')[:-1])
                
                nuovo_messaggio =  str(t) + ': ' + self.active_user + ': ' + nuovo_messaggio
                self.db.update_conversazione(self.active_user, contatto, nuovo_messaggio, t)

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
            
            # verifica presenza di spazi
            if " " in nome_utente:
                print("Il nome utente non può contenere spazi")
                continue

            # verifica sulla lunghezza minima e massima del nome utente
            lunghezza_nomeutente = len(nome_utente)
            if lunghezza_nomeutente < 3 or lunghezza_nomeutente > 20:
                print("Il nome utente deve avere una lunghezza compresa tra 3 e 20 (compresi)")
                continue

            # verifica dell'esistenza pregressa del nome utente
            if self.db.user_exists(nome_utente):
                print("Nome utente già esistente.")
                continue

            break
            
        # ciclo per inserimento corretto del numero di telefono
        while True:
            # ciclo per verifica della formattazione del numero di telefono    
            while True:
                numero_telefono = input("Inserisci il tuo numero di telefono: +")

                # verifica se l'utente vuole uscire
                if numero_telefono == "q":
                    return
                
                # verifica della lunghezza del numero
                lunghezza_numero = len(numero_telefono)    
                if lunghezza_numero < 12 or lunghezza_numero > 13:
                    print("Il numero di telefono deve avere 12/13 cifre (incluso il prefisso).")
                    continue 
                
                try:
                    # tentativo di casting a numero intero per verifica presenza caratteri non numerici
                    numero_telefono = int(numero_telefono)
                    break
                
                except ValueError:
                    print("Il numero di telefono contiene simboli oltre ai numeri.")

            # verifica dell'esistenza pregressa del numero di telefono
            if self.db.phonenumber_exists(numero_telefono):
                print("Numero già registrato.")
                continue

            break

        # ciclo per inserimento corretto della password
        while True:
            # input della password
            password = input("Inserisci la tua nuova password: ")
            
            # verifica se l'utente vuole uscire
            if password == "q":
                return
            
            # verifica presenza di spazi
            if " " in password:
                print("La password non può contenere spazi")
                continue
            
            break

        
        # aggiunta delle chiavi all'hashmap Redis
        self.db.set_utente(nome_utente, password)
        self.db.set_numero_telefono(nome_utente, numero_telefono)
        self.active_user = nome_utente

        print(f'\nUtente "{nome_utente}" con numero di telefono "{numero_telefono}" registrato')
        input("Premi invio per continuare...")

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
        output = self.db.get_pass_utente(nome_utente)

        if output == password and output != None :
            self.active_user = nome_utente
            print("Login effettuato")
            input("Premi 'invio' per continuare...")
            return
        
        print ("Nome utente o password errati, riprovare")
        input("Premi 'invio' per continuare...")
        return
        
        

    @schermata
    def logout(self):
        print("Utente attivo:", self.active_user if self.active_user != None else "guest")
        print()

        if self.active_user != None:

            decisione = input("Sei sicuro di voler effettuare il logout?\ny=Sì\nn=No\n\n: ")

            if decisione == "y":
                self.active_user = None
        
    @schermata
    def aggiungi_contatto(self):
        # TODO: l'utente non dovrebbe essere in grado di mandare la richiesta a se stesso
        
        print("Utente attivo:", self.active_user if self.active_user != None else "guest")
        print()

        # inserimento da tastiera del nome da ricercare
        nome_utente_ricercato = input("Inserisci il nome utente del contatto da aggiungere: ")

        # controlli sull'input
        if nome_utente_ricercato == "":
            print("Non hai inserito un utente valido.")
            input("Premi invio per continuare...")
            return

        # scannerizzo la stringa inserita dall'utente
        risultati_ricerca_utenti = self.db.get_utenti(nome_utente_ricercato)

        # rimozione dell'utente attivo (se stessi) dai risultati della ricerca
        if self.active_user in risultati_ricerca_utenti.keys():
            risultati_ricerca_utenti.pop(self.active_user)

        # calcolo numero di risultati
        numero_risultati = len(risultati_ricerca_utenti)
        
        # creazione oggetto enumerate per mostrare risultati
        risultati_contati = list(enumerate(risultati_ricerca_utenti.items()))

        # azioni in base ai risultati
        match numero_risultati:
            # caso in cui non ci sono risultati
            case 0:
                print("\nNessun risultato trovato")
                input("Premi 'invio' per continuare...")
                return

            # caso in cui c'è solo un risultato
            case 1:
                key, _ = risultati_contati[0][1]  # Estrai la chiave dalla lista
                output = self.db.set_contatto(self.active_user, key)
                nome_utente_ricercato = key

            # caso in cui ci sono più risultati
            case _:
                print("\nScegli uno dei risultati:")

                # stampa dei risultati
                [print(f"{i+1}-", key) for i, (key,_) in risultati_contati]

                # while per far scegliere all'utente il risultato senza errori
                while True:
                    try:
                        i = int(input("\n: ")) - 1

                        if i < 0 or i >= len(risultati_contati):
                            print("Scelta non valida, riprova.")
                            continue

                        key, _ = risultati_contati[i][1]  # Estrai la chiave dalla lista
                        output = self.db.set_contatto(self.active_user, key)

                        nome_utente_ricercato = key
                        break

                    except ValueError:
                        print("Numero non valido.")

        # stampa in base all'output del'add di redis
        if output == 0:
            print(f"\nL'utente {nome_utente_ricercato} è già nei contatti.")
        else: 
            print(f"\nUtente {key} aggiunto ai contatti.")
            
        input("Premi 'invio' per continuare...")

    @schermata
    def rimuovi_contatto(self):
        print("Utente attivo:", self.active_user if self.active_user != None else "guest", end='\n')
        print()

        amicizie = self.db.get_contatti(self.active_user)
        if not amicizie:
            print("Non hai contatti.")
            input("Premi invio per continuare...")
            return
        
        print(f"I tuoi contatti sono:")
        for i, amico in enumerate(amicizie):
            print(f'{i+1}. {amico}')
        print('q. Esci')
        
        scelta = input('\nDigita l\'indice del contatto da eliminare: ')
        if scelta.lower() == 'q':
            return
        
        try:
            scelta = int(scelta)
            if scelta < 1 or scelta > len(amicizie):
                raise ValueError
        except ValueError:
            print('\nScelta non valida')
            input('Premi invio per continuare...')
            return

        nome_utente = list(amicizie)[scelta - 1]
        self.db.del_contatto(self.active_user, nome_utente)
        
        print('Contatto rimosso con successo,')
        input('Premi invio per continuare...')

    @schermata
    def mostra_contatti(self):
        contatti = self.db.get_contatti(self.active_user)
        if not contatti:
            print("\nNon hai contatti.")
        else:
            print(f"\nI tuoi contatti sono:")
            for i, contatto in enumerate(contatti):
                print(f'{i+1}-',contatto)
        
        input("\nPremi 'invio' per continuare...")

    @schermata
    def contatti(self):
        print("Utente attivo:", self.active_user if self.active_user != None else "guest", end='\n')
        print()
        
        if self.active_user == None:
            return

        print('''Scegli un'opzione: 
1- Aggiungi contatto 
2- Elimina contatto
3- Visualizza contatti
q- Torna al menù''')
        scelta = input("\n:")

        match scelta:
            case "q":
                return
            case "1":
                self.aggiungi_contatto()
            case "2":
                self.rimuovi_contatto()
            case "3":
                self.mostra_contatti()


if __name__ == "__main__":
    manager = Manager(6379)   
    
    while True:
        manager.menu_iniziale()
    