from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/meal-parse")
def parse_meal() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "not_implemented")
