import sys
import pwinput
import os
from datetime import datetime
from database import Database, Chiavi
import time
import msvcrt

def schermata(f):
    def wrapper(self, *args, **kwargs):
        """Questa funzione pulisce il terminale e stampa delle informazioni:
        - Utente attivo
        - Notifiche ricevute (da aggiungere)"""
        
        if os.name == 'nt':
            # Per Windows
            os.system('cls')
        else:
            # Per Unix/Linux/macOS
            os.system('clear')
        
        if self.active_user:
            active_user_name = self.active_user if self.active_user is not None else "guest"

            print("\nUtente attivo:", active_user_name, end='\n')

            self.gestisci_notifiche()

        else:
            print("Nessun utente attivo.")

        print()
        return f(self, *args, **kwargs)
    return wrapper

class Manager:
    def __init__(
        self,
        porta: str
    ):
        self.db = Database(porta)
        self.active_user = None

        # thread per le notifiche viene inizializzato quando viene fatto il login
        self.notification_agent_thread = None
        
        # inzializzazione e controllo presenza di notifiche
        self.notifiche_da = []
        self.chiavi = Chiavi()


    def gestisci_notifiche(self, messaggio=None):
        def mostra_notifica(lista_contatti):
            # Memorizzazione posizione cursore
            print("\033[s", end='')
            # Spostamento del cursore in alto a sinistra
            print("\033[1;1H", end='')

            # Stampa della notifica
            if lista_contatti:
                print(f"Hai delle nuove notifiche da: {', '.join(lista_contatti)}", end="")
            else:
                print("Nessuna nuova notifica.", end="")
            
            # Ritorno cursore alla posizione memorizzata prima
            print("\033[u", end='')
            
            # Flush dello stdout per forzare la stampa
            sys.stdout.flush()

        if messaggio:
            contatto = messaggio["data"]
            if contatto not in self.notifiche_da:
                self.notifiche_da.append(contatto)

        mostra_notifica(self.notifiche_da)

    @schermata
    def menu_iniziale(self):
        
        ## LOGIN, CHAT E CONTATTI devono essere disonibili solo una volta avcer efettuto l'accesso
        print("""Scegli un'opzione:
1- Registrazione 
2- Login """)
        if self.active_user:
            print("""3- Logout
4- Chat
5- Chat con messaggi effimeri
6- Contatti
7- Imposta modalità non disturbare""")

        print('q- Esci dal programma')
        
        scelta = input("\nScelta: ")

        if self.active_user != None:
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
                    self.menu_chat(effimeri=True)
                case "6":
                    self.contatti()
                case "7":
                    self.non_disturbare()
                case "q":
                    self.notification_agent_thread.stop()
                    exit(0)
                case _:
                    print('\nScelta non valida,')
                    input('Premi "invio" per continuare...')
            return

        if self.active_user == None:
            match scelta:
                case "1":
                    self.registrazione()
                case "2":
                    self.login()
                case "q":
                    self.notification_agent_thread.stop()
                    exit(0)
                case _:
                    print('\nScelta non valida,')
                    input('Premi "invio" per continuare...')
            return
    
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
    def menu_chat(self, effimeri=False):

        contatti = self.db.get_contatti(self.active_user)
        
        # controllo esistenza di almeno un contatto
        if not contatti:
            print("Non hai ancora chat aperte. Aggiungi un contatto per iniziare una chat.")
            input('Premi "invio" per continuare...')
            return
        
        print("Se vuoi uscire in qualunque momento, inserisci 'q'\n")
        
        if effimeri:
            print("   n   |            nome              |    DnD    ") 
            print("--------------------------------------------------")

        else:
            print("   n   |            nome              |    DnD    |  Nuovi mess.  ")
            print("------------------------------------------------------------------")

        
        # stampa di indice, utente e stato dnd per ogni contatto
        for i, utente in enumerate(contatti):
            
            if effimeri:
                print(f"   {i+1}   "+f"|     {utente}"+" " * (25-len(utente))+("|     ●     |" if self.db.get_non_disturbare(utente) == "on" else "|     ○     |"))
            else:        
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
        self.chat(contatto, effimeri)

    @schermata
    def mostra_chat(self, contatto, effimeri=False):
        
        print (">> Chat con", contatto, "<<")          
        
        # estrazione dei messaggi dal db
        if not effimeri:
            messaggi = self.db.get_conversazione(self.active_user, contatto)
        else:
            messaggi = self.db.get_conversazione_effimeri(self.active_user, contatto)
        
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

        print(f"\nScrivi (lascia vuoto per uscire): {self.nuovo_messaggio}", end="")

    def controlla_nuovi_messaggi(self):

        # estrazione di tutti i contatti dell'utente loggato
        contatti = self.db.get_contatti(self.active_user)

        # inizializzazione della lista di notifiche
        notifiche_da = []

        for contatto in contatti:
            ultimo_accesso = self.db.get_ultimo_accesso(self.active_user, contatto)
            if not ultimo_accesso:
                continue

            nuovi_messaggi = self.db.check_nuovi_messaggi(self.active_user, contatto, ultimo_accesso)
            if nuovi_messaggi and len(nuovi_messaggi) > 0:
                notifiche_da.append(contatto)

        return notifiche_da

    def chat(self, contatto, effimeri=False):

        # funzione da eseguire quando si riceve un messaggio dal contatto
        def azioni_ricezione(_):

            # ricarica chat
            self.mostra_chat(contatto, effimeri)

            # aggiornamento dell'accesso alla chat
            if not effimeri:
                self.db.set_ultimo_accesso(self.active_user, contatto)

            # aggiornamento lista notifiche
            self.notifiche_da = self.controlla_nuovi_messaggi()
        
        def azioni_effimeri(message):
            key = message['data']
            k = self.chiavi.messaggio_effimero(self.active_user, contatto).split(':')[:-1]
            
            if k != key.split(':')[:-1]: 
                ## se il messaggio cancellato non fa parte di questa chat ignoralo
                ## c'è bisogno di questo check perchè redis invia una notifica per TUTTI i messaggi cancellati
                ## se lo aggiornassimo ogni volta che un messaggio di qualsiasi utente si cancella le perf. calerebbero
                return 
            
            # ricarica chat
            self.mostra_chat(contatto, effimeri)

            # aggiornamento lista notifiche
            self.notifiche_da = self.controlla_nuovi_messaggi()
        

        
        # creazione del thread a partire dalla connessione pubsub al canale della chat
        pubsub = self.db.get_pubsub(self.active_user, azioni_ricezione, contatto, effimeri)
        pubsub_thread = pubsub.run_in_thread(sleep_time=0.1)

        if effimeri:
            pubsub_cancellazione = self.db.get_pubsub_messaggi_effimeri(self.active_user, azioni_effimeri, contatto)
            pubsub_cancellazione_thread = pubsub_cancellazione.run_in_thread(sleep_time=0.1)

        while True:
            # aggiornamento dell'accesso alla chat
            if not effimeri:
                self.db.set_ultimo_accesso(self.active_user, contatto)

            # aggiornamento lista notifiche
            self.notifiche_da = self.controlla_nuovi_messaggi()

            # inserimento del messaggio
            self.nuovo_messaggio = ''

            # stampa della chat
            self.mostra_chat(contatto, effimeri)

            ## inserimento del messaggio
            while True:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    ## se premiamo "enter" -> esci
                    if key == b'\r':
                        break
                    
                    ## se premiamo "cancel"/"delete" rimuoviamo l'ultima lettere del messaggio
                    elif key == b'\x08': 
                        self.nuovo_messaggio = self.nuovo_messaggio[:-1]
                        
                    elif len(key) == 1: 
                        try:
                            key = key.decode()
                            self.nuovo_messaggio += key
                        except: pass ## il carattere premuto non è decifrabile / non è valido
                    
                    else: continue
                    
                    self.mostra_chat(contatto, effimeri)

            # controllo messaggio vuoto per uscire
            if self.nuovo_messaggio == "":

                # terminazione del thread di ricezione messaggi
                pubsub_thread.stop()
                if effimeri: 
                    pubsub_cancellazione_thread.stop()
                break
            
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
                
                self.nuovo_messaggio =  str(t) + ': ' + self.active_user + ': ' + self.nuovo_messaggio
                
                if not effimeri:
                    self.db.update_conversazione(self.active_user, contatto, self.nuovo_messaggio, t)
                else:
                    self.db.update_conversazione_effimeri(self.active_user, contatto, self.nuovo_messaggio, t)

                # publish per aggiornare la chat live
                self.db.notify_channel(contatto, self.active_user, effimeri=effimeri)

                # publish per inviare notifica
                self.db.notify_channel(contatto, message=self.active_user, effimeri=effimeri)
            
    
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

        print(f'\nUtente "{nome_utente}" con numero di telefono "{numero_telefono}" registrato. Per cominciare a chattare esegui il login.')
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

            # arresto del vecchio thread per ricevere le notifiche
            if self.active_user != None:
                self.notification_agent_thread.stop()
            
            # impostazione del nuovo utente
            self.active_user = nome_utente

             # creazione del thread per ricevere le notifiche
            notification_agent = self.db.get_pubsub(self.active_user, self.gestisci_notifiche)

            # ricreazione del thread per ricevere le notifiche
            self.notification_agent_thread = notification_agent.run_in_thread(sleep_time=0.1)

            # controllo di esistenza di nuove notifiche
            self.notifiche_da = self.controlla_nuovi_messaggi()

            print("Login effettuato")
            input('Premi "invio" per continuare...')
            return
        
        print ("Nome utente o password errati, riprovare")
        input('Premi "invio" per continuare.')
        return
    
    @schermata
    def logout(self):
        
        decisione = input("Sei sicuro di voler effettuare il logout?\ny=Sì\nn=No\n\n: ")

        if decisione == "y":
            # arresto del thread delle notifiche
            self.notification_agent_thread.stop()

            # rimozione dell'utente attivo
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
    