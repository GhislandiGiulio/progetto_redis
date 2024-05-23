import redis
from uuid import uuid1

class Database:
    """Questa classe è realizzata per raggruppare le funzioni che interagiscono con il database Redis e i valori delle chiavi"""
    def __init__(
        self,
        porta: str
    ):
        self.redis = redis.Redis(
            port=porta,
            decode_responses=True
        )
        
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
        return self.redis.smembers(self.chiavi.utente_amici(utente))
    
    def get_contatto(self, utente, contatto):
        """Ritorna/Verifica l'esistenza di un contatto"""
        return self.redis.hget(self.chiavi.utente_amici(utente), contatto)
    
    def set_contatto(self, utente, contatto):
        """Aggiunge un contatto ad un utente"""
        self.redis.sadd(
            self.chiavi.utente_amici(utente),
            contatto,
        )
        
        return self.redis.sadd(
            self.chiavi.utente_amici(contatto),
            utente,
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

    def add_conversazione(self, utente, contatto, messaggio, score):
        """Aggiunge un messaggio alla chat"""
        self.redis.zadd(
            self.chiavi.conversazione(utente, contatto),
            {messaggio: score}
        )
        
class Chiavi:
    def __init__(self):
        self.utenti = 'users' ## per salvare la password di ogni utente (usato per verificare l'esistenza di un utente e la correttezza della password)
        self.numeri_telefono = 'phone_numbers' ## per salvare i numeri telefonici di ogni utente (usato per verificare l'esistenza di un numero di telefono)
        self.utente_amici = lambda id_utente: f'user:{id_utente}:friends' ## per salvare gli utenti che fanno parte dei contatti
        self.utente_non_disturbare = lambda id_utente: f'user:{id_utente}:do_not_disturb' ## per salvare gli utenti che non vogliono ricevere notifiche
        self.conversazione = lambda id_utente1, id_utente2: f'chat:{sorted([id_utente1, id_utente2])[0]}:{sorted([id_utente1, id_utente2])[1]}' ## per salvare i messaggi di una chat