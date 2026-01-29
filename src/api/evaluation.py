from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.evaluation import manual_evaluate_query
from services.evaluation import InstanceNotFoundError, GroundTruthQueryError
from models.schemas import ManualEvaluationStats

router = APIRouter()


class ManualEvaluationRequest(BaseModel):
    instance_id: str
    generated_sql: str


@router.post("/evaluation/manual", response_model=ManualEvaluationStats)
async def manual_evaluate(request: ManualEvaluationRequest):
    """
    Manually evaluate a generated SQL query against the ground truth.
    """
    try:
        stats = await manual_evaluate_query(
            instance_id=request.instance_id, generated_sql=request.generated_sql
        )
        return stats
    except InstanceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except GroundTruthQueryError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")