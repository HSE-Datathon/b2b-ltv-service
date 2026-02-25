from __future__ import annotations

from ..schemas import NBORequest, NBOResponse, RecommendedProduct


class NBOService:
    """
    Заглушка сервиса NBO (Next Best Offer).

    В боевой реализации:
    - загружается модель ранжирования / классификации по продуктам;
    - на основе профиля клиента и истории покупок формируется набор кандидатов;
    - для каждого продукта считается вероятность/ uplift по LTV;
    - результаты записываются в витрину, откуда могут забираться BI-системой.
    """

    MODEL_VERSION = "0.0.1-dev"

    def recommend(self, payload: NBORequest) -> NBOResponse:
        # TODO: заменить на реальную инференс-логику
        dummy_products = [
            RecommendedProduct(
                product_name="Enterprise-100",
                uplift_ltv=50_000,
                probability=0.65,
            ),
            RecommendedProduct(
                product_name="Расширения",
                uplift_ltv=20_000,
                probability=0.55,
            ),
        ]

        top_k = max(1, payload.top_k)

        return NBOResponse(
            company_id=payload.company_id,
            recommendations=dummy_products[:top_k],
            model_version=self.MODEL_VERSION,
        )

