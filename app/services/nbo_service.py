from __future__ import annotations

from pathlib import Path
from typing import List

import joblib

from ..schemas import NBORequest, NBOResponse, RecommendedProduct, TopNBOItem

MODELS_DIR = Path(__file__).parent.parent / "models"


def _load_artifacts() -> dict | None:
    path = MODELS_DIR / "artifacts.joblib"
    if path.exists():
        return joblib.load(path)
    return None


class NBOService:

    def __init__(self) -> None:
        self._artifacts = _load_artifacts()
        if self._artifacts:
            print("[NBOService] Артефакты загружены, NBO активен.")
        else:
            print("[NBOService] Артефакты не найдены, работает в режиме заглушки.")

    @property
    def model_version(self) -> str:
        if self._artifacts:
            return self._artifacts.get("model_version", "1.0.0")
        return "0.0.1-dev"

    def recommend(self, payload: NBORequest) -> NBOResponse:
        if self._artifacts is None:
            return self._fallback_recommend(payload)

        top_k = max(1, payload.top_k)
        products: list[dict] = []

        if payload.company_id:
            products = self._artifacts["company_nbo"].get(str(payload.company_id), [])

        if not products:
            cluster = self._get_cluster(payload)
            products = self._artifacts["product_scores"].get(str(cluster), [])

        max_score = max((p["nbo_score"] for p in products), default=1.0) or 1.0

        recs = [
            RecommendedProduct(
                product_name=p["product_name"],
                uplift_ltv=float(p.get("avg_revenue", 0.0)),
                probability=round(float(p["nbo_score"]) / max_score, 4),
            )
            for p in products[:top_k]
        ]

        return NBOResponse(
            company_id=payload.company_id,
            recommendations=recs,
            model_version=self.model_version,
        )

    def _get_cluster(self, payload: NBORequest) -> int:
        try:
            import numpy as np
            import pandas as pd

            kmeans_path = MODELS_DIR / "kmeans.joblib"
            scaler_path = MODELS_DIR / "cluster_scaler.joblib"
            if not kmeans_path.exists():
                return 0

            kmeans = joblib.load(kmeans_path)
            scaler = joblib.load(scaler_path)
            arts = self._artifacts
            medians: dict = arts["median_features"]
            cluster_features: list = arts["cluster_features"]

            row = {f: medians.get(f, 0.0) for f in cluster_features}
            if payload.revenue is not None:
                row["total_revenue"] = payload.revenue

            X = np.log1p(
                np.clip(
                    pd.DataFrame([row])[cluster_features].values.astype(float),
                    a_min=0, a_max=None,
                )
            )
            return int(kmeans.predict(scaler.transform(X))[0])
        except Exception:
            return 0

    def get_top_nbo(self, n: int = 10) -> List[TopNBOItem]:
        if self._artifacts is None:
            return self._fallback_top_nbo(n)

        global_top: list[dict] = self._artifacts.get("global_top_nbo", [])
        max_score = max((p["nbo_score"] for p in global_top), default=1.0) or 1.0

        return [
            TopNBOItem(
                rank=i + 1,
                product_name=p["product_name"],
                nbo_score=round(float(p["nbo_score"]), 6),
                avg_revenue=float(p.get("avg_revenue", 0.0)),
                probability=round(float(p["nbo_score"]) / max_score, 4),
            )
            for i, p in enumerate(global_top[:n])
        ]

    @staticmethod
    def _fallback_recommend(payload: NBORequest) -> NBOResponse:
        top_k = max(1, payload.top_k)
        dummy = [
            RecommendedProduct(product_name="Enterprise-100", uplift_ltv=50_000, probability=0.65),
            RecommendedProduct(product_name="Расширения",     uplift_ltv=20_000, probability=0.55),
        ]
        return NBOResponse(
            company_id=payload.company_id,
            recommendations=dummy[:top_k],
            model_version="0.0.1-dev",
        )

    @staticmethod
    def _fallback_top_nbo(n: int) -> List[TopNBOItem]:
        stubs = [
            TopNBOItem(rank=1, product_name="Enterprise-100",    nbo_score=0.9, avg_revenue=50_000, probability=1.0),
            TopNBOItem(rank=2, product_name="Расширения",        nbo_score=0.7, avg_revenue=20_000, probability=0.78),
            TopNBOItem(rank=3, product_name="МТС Линк. Команда", nbo_score=0.5, avg_revenue=15_000, probability=0.56),
        ]
        return stubs[:n]
