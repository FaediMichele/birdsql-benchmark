from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class QueryRequest(BaseModel):
    database: str
    query: str


class QueryResponse(BaseModel):
    sql: str


@app.post("/", response_model=QueryResponse)
async def generate_sql(request: QueryRequest):
    return QueryResponse(sql="SELECT 1;")
