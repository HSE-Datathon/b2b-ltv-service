from __future__ import annotations

from pathlib import Path
from typing import List

import joblib
import numpy as np

from ..schemas import LTVRequest, LTVResponse, SegmentLTVResponse

MODELS_DIR = Path(__file__).parent.parent / "models"


def _load_artifacts() -> dict | None:
    path = MODELS_DIR / "artifacts.joblib"
    if path.exists():
        return joblib.load(path)
    return None


def _load_catboost():
    try:
        from catboost import CatBoostRegressor
        path = MODELS_DIR / "catboost_ltv.cbm"
        if path.exists():
            m = CatBoostRegressor()
            m.load_model(str(path))
            return m
    except Exception:
        pass
    return None


class LTVService:

    def __init__(self) -> None:
        self._artifacts = _load_artifacts()
        self._model = _load_catboost()
        if self._artifacts:
            print("[LTVService] Артефакты загружены, модель активна.")
        else:
            print("[LTVService] Артефакты не найдены, работает в режиме заглушки.")

    @property
    def model_version(self) -> str:
        if self._artifacts:
            return self._artifacts.get("model_version", "1.0.0")
        return "0.0.1-dev"

    def predict_ltv(self, payload: LTVRequest) -> LTVResponse:
        if self._artifacts is None:
            return self._fallback_predict(payload)

        if payload.company_id:
            entry = self._artifacts["company_ltv"].get(str(payload.company_id))
            if entry:
                return LTVResponse(
                    company_id=payload.company_id,
                    predicted_ltv=entry["predicted_ltv"],
                    ltv_segment=entry["ltv_segment"],
                    model_version=self.model_version,
                )

        if self._model is not None:
            return self._infer(payload)

        return self._fallback_predict(payload)

    def _infer(self, payload: LTVRequest) -> LTVResponse:
        arts = self._artifacts
        medians: dict = arts["median_features"]
        feature_cols: list = arts["feature_cols"]
        cat_features: list = arts["cat_features"]

        cluster = self._predict_cluster(payload)

        row: dict = {
            "sector":    str(payload.sector_id or "unknown"),
            "segment":   str(payload.segment or "unknown"),
            "industry":  str(payload.industry or "unknown"),
            "segment_2": str(payload.segment_2 or "unknown"),
            "company_size": payload.company_size,
            "revenue":   payload.revenue,
            "cluster":   str(cluster),
        }

        for col in feature_cols:
            if col not in row or row[col] is None:
                row[col] = medians.get(col, 0.0)

        import pandas as pd
        X = pd.DataFrame([row])[feature_cols]
        for col in cat_features:
            X[col] = X[col].astype(str).fillna("unknown")

        pred_log = float(self._model.predict(X)[0])
        pred_ltv = float(np.expm1(pred_log))

        q33: float = arts["ltv_q33"]
        q66: float = arts["ltv_q66"]
        segment = "high" if pred_ltv > q66 else ("mid" if pred_ltv > q33 else "low")

        return LTVResponse(
            company_id=payload.company_id,
            predicted_ltv=pred_ltv,
            ltv_segment=segment,
            model_version=self.model_version,
        )

    def _predict_cluster(self, payload: LTVRequest) -> int:
        try:
            kmeans_path = MODELS_DIR / "kmeans.joblib"
            scaler_path = MODELS_DIR / "cluster_scaler.joblib"
            if not kmeans_path.exists():
                return 0

            kmeans = joblib.load(kmeans_path)
            scaler = joblib.load(scaler_path)
            arts = self._artifacts
            medians = arts["median_features"]
            cluster_features = arts["cluster_features"]

            row = {f: medians.get(f, 0.0) for f in cluster_features}
            if payload.revenue is not None:
                row["total_revenue"] = payload.revenue

            import pandas as pd
            X = np.log1p(
                np.clip(
                    pd.DataFrame([row])[cluster_features].values.astype(float),
                    a_min=0, a_max=None,
                )
            )
            return int(kmeans.predict(scaler.transform(X))[0])
        except Exception:
            return 0

    def get_top_segments(self, limit: int = 10) -> List[SegmentLTVResponse]:
        if self._artifacts:
            stats = self._artifacts.get("segment_stats", [])
            return [
                SegmentLTVResponse(
                    ltv_segment=s["ltv_segment"],
                    avg_ltv=s["avg_ltv"],
                    clients_count=s["clients_count"],
                )
                for s in stats[:limit]
            ]
        return [
            SegmentLTVResponse(ltv_segment="low",  avg_ltv=50_000,  clients_count=500),
            SegmentLTVResponse(ltv_segment="mid",  avg_ltv=120_000, clients_count=300),
            SegmentLTVResponse(ltv_segment="high", avg_ltv=300_000, clients_count=50),
        ][:limit]

    @staticmethod
    def _fallback_predict(payload: LTVRequest) -> LTVResponse:
        return LTVResponse(
            company_id=payload.company_id,
            predicted_ltv=100_000.0,
            ltv_segment="mid",
            model_version="0.0.1-dev",
        )
