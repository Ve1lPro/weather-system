import requests
from dataclasses import dataclass


@dataclass
class QWeatherClient:
    host: str
    api_key: str
    timeout: int = 12

    def _get(self, path: str, params: dict) -> dict:
        if not self.api_key:
            raise RuntimeError("QWEATHER_API_KEY 未配置（请在 .env 里填）")

        url = self.host.rstrip("/") + path

        headers = {
            "X-QW-Api-Key": self.api_key,   # 按你控制台要求放请求头
        }

        r = requests.get(url, params=params, headers=headers, timeout=self.timeout)

        if r.status_code != 200:
            raise RuntimeError(f"QWeather HTTP {r.status_code}: {r.text[:600]}")

        data = r.json()

        # 和风接口通常用 code=200 表示成功
        code = str(data.get("code", "200"))
        if code != "200":
            raise RuntimeError(f"QWeather API code={code}: {data}")

        return data

    def hourly_24h(self, location_id: str) -> dict:
        return self._get("/v7/weather/24h", {"location": location_id})