from fastapi import APIRouter
from backend.shared_models.lender import LenderDecisionInput, LenderApprovalSummary
from lender_simulator.approval_predictor.predictor import predict_all_lenders

router = APIRouter()


@router.post("/predict", response_model=LenderApprovalSummary)
async def predict_lender_approval(inp: LenderDecisionInput) -> LenderApprovalSummary:
    """Predict approval probability across all DSCR lenders."""
    return predict_all_lenders(inp)
