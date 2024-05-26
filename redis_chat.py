import pwinput
import os
from datetime import datetime
from database import Database
import time
import msvcrt
import threading
import cursor

def aggiorna_messaggi(active_user, contatto, db: Database, aggiorna: threading.Event, stop: threading.Event):
    while True:
        ultimo_accesso = db.get_ultimo_accesso(active_user, contatto)
        nuovi_messaggi = db.check_nuovi_messaggi(active_user, contatto, ultimo_accesso)
        
        if nuovi_messaggi and len(nuovi_messaggi) > 0:
            aggiorna.set()
            db.set_ultimo_accesso(active_user, contatto)

        if stop.is_set(): return

def schermata(f):
    def wrapper(*args, **kwargs):
        """Questa funzione pulisce il terminale e stampa delle informazioni:
        - Utente attivo
        - Notifiche ricevute (da aggiungere)"""
        self = args[0]
        
        if os.name == 'nt':
            # Per Windows
            os.system('cls')
        else:
            # Per Unix/Linux/macOS
            os.system('clear')
        
        if self.active_user:
            active_user_name = self.active_user if self.active_user is not None else "guest"
            print("Utente attivo:", active_user_name)

            contatti = self.db.get_contatti(self.active_user)
            nuovi_messaggi_da = []
            for contatto in contatti:
                ultimo_accesso = self.db.get_ultimo_accesso(self.active_user, contatto)
                if not ultimo_accesso:
                    continue

                nuovi_messaggi = self.db.check_nuovi_messaggi(self.active_user, contatto, ultimo_accesso)
                if nuovi_messaggi and len(nuovi_messaggi) > 0:
                    nuovi_messaggi_da.append(contatto)

            if nuovi_messaggi_da:
                print(f'Hai nuovi messaggi da {", ".join(nuovi_messaggi_da)}')
        else:
            print("Nessun utente attivo.")

        print()
        return f(*args, **kwargs)
    return wrapper

class Manager:
    def __init__(
        self,
        porta: str
    ):
        self.db = Database(porta)
        self.active_user = None
        # self.active_user = 'flavio'
        
    @schermata
    def menu_iniziale(self):
        
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
                input('Premi "invio" per continuare...')
    
    @schermata
    def non_disturbare(self):
        if self.active_user == None: return
                    
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

        input('\nPremi "invio" per continuare...')

    @schermata
    def menu_chat(self):

        contatti = self.db.get_contatti(self.active_user)
        
        # controllo esistenza di almeno un contatto
        if not contatti:
            print("Non hai ancora chat aperte. Aggiungi un contatto per iniziare una chat.")
            input('Premi "invio" per continuare...')
            return
        
        print("Se vuoi uscire in qualunque momento, inserisci 'q'\n")
        print("   n   |            nome              |    DnD    |  Nuovi mess.  ")
        print("------------------------------------------------------------------")

        
        # stampa di indice, utente e stato dnd per ogni contatto
        for i, utente in enumerate(contatti):
            
            ## calcolo dei messaggi non letti
            ultimo_accesso = self.db.get_ultimo_accesso(self.active_user, utente)
            nuovi_messaggi = 0
            if ultimo_accesso:
                nuovi_messaggi = len(self.db.check_nuovi_messaggi(self.active_user, utente, ultimo_accesso))
                    
            print(f"   {i+1}   "+f"|     {utente}"+" " * (25-len(utente))+("|     ●     |" if self.db.get_non_disturbare(utente) == "on" else "|     ○     |")+f"     n.{nuovi_messaggi}")        
        
        scelta = input("\nScelta: ")

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
    def mostra_chat(self, contatto, nuovo_messaggio):
        print (">> Chat con", contatto, "<<")
        print('- Lascia vuoto per uscire')     
        print('- Inserisci LOAD_MORE per caricare altri messaggi')
             
        print(f'\nScrivi: {nuovo_messaggio}⏴\n')
        
        # estrazione dei messaggi dal db
        messaggi = self.db.get_conversazione(self.active_user, contatto)
        messaggi = messaggi[0:25*self.load_more]
        
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
        self.load_more = 1
        self.db.set_ultimo_accesso(self.active_user, contatto)
        
        ## nasconde il cursore del terminale
        print('\033[?25l', end="")

        ## valori di shared memory utilizzati per aggiornare i messaggi e fermare l'esecuzione del thread
        aggiorna = threading.Event()
        stop = threading.Event()
        
        thread = threading.Thread(target=aggiorna_messaggi, args=(self.active_user, contatto, self.db, aggiorna, stop,), daemon=True)
        thread.start()

        while True:
            nuovo_messaggio = ''

            # stampa della chat
            self.mostra_chat(contatto, nuovo_messaggio)

            ## inserimento del messaggio
            while True:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    ## se premiamo "enter" -> esci
                    if key == b'\r':
                        break
                    
                    try:
                        ## se premiamo "cancel"/"delete" rimuoviamo l'ultima lettere del messaggio
                        if key == b'\x08': 
                            nuovo_messaggio = nuovo_messaggio[:-1]
                            
                        elif len(key) == 1: 
                            key = key.decode()
                            nuovo_messaggio += key
                        else:
                            raise Exception
                        
                        self.mostra_chat(contatto, nuovo_messaggio)
                        t = time.time()
                        
                    except: pass ## il carattere premuto non è decifrabile / non è valido
                    
                ## se ci sono nuovi messaggi -> aggiorna la schermata
                if aggiorna.is_set():
                    self.mostra_chat(contatto, nuovo_messaggio)
                    aggiorna.clear()

            # controllo messaggio vuoto per uscire
            if nuovo_messaggio == "":
                break
                
            ## caricamento dei messaggi
            ## essendo che la chat deve essere dall alto verso il basso con i messaggi più recenti in cima,
            ## per evitare che ogni volta che aggiorniamo i messaggi o l'input dell'utente il terminale venga
            ## spinto in fondo (a causa delle eccessive linee di messaggi)
            ## ho preimpostato il numero di messaggi da mostrare a 50 per evitare questo problema
            ## scrivendo LOAD_MORE nell'input aumentiamo questa cifra
            ## in modo da poter visionare anche i messaggi più vecchi
            if nuovo_messaggio == "LOAD_MORE":
                self.load_more += 1
                continue
            
            # disattivazione della DnD se l'utente che ce l'ha attiva invia un messaggio
            if self.db.get_non_disturbare(self.active_user) == "on":
                self.db.set_non_disturbare(self.active_user, "off") 

            ## controllo della modalità non disturbare
            non_disturbare = self.db.get_non_disturbare(contatto)
            if non_disturbare == 'on':
                print('\nLa persona con cui stai provando a comunicare ha la modalità non disturbare attiva!')
                input('Premi "invio" per continuare...')
            else:    
                t = time.time()
                nuovo_messaggio =  str(t) + ': ' + self.active_user + ': ' + nuovo_messaggio
                self.db.update_conversazione(self.active_user, contatto, nuovo_messaggio, t)
        
        stop.set()
        thread.join()
        
        print('\033[?25h', end="")

    @schermata
    def registrazione(self):
        
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
            password = pwinput.pwinput(prompt='Inserisci la password: ', mask='*')
            
            # verifica se l'utente vuole uscire
            if password == "q":
                return
            
            # verifica presenza di spazi
            if " " in password:
                print("La password non può contenere spazi")
                continue
            
            conferma_password = pwinput.pwinput(prompt='Conferma la password: ', mask='*')
            
            if conferma_password == password:        
                break

            print('Le password non corrispondono\n')
        
        # aggiunta delle chiavi all'hashmap Redis
        self.db.set_utente(nome_utente, password)
        self.db.set_numero_telefono(nome_utente, numero_telefono)
        self.active_user = nome_utente

        print(f'\nUtente "{nome_utente}" con numero di telefono "{numero_telefono}" registrato')
        input('Premi "invio" per continuare...')

    @schermata
    def login(self):
                
        print("Se vuoi uscire in qualunque momento, inserisci 'q'")

        # inserimento del nome utente
        nome_utente = input("Inserisci il tuo nome utente: ")

        # esci se l'utente inserisce "q"
        if nome_utente == "q":
            return
        
        # inserimento della password
        password = pwinput.pwinput(prompt='Inserisci la password: ', mask='*')

        # esci se l'utente inserisce "q"
        if password == "q":
            return
        
        # verifica della correttezza della password / esistenza dell'utente inserito
        output = self.db.get_pass_utente(nome_utente)

        if output == password and output != None :
            self.active_user = nome_utente
            print("Login effettuato")
            input('Premi "invio" per continuare...')
            return
        
        print ("Nome utente o password errati, riprovare")
        input('Premi "invio" per continuare.')
        return
    
    @schermata
    def logout(self):
        
        if self.active_user != None:

            decisione = input("Sei sicuro di voler effettuare il logout?\ny=Sì\nn=No\n\n: ")

            if decisione == "y":
                self.active_user = None
    
    @schermata
    def aggiungi_contatto(self):
        
        # inserimento da tastiera del nome da ricercare
        nome_utente_ricercato = input("Inserisci il nome utente del contatto da aggiungere: ")

        # controlli sull'input
        if nome_utente_ricercato == "":
            print("Non hai inserito un utente valido.")
            input('Premi "invio" per continuare.')
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
                input('Premi "invio" per continuare.')
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
            
        input('Premi "invio" per continuare.')

    @schermata
    def rimuovi_contatto(self):

        amicizie = self.db.get_contatti(self.active_user)
        if not amicizie:
            print("Non hai contatti.")
            input('Premi "invio" per continuare.')
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
            input('Premi "invio" per continuare.')
            return

        nome_utente = list(amicizie)[scelta - 1]
        self.db.del_contatto(self.active_user, nome_utente)
        
        print('Contatto rimosso con successo,')
        input('Premi "invio" per continuare.')

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
        if self.active_user == None:
            return
        
        print('''Scegli un'opzione: 
1- Aggiungi contatto 
2- Elimina contatto
3- Visualizza contatti
q- Torna al menù''')
        scelta = input("\nScelta:")

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
    