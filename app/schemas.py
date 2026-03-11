from typing import List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="Текущее состояние сервиса")


class LTVRequest(BaseModel):
    company_id: Optional[str] = Field(
        default=None,
        description="ID компании. Может использоваться для онлайнового скоринга существующего клиента.",
    )
    sector_id: Optional[str] = None
    segment: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[float] = Field(
        default=None, description="Число сотрудников компании"
    )
    revenue: Optional[float] = Field(
        default=None, description="Нормированная годовая выручка за 2023 год"
    )
    segment_2: Optional[str] = None


class LTVResponse(BaseModel):
    company_id: Optional[str] = None
    predicted_ltv: float = Field(..., description="Прогнозный LTV клиента")
    ltv_segment: str = Field(..., description="Сегмент по LTV (например, low/mid/high)")
    model_version: str = Field(..., description="Версия модели LTV")


class SegmentLTVResponse(BaseModel):
    ltv_segment: str
    avg_ltv: float
    clients_count: int


class RecommendedProduct(BaseModel):
    product_name: str
    uplift_ltv: float = Field(
        ..., description="Ожидаемый прирост LTV при продаже продукта"
    )
    probability: float = Field(
        ..., description="Вероятность покупки/отклика по модели NBO"
    )


class NBORequest(BaseModel):
    company_id: Optional[str] = None
    sector_id: Optional[str] = None
    segment: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[float] = None
    revenue: Optional[float] = None
    segment_2: Optional[str] = None
    top_k: int = Field(default=5, description="Сколько продуктов отдать в рекомендацию")


class NBOResponse(BaseModel):
    company_id: Optional[str] = None
    recommendations: List[RecommendedProduct]
    model_version: str


class CompanyItem(BaseModel):
    company_id: str
    ltv_segment: str
    predicted_ltv: float


class TopNBOItem(BaseModel):
    rank: int = Field(..., description="Позиция в рейтинге")
    product_name: str
    nbo_score: float = Field(..., description="Суммарный NBO-скор по всем кластерам")
    avg_revenue: float = Field(..., description="Средняя выручка по продукту")
    probability: float = Field(..., description="Нормированная вероятность рекомендации")

