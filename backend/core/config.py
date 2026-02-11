import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    BYBIT_API_KEY: str = os.getenv("BYBIT_API_KEY", "")
    BYBIT_API_SECRET: str = os.getenv("BYBIT_API_SECRET", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./crypto_mentor.db")
    MOCK_MODE: bool = os.getenv("MOCK_MODE", "true").lower() == "true"
    DEFAULT_PAIR: str = os.getenv("DEFAULT_PAIR", "BTC/USDT")
    DEFAULT_TIMEFRAME: str = os.getenv("DEFAULT_TIMEFRAME", "15m")
    INITIAL_BALANCE: float = float(os.getenv("INITIAL_BALANCE", "10000"))

    @property
    def is_bybit_configured(self) -> bool:
        return bool(self.BYBIT_API_KEY and self.BYBIT_API_SECRET)


settings = Settings()
