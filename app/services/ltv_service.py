from __future__ import annotations

from typing import List

from ..schemas import LTVRequest, LTVResponse, SegmentLTVResponse


class LTVService:
    """
    Заглушка сервиса LTV.

    В боевой реализации здесь:
    - загружается обученная модель (pickle/joblib);
    - подготавливаются фичи по клиенту;
    - считается прогнозный LTV;
    - LTV-баллы маппятся к сегментам (low/mid/high или квантильные группы).
    """

    MODEL_VERSION = "0.0.1-dev"

    def predict_ltv(self, payload: LTVRequest) -> LTVResponse:
        # TODO: заменить на реальную инференс-логику
        dummy_ltv = 100_000.0
        ltv_segment = "mid"

        return LTVResponse(
            company_id=payload.company_id,
            predicted_ltv=dummy_ltv,
            ltv_segment=ltv_segment,
            model_version=self.MODEL_VERSION,
        )

    def get_top_segments(self, limit: int = 10) -> List[SegmentLTVResponse]:
        # TODO: заменить на выгрузку из витрины / базы с рассчитанными метриками
        segments = [
            SegmentLTVResponse(ltv_segment="low", avg_ltv=50_000, clients_count=500),
            SegmentLTVResponse(ltv_segment="mid", avg_ltv=120_000, clients_count=300),
            SegmentLTVResponse(ltv_segment="high", avg_ltv=300_000, clients_count=50),
        ]
        return segments[:limit]

