from fastapi import FastAPI

from api.benchmark import router as benchmark_router
from api.evaluation import router as evaluation_router
from api.metadata import router as metadata_router
from db.session import init_db

app = FastAPI(title="T2SQL Benchmark Server")


@app.on_event("startup")
async def on_startup():
    await init_db()


app.include_router(benchmark_router)
app.include_router(metadata_router)
app.include_router(evaluation_router)


@app.get("/")
async def root():
    return {"message": "T2SQL Benchmark Server is running"}
