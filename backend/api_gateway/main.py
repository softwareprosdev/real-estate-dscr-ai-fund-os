"""
FastAPI gateway — single entry point for all DSCR Fund OS services.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api_gateway.routers import underwriting, lender, decision, bidding, portfolio, health

app = FastAPI(
    title="DSCR Real Estate AI Fund OS",
    description="Institutional DSCR underwriting, lender simulation, RL capital allocation",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(underwriting.router, prefix="/api/v1/underwriting", tags=["underwriting"])
app.include_router(lender.router, prefix="/api/v1/lender", tags=["lender"])
app.include_router(decision.router, prefix="/api/v1/decision", tags=["decision"])
app.include_router(bidding.router, prefix="/api/v1/bidding", tags=["bidding"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["portfolio"])
