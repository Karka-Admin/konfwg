from pydantic_settings import BaseSettings

class Configuration(BaseSettings):
    BASE_URL: str
    DB_PATH: str
    QR_PATH: str
    DEFAULT_TTL: int = 180
    DEFAULT_HITS: int = 1
    
    class Config:
        env_file = "/etc/konfwg/konfwg.conf"

configuration = Configuration()