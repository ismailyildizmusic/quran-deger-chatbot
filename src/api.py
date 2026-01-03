from __future__ import annotations

import requests

BASE_URL = "https://api.alquran.cloud/v1"


class QuranAPIError(RuntimeError):
    pass


def _get(url: str, params: dict | None = None) -> dict:
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        raise QuranAPIError(f"API isteği başarısız: {e}") from e

    if not isinstance(data, dict) or data.get("status") != "OK":
        raise QuranAPIError(f"API beklenmeyen cevap döndürdü: {data}")
    return data


def list_tr_translations() -> list[dict]:
    """
    Türkçe çeviri (translation) editionlarını listeler.
    Doküman: /v1/edition?format=text&language=tr&type=translation
    """
    url = f"{BASE_URL}/edition"
    params = {"format": "text", "language": "tr", "type": "translation"}
    data = _get(url, params=params)
    return data["data"]


def search(keyword: str, surah: str = "all", edition_or_language: str = "tr") -> dict:
    """
    Kur'an metninde arama.
    Doküman: /v1/search/{keyword}/{surah}/{edition or language}
    """
    url = f"{BASE_URL}/search/{keyword}/{surah}/{edition_or_language}"
    return _get(url)["data"]


def ayah_multi(reference: str, editions_csv: str) -> list[dict]:
    """
    Aynı ayeti birden fazla edition'dan getirir.
    Doküman: /v1/ayah/{reference}/editions/{edition1},{edition2}
    """
    url = f"{BASE_URL}/ayah/{reference}/editions/{editions_csv}"
    return _get(url)["data"]
