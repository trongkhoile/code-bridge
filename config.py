import os
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "changeme")

MT5_LOGIN = int(os.getenv("MT5_LOGIN", 0))
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
MT5_SERVER = os.getenv("MT5_SERVER", "")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

DEFAULT_LOT = float(os.getenv("DEFAULT_LOT", 0.01))
MAGIC_NUMBER = int(os.getenv("MAGIC_NUMBER", 20240101))
