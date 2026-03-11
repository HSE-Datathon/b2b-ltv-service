from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional

from .schemas import (
    CompanyItem,
    HealthResponse,
    LTVRequest,
    LTVResponse,
    NBORequest,
    NBOResponse,
    SegmentLTVResponse,
    TopNBOItem,
)
from .services.ltv_service import LTVService
from .services.nbo_service import NBOService

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="B2B LTV & NBO Analytics API",
    description=(
        "Сервис для расчета LTV клиентов B2B и выдачи рекомендаций по продуктам "
        "(Next Best Offer) на основе обученных моделей.\n\n"
        "API предполагается использовать как источник данных для BI-витрин и "
        "отчетности менеджмента."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ltv_service = LTVService()
nbo_service = NBOService()

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", tags=["ui"])
def index():
    return FileResponse(STATIC_DIR / "index.html", media_type="text/html")


@app.get("/companies", response_model=List[CompanyItem], tags=["service"])
def list_companies() -> List[CompanyItem]:
    company_ltv: dict = ltv_service._artifacts.get("company_ltv", {}) if ltv_service._artifacts else {}
    return [
        CompanyItem(
            company_id=cid,
            ltv_segment=v["ltv_segment"],
            predicted_ltv=round(v["predicted_ltv"], 2),
        )
        for cid, v in company_ltv.items()
    ]


@app.get("/health", response_model=HealthResponse, tags=["service"])
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/ltv/predict", response_model=LTVResponse, tags=["ltv"])
def predict_ltv(payload: LTVRequest) -> LTVResponse:
    try:
        return ltv_service.predict_ltv(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/ltv/segments", response_model=List[SegmentLTVResponse], tags=["ltv"])
def get_ltv_segments(limit: Optional[int] = 10) -> List[SegmentLTVResponse]:
    return ltv_service.get_top_segments(limit=limit)


@app.post("/nbo/recommend", response_model=NBOResponse, tags=["nbo"])
def recommend_products(payload: NBORequest) -> NBOResponse:
    try:
        return nbo_service.recommend(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/nbo/top", response_model=List[TopNBOItem], tags=["nbo"])
def get_top_nbo_products(n: Optional[int] = 10) -> List[TopNBOItem]:
    return nbo_service.get_top_nbo(n=max(1, n or 10))
