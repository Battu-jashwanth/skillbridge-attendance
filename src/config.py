from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/skillbridge")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
MONITORING_API_KEY = os.getenv("MONITORING_API_KEY", "sk-monitor-hardcoded-key-for-testing")
MONITORING_TOKEN_EXPIRE_MINUTES = int(os.getenv("MONITORING_TOKEN_EXPIRE_MINUTES", "60"))
