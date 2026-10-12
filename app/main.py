from fastapi import FastAPI

from app.api.routes.transfers import router as transfer_router

app = FastAPI()
app.include_router(transfer_router)
