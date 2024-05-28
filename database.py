import redis
import time
from uuid import uuid1

class Database:
    """Questa classe è realizzata per raggruppare le funzioni che interagiscono con il database Redis e i valori delle chiavi"""
    def __init__(
        self,
        porta: str = 6379,
    ):

        self.redis = redis.Redis(
            host='127.0.0.1',
            port=porta,
            decode_responses=True
        )
        
        self.redis.config_set('notify-keyspace-events', 'Ex')
        self.chiavi = Chiavi()
        
    def user_exists(self, utente):
        return self.redis.hexists("users", utente)

    def phonenumber_exists(self, phone_number):
        return self.redis.hexists("phone_numbers", phone_number)

    def set_utente(
        self,
        username: str,
        password: str,
    ): 
        """Registra un utente nel database"""
        self.redis.hset(
            self.chiavi.utenti,
            username,
            password
        )
    
    def get_pass_utente(self, utente):
        """Ritorna/Verifica la password di un utente,
Ritorna None se esso non esiste"""
        return self.redis.hget(self.chiavi.utenti, utente)
    
    def get_utenti(self, utente, quantità=10):
        """Ritorna una lista di n (quantità) nomi utente che matchano l'utente inserito"""
        _, keys = self.redis.hscan(
            self.chiavi.utenti, 
            cursor=0, 
            match=f'{utente}*', 
            count = quantità
        )
        return keys
    
    def set_numero_telefono(self, username, numero_telefono):
        """Registra un numero di telefono nel database"""
        self.redis.hset(
            self.chiavi.numeri_telefono,
            numero_telefono,
            username
        )
        
    def get_numero_telefono(self, phone_number):
        """Ritorna/Verifica l'esistenza di un numero di telefono"""
        return self.redis.hget(self.chiavi.numeri_telefono, phone_number)
    
    def get_contatti(self, utente):
        """Ritorna tutti i contatti di un utente"""
        return self.redis.zrange(self.chiavi.utente_amici(utente), 0, -1, desc=True)
    
    # def get_contatto(self, utente, contatto):
    #     """Ritorna/Verifica l'esistenza di un contatto"""
    #     return self.redis.hget(self.chiavi.utente_amici(utente), contatto)
    
    def set_contatto(self, utente, contatto):
        """Aggiunge un contatto ad un utente"""
        self.redis.zadd(
            self.chiavi.utente_amici(utente),
            {contatto: 0},
        )
        
        return self.redis.zadd(
            self.chiavi.utente_amici(contatto),
            {utente: 0},
        )
    
    def del_contatto(self, utente, contatto):
        """Elimina un contatto ad un utente"""
        return self.redis.srem(
            self.chiavi.utente_amici(utente),
            contatto,
        )
    
    def set_non_disturbare(self, utente, valore):
        """Imposta il valore che determina la modalità non disturbare (on/off)"""
        self.redis.set(self.chiavi.utente_non_disturbare(utente), valore)
    
    def get_non_disturbare(self, utente):
        """Ritorna il valore che determina la modalità non disturbare (on/off)"""
        return self.redis.get(self.chiavi.utente_non_disturbare(utente))
    
    def get_conversazione(self, utente, contatto):
        """Ritorna tutti i messaggi di una chat"""
        return self.redis.zrange(self.chiavi.conversazione(utente, contatto), 0, -1)

    def update_conversazione(self, utente, contatto, messaggio, score):
        """Aggiunge un messaggio alla chat"""
        self.redis.zadd(
            self.chiavi.conversazione(utente, contatto),
            {messaggio: score}
        )
        
        self.redis.zadd(
            self.chiavi.utente_amici(contatto),
            {utente: score}
        )
    
    def get_conversazione_effimeri(self, utente, contatto):
        """Ritorna tutti i messaggi di una chat negli ultimi 60sec"""
        
        ## id dei messaggi inviati/ricevuti negli ultimi 60sec
        id_messagi = self.redis.zrangebyscore(
            self.chiavi.conversazione_effimeri(utente, contatto), 
            time.time()-59, 
            time.time()
        )
        
        ## testo dei messaggi
        messaggi = []
        for id_messagio in id_messagi:
            messaggi.append(
                self.redis.get(id_messagio)
            )
        
        return messaggi

    def update_conversazione_effimeri(self, utente, contatto, messaggio, score):
        """Aggiunge un messaggio alla chat effimeri"""
        id_messaggio = self.chiavi.messaggio_effimero(utente, contatto)
        
        ## aggiunge id del messaggio alla lista
        self.redis.zadd(
            self.chiavi.conversazione_effimeri(utente, contatto),
            {id_messaggio: score}
        )
        
        ## aggiunge il messaggio sotto il suo id
        self.redis.set(
            id_messaggio,
            messaggio,
            ex=60    
        )
    
    def get_pubsub(self, utente, funzione, contatto=None, effimeri=False):

        pubsub = self.redis.pubsub()
        if not effimeri:
            pubsub.psubscribe(**{self.chiavi.canale(utente, contatto): funzione})
        else:
            pubsub.psubscribe(**{self.chiavi.canale_effimeri(utente, contatto): funzione})
        return pubsub

    def get_pubsub_messaggi_effimeri(self, utente, funzione, contatto=None):
        pubsub = self.redis.pubsub()
        pubsub.psubscribe(**{'__keyevent@0__:expired': funzione})

        return pubsub
    
    def notify_channel(self, contatto, utente=None, message="", effimeri=False):
        if not effimeri:
            self.redis.publish(self.chiavi.canale(contatto, utente), message)
        else:
            self.redis.publish(self.chiavi.canale_effimeri(contatto, utente), message)
    
    def set_ultimo_accesso(self, utente, contatto):
        """Aggiorna l'ultimo accesso di un utente ad una determinata chat"""
        self.redis.set(
            self.chiavi.utente_ultimo_accesso_chat(utente, contatto),
            time.time()
        )
    
    def get_ultimo_accesso(self, utente, contatto):
        return self.redis.get(
            self.chiavi.utente_ultimo_accesso_chat(utente, contatto)
        )
    
    def check_nuovi_messaggi(self, utente, contatto, ultimo_accesso: float):
        return self.redis.zrangebyscore(
            self.chiavi.conversazione(utente, contatto),
            ultimo_accesso,
            time.time()
        )
    
        
class Chiavi:
    def __init__(self):
        self.utenti = 'users:passwords' ## per salvare la password di ogni utente (usato per verificare l'esistenza di un utente e la correttezza della password)
        self.numeri_telefono = 'users:phone_numbers' ## per salvare i numeri telefonici di ogni utente (usato per verificare l'esistenza di un numero di telefono)
        self.utente_amici = lambda id_utente: f'user:{id_utente}:friends' ## per salvare gli utenti che fanno parte dei contatti
        self.utente_non_disturbare = lambda id_utente: f'user:{id_utente}:do_not_disturb' ## per salvare gli utenti che non vogliono ricevere notifiche
        self.utente_ultimo_accesso_chat = lambda id_utente, contatto: f'user:{id_utente}:last_acces_to_chat:{sorted([id_utente, contatto])[0]}:{sorted([id_utente, contatto])[1]}'
        self.conversazione = lambda id_utente1, id_utente2: f'chat:{sorted([id_utente1, id_utente2])[0]}:{sorted([id_utente1, id_utente2])[1]}' ## per salvare i messaggi di una chat
        self.canale = lambda id_utente1, id_utente2: f'channel:{id_utente1}:{id_utente2}'
        self.conversazione_effimeri = lambda id_utente1, id_utente2: f'chat:{sorted([id_utente1, id_utente2])[0]}:{sorted([id_utente1, id_utente2])[1]}:messaggi_effimeri' ## per salvare i messaggi di una chat a tempo
        self.messaggio_effimero = lambda id_utente1, id_utente2: f'chat:{sorted([id_utente1, id_utente2])[0]}:{sorted([id_utente1, id_utente2])[1]}:messaggio_effimero:{uuid1()}'
        self.canale_effimeri = lambda id_utente1, id_utente2: f'channel:{id_utente1}:{id_utente2}:effimeri'
        self.canale_effimeri_cancellazione = lambda id_utente1, id_utente2: f'channel:{id_utente1}:{id_utente2}:delete_effimeri'