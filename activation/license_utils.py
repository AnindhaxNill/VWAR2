import os
import json
from datetime import datetime
from config import ACTIVATION_FILE
from activation.hwid import get_processor_info, get_motherboard_info
from cryptography.fernet import Fernet
import base64, hashlib

# def is_activated():
#     """
#     Return (True, None) if activated.
#     Return (False, reason) if not.
#     """
#     if not os.path.exists(ACTIVATION_FILE):
#         return False, "Activation file not found."

#     try:
#         with open(ACTIVATION_FILE, "r", encoding="utf-8") as f:
#             data = json.load(f)

#         valid_till = data.get("valid_till")
#         cpu = data.get("processor_id")
#         mobo = data.get("motherboard_id")

#         if not (valid_till and cpu and mobo):
#             return False, "Activation data is incomplete."

#         expiry = datetime.strptime(valid_till, "%Y-%m-%d %H:%M:%S")
#         if datetime.now() > expiry:
#             return False, "License expired."

#         current_cpu = get_processor_info()
#         current_mobo = get_motherboard_info()

#         if cpu != current_cpu or mobo != current_mobo:
#             return False, "Activation bound to another system."

#         return True, None

#     except Exception as e:
#         return False, f"Failed to validate activation: {e}"

def generate_fernet_key_from_string(secret_string):
    sha256 = hashlib.sha256(secret_string.encode()).digest()
    return base64.urlsafe_b64encode(sha256)

SECRET_KEY = generate_fernet_key_from_string("VWAR@BIFIN")
fernet = Fernet(SECRET_KEY)

def is_activated():
    """
    Return (True, None) if activated.
    Return (False, reason) if not.
    """
    if not os.path.exists(ACTIVATION_FILE):
        return False, "Activation file not found."

    try:
        # with open(ACTIVATION_FILE, "r", encoding="utf-8") as f:
        #     data = json.load(f)
        
        
        with open(ACTIVATION_FILE, "rb") as f:
            encrypted = f.read()
            
            decrypted = fernet.decrypt(encrypted)
            data = json.loads(decrypted.decode("utf-8"))
            
            # print("69 lincensse", data)

        valid_till = data.get("valid_till")
        cpu = data.get("processor_id")
        mobo = data.get("motherboard_id")

        if not (valid_till and cpu and mobo):
            return False, "Activation data is incomplete."

        # expiry = datetime.strptime(valid_till, "%Y-%m-%d %H:%M:%S")
        # if datetime.now() > expiry:
        #     return False, "License expired."
        
        created_at = data.get("created_at")

        if not created_at:
            return False, "Activation start date missing."

        try:
            start = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
            end = datetime.strptime(valid_till, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()

            if not (start <= now <= end):
                return False, "License has expired."

        except Exception as e:
            return False, f"Failed to parse license dates: {e}"


        current_cpu = get_processor_info()
        current_mobo = get_motherboard_info()

        if cpu != current_cpu or mobo != current_mobo:
            return False, "Activation bound to another system."

        return True, None

    except Exception as e:
        return False, f"Failed to validate activation: {e}"
