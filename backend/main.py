import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.db import init_db
from backend.api.routes import router
from backend.api.websocket import ws_router
from backend.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    print(f"CryptoMentor started | Mock mode: {settings.MOCK_MODE}")
    print(f"Default pair: {settings.DEFAULT_PAIR} | Timeframe: {settings.DEFAULT_TIMEFRAME}")

    # Start the bot loop in background
    from backend.core.bot import trading_bot
    bot_task = asyncio.create_task(trading_bot.run())

    yield

    # Shutdown
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass
    print("CryptoMentor stopped")


app = FastAPI(
    title="CryptoMentor",
    description="Educational Paper Trading Bot — Belajar trading dengan bot yang explain setiap keputusan",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(ws_router)


@app.get("/")
async def root():
    return {
        "name": "CryptoMentor",
        "status": "running",
        "mock_mode": settings.MOCK_MODE,
        "pair": settings.DEFAULT_PAIR,
    }
