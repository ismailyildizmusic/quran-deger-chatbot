from __future__ import annotations

import time
from urllib.parse import quote

import requests

BASE_URL = "https://api.alquran.cloud/v1"


class QuranAPIError(RuntimeError):
    pass


def _get(url: str, params: dict | None = None, *, empty_on_404: bool = False) -> dict:
    """
    empty_on_404=True ise 404'te hata fırlatmak yerine 'boş sonuç' döndürür.
    Bu, search endpoint'inde çok işe yarar (bazı kelimelerde API 404 döndürebiliyor).
    """
    last_err = None

    # Basit retry: geçici hata / rate limit olursa tekrar dene
    for _ in range(3):
        try:
            r = requests.get(url, params=params, timeout=20)

            # Search için: sonuç yoksa bazen 404 gelebiliyor → boş sonuç dön
            if r.status_code == 404 and empty_on_404:
                return {"status": "OK", "data": {"count": 0, "matches": []}}

            # Rate limit / geçici sunucu hatasıysa kısa bekle ve tekrar dene
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(1.0)
                continue

            r.raise_for_status()
            data = r.json()

            if not isinstance(data, dict) or data.get("status") != "OK":
                raise QuranAPIError(f"API beklenmeyen cevap döndürdü: {data}")

            return data

        except Exception as e:
            last_err = e
            time.sleep(0.5)

    raise QuranAPIError(f"API isteği başarısız: {last_err}") from last_err


def list_tr_translations() -> list[dict]:
    """
    Türkçe çeviri (translation) editionlarını listeler.
    """
    url = f"{BASE_URL}/edition"
    params = {"format": "text", "language": "tr", "type": "translation"}
    data = _get(url, params=params)
    return data["data"]


def search(keyword: str, surah: str = "all", edition_or_language: str = "tr") -> dict:
    """
    Kur'an metninde arama.
    Bazı kelimelerde API 404 döndürürse bunu '0 sonuç' kabul ederiz.
    """
    kw = quote(keyword.strip(), safe="")  # URL encode
    url = f"{BASE_URL}/search/{kw}/{surah}/{edition_or_language}"
    data = _get(url, empty_on_404=True)
    return data["data"]


def ayah_multi(reference: str, editions_csv: str) -> list[dict]:
    """
    Aynı ayeti birden fazla edition'dan getirir.
    """
    ref = quote(reference.strip(), safe=":")  # "2:255" gibi ref güvenli kalsın
    url = f"{BASE_URL}/ayah/{ref}/editions/{editions_csv}"
    data = _get(url)
    return data["data"]
