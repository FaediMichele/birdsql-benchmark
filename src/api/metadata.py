from fastapi import APIRouter, HTTPException

from models.schemas import DatabaseMetadata
from services import metadata_service

router = APIRouter(prefix="/metadata", tags=["metadata"])


@router.get("/", response_model=list[str])
async def list_databases():
    return metadata_service.list_databases()


@router.get("/{database_name}", response_model=DatabaseMetadata)
async def get_metadata(database_name: str):
    try:
        return metadata_service.get_database_metadata(database_name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
