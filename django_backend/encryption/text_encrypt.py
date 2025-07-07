import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet


class Encryptor():
    def __init__(self):
        load_dotenv()
        self.key = os.getenv('ENCRYPTION_KEY')

    def encrypt_text(self, text):
            cipher = Fernet(self.key)
            encrypted_token = cipher.encrypt(bytes(text, 'utf-8'))
            return encrypted_token
        
    def decrypt_text(self, text):
        cipher = Fernet(self.key)
        if len(text) > 0:
            decrypted_token = cipher.decrypt(text)
            return decrypted_token
        return ""
    
