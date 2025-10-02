import json
import requests
import bcrypt
from datetime import datetime

SUPABASE_URL = "https://auhwzjqzyzrqjgfkuatb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1aHd6anF6eXpycWpnZmt1YXRiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQyNzc2ODIsImV4cCI6MjA1OTg1MzY4Mn0.BrKQYBC4mWXha4zfrNvohOMLAdmZTN0SbT-QnDaEW98"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

class SupabaseDB:
    TABLE_NAME = "historia"

    @staticmethod
    def validar_login(usuario, clave):
        try:
            url = f"{SUPABASE_URL}/rest/v1/{SupabaseDB.TABLE_NAME}?usuario=eq.{usuario}&select=*"
            response = requests.get(url, headers=HEADERS)
            if response.status_code != 200:
                print("Error al obtener usuario:", response.status_code)
                return None

            data = response.json()
            if not data:
                print("Usuario no encontrado.")
                return None

            hashed_clave = data[0]['clave']
            if bcrypt.checkpw(clave.encode('utf-8'), hashed_clave.encode('utf-8')):
                return data[0]
            else:
                print("Contraseña incorrecta.")
                return None
        except Exception as e:
            print(f"Error en validar_login: {e}")
            return None

    @staticmethod
    def registrar_usuario(usuario, clave, fecha_nacimiento):
        try:
            if not fecha_nacimiento:
                raise ValueError("La fecha de nacimiento es obligatoria")
                
            url = f"{SUPABASE_URL}/rest/v1/{SupabaseDB.TABLE_NAME}"
            hashed = bcrypt.hashpw(clave.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            payload = {
                "usuario": usuario,
                "clave": hashed,
                "reto": 0,
                "fecha": fecha_nacimiento
            }
            response = requests.post(url, json=payload, headers=HEADERS)
            print("Registro:", response.status_code, response.text)
            return response.status_code == 201
        except Exception as e:
            print(f"Error en registrar_usuario: {e}")
            return False

    @staticmethod
    def recuperar_usuario(usuario):
        try:
            url = f"{SUPABASE_URL}/rest/v1/{SupabaseDB.TABLE_NAME}?usuario=eq.{usuario}&select=*"
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 200:
                data = response.json()
                return data[0] if data else None
            return None
        except Exception as e:
            print(f"Error en recuperar_usuario: {e}")
            return None

    @staticmethod
    def guardar_reto(usuario, reto):
        try:
            url = f"{SUPABASE_URL}/rest/v1/{SupabaseDB.TABLE_NAME}?usuario=eq.{usuario}"
            payload = {
                "reto": reto,
                "fecha": datetime.now().isoformat()
            }
            response = requests.patch(url, json=payload, headers=HEADERS)
            return response.status_code == 204
        except Exception as e:
            print(f"Error en guardar_reto: {e}")
            return False

    @staticmethod
    def actualizar_clave(usuario, nueva_clave):
        try:
            hashed = bcrypt.hashpw(nueva_clave.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            url = f"{SUPABASE_URL}/rest/v1/{SupabaseDB.TABLE_NAME}?usuario=eq.{usuario}"
            payload = {
                "clave": hashed
            }
            response = requests.patch(url, json=payload, headers=HEADERS)
            return response.status_code == 204
        except Exception as e:
            print(f"Error en actualizar_clave: {e}")
            return False

    @staticmethod
    def obtener_todos_los_usuarios():
        try:
            url = f"{SUPABASE_URL}/rest/v1/{SupabaseDB.TABLE_NAME}?select=usuario,reto&order=reto.desc"
            response = requests.get(url, headers=HEADERS)
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"Error en obtener_todos_los_usuarios: {e}")
            return []
        
    @staticmethod
    def get_user_reto(user_id):
        try:
            url = f"{SUPABASE_URL}/rest/v1/{SupabaseDB.TABLE_NAME}?id=eq.{user_id}&select=reto"
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 200:
                data = response.json()
                return data[0]['reto'] if data else None
            return None
        except Exception as e:
            print(f"Error in get_user_reto: {e}")
            return None

    @staticmethod
    def update_user_reto(user_id, reto_data):
        try:
            url = f"{SUPABASE_URL}/rest/v1/{SupabaseDB.TABLE_NAME}?id=eq.{user_id}"
            payload = {
                "reto": reto_data
            }
            response = requests.patch(url, json=payload, headers=HEADERS)
            return response.status_code == 204
        except Exception as e:
            print(f"Error in update_user_reto: {e}")
            return False

    @staticmethod
    def get_top_streaks(limit=10):
        url = f"{SUPABASE_URL}/rest/v1/{SupabaseDB.TABLE_NAME}?select=usuario,reto&order=reto->streak.desc&limit={limit}"
        response = requests.get(url, headers=HEADERS)

        if not response.ok:
            print("Error obteniendo ranking:", response.text)
            return []

        datos = response.json()
        resultado = []

        for item in datos:
            usuario = item.get("usuario", "Desconocido")
            reto = item.get("reto", {})

            # Asegurar que 'reto' sea un diccionario válido
            if isinstance(reto, str):
                try:
                    reto = json.loads(reto)
                except json.JSONDecodeError:
                    reto = {}

            # Si reto es un número (backward compatibility)
            if isinstance(reto, (int, float)):
                reto = {'streak': int(reto)}

            streak = reto.get("streak", 0)
            resultado.append({"usuario": usuario, "streak": streak})

        return resultado


db = SupabaseDB()