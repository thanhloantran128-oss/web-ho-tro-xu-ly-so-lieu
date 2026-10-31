import json

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def _survey():
    rng = np.random.default_rng(7)
    n = 60
    df = pd.DataFrame({f"PSS{i}": rng.integers(0, 5, n) for i in range(1, 11)})
    df["GioiTinh"] = rng.choice(["Nam", "Nữ"], n)
    df["Khoi"] = rng.choice([10, 11, 12], n)
    return df


def test_list_scales():
    r = client.get("/thang-do")
    assert r.status_code == 200
    assert any(s["ma"] == "DASS-21" for s in r.json())


def test_preview_suggests_pss10_without_raw_data():
    r = client.post("/xem-truoc", files={"file": ("data.csv", _csv(_survey()), "text/csv")})
    body = r.json()
    assert r.status_code == 200
    group = next(g for g in body["goi_y_thang_do"] if g["tien_to"] == "pss")
    assert group["thang_co_the"][0]["ma"] == "PSS-10"


def test_scale_score_then_ttest_and_anova():
    params = {"thang_do": [{"ma": "PSS-10", "cot": [f"PSS{i}" for i in range(1, 11)]}]}
    files = {"file": ("data.csv", _csv(_survey()), "text/csv")}
    r = client.post("/phan-tich", files=files,
                    data={"params": json.dumps({**params, "analysis": "t-test", "type": "independent",
                                                "dv": "PSS-10_TONG", "group": "GioiTinh"})})
    assert r.status_code == 200, r.text
    assert r.json()["thang_do"][0]["ma"] == "PSS-10"
    files = {"file": ("data.csv", _csv(_survey()), "text/csv")}
    r = client.post("/phan-tich", files=files,
                    data={"params": json.dumps({**params, "analysis": "anova", "dv": "PSS-10_TONG",
                                                "factor": "Khoi"})})
    assert r.status_code == 200, r.text
    assert r.json()["posthoc"]["method"] in ("Tukey HSD", "Games-Howell")


def test_bad_request_message_in_vietnamese():
    files = {"file": ("data.csv", _csv(_survey()), "text/csv")}
    r = client.post("/phan-tich", files=files,
                    data={"params": json.dumps({"analysis": "anova", "dv": "PSS1", "factor": "GioiTinh"})})
    assert r.status_code == 400
    assert "t-test" in r.json()["detail"]
