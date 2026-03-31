import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

DB_USER_DW = os.getenv("DB_USER_DW")
DB_PASSWORD_DW = os.getenv("DB_PASSWORD_DW")
DB_HOST_DW = os.getenv("DB_HOST_DW")
DB_PORT_DW = os.getenv("DB_PORT_DW")
DB_NAME_DW = os.getenv("DB_NAME_DW")

DB_USER_GEOCOM = os.getenv("DB_USER_GEOCOM")
DB_PASSWORD_GEOCOM = os.getenv("DB_PASSWORD_GEOCOM")
DB_HOST_GEOCOM = os.getenv("DB_HOST_GEOCOM")
DB_PORT_GEOCOM = os.getenv("DB_PORT_GEOCOM")
DB_NAME_GEOCOM = os.getenv("DB_NAME_GEOCOM")

DB_USER_GEOCOM_QA = os.getenv("DB_USER_GEOCOM_QA")
DB_PASSWORD_GEOCOM_QA = os.getenv("DB_PASSWORD_GEOCOM_QA")
DB_HOST_GEOCOM_QA = os.getenv("DB_HOST_GEOCOM_QA")
DB_PORT_GEOCOM_QA = os.getenv("DB_PORT_GEOCOM_QA")
DB_NAME_GEOCOM_QA = os.getenv("DB_NAME_GEOCOM_QA")

# Credenciales de Base de Datos - Tablet/MySQL (spr_new)
DB_SPR_USER = os.getenv("DB_SPR_USER")
DB_SPR_PASS = os.getenv("DB_SPR_PASS")
DB_SPR_HOST = os.getenv("DB_SPR_HOST")
DB_SPR_PORT = os.getenv("DB_SPR_PORT", "3306")
DB_SPR_NAME = os.getenv("DB_SPR_NAME", "tablet")

DB_URL_DW = f"mssql+pyodbc://{DB_USER_DW}:{DB_PASSWORD_DW}@{DB_HOST_DW}:{DB_PORT_DW}/{DB_NAME_DW}?driver=ODBC+Driver+17+for+SQL+Server"
DB_URL_GEOCOM = f"mssql+pyodbc://{DB_USER_GEOCOM}:{DB_PASSWORD_GEOCOM}@{DB_HOST_GEOCOM}:{DB_PORT_GEOCOM}/{DB_NAME_GEOCOM}?driver=ODBC+Driver+17+for+SQL+Server"
DB_URL_GEOCOM_QA = f"mssql+pyodbc://{DB_USER_GEOCOM_QA}:{DB_PASSWORD_GEOCOM_QA}@{DB_HOST_GEOCOM_QA}:{DB_PORT_GEOCOM_QA}/{DB_NAME_GEOCOM_QA}?driver=ODBC+Driver+17+for+SQL+Server"
DB_URL_SPR = f"mysql+pymysql://{DB_SPR_USER}:{DB_SPR_PASS}@{DB_SPR_HOST}:{DB_SPR_PORT}/{DB_SPR_NAME}"

# Configuración SMTP para envío de correos
class Settings:
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

settings = Settings()

# Destinatarios de correos de reporte
DESTINATARIOS = ['samuel.prado@castano.cl']
