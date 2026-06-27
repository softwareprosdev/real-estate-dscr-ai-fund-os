from fastapi import APIRouter
from backend.shared_models.underwriting import UnderwritingInput, UnderwritingReport
from core.underwriting_engine.engine import underwrite

router = APIRouter()


@router.post("/analyze", response_model=UnderwritingReport)
async def analyze(inp: UnderwritingInput) -> UnderwritingReport:
    """Run full institutional DSCR underwriting on a property."""
    return underwrite(inp)
