from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class QueryRequest(BaseModel):
    database: str
    query: str


@app.post("/")
async def generate_sql(request: QueryRequest):
    # Always return a valid SQL that is likely to fail the exact match but run successfully
    # Or we can return a syntax error to see if it handles it.
    # The user asked for "Always return the same query".
    return {"sql": "SELECT 1;"}
