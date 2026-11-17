"""Read-only outbound checks; run with the backend's Python and environment."""

import asyncio
import json
import os
from urllib.parse import urlsplit

import httpx

from app.core.config import settings


def _safe_address(value: str) -> str:
    parsed = urlsplit(value)
    host = parsed.hostname or ""
    if ":" in host:
        host = f"[{host}]"
    return f"{parsed.scheme}://{host}" + (f":{parsed.port}" if parsed.port else "")


async def _probe(service: str, url: str, token: str | None = None) -> dict:
    result = {"service": service, "address": _safe_address(url)}
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        # Use the same proxy environment as the application, without bypassing it.
        async with httpx.AsyncClient(timeout=httpx.Timeout(20, connect=5)) as client:
            response = await client.get(url, headers=headers)
        result.update(ok=response.is_success, http_status=response.status_code)
        if not response.is_success:
            result["hint"] = "网络已连通；请检查凭证、接口地址或服务端限流。"
    except httpx.HTTPError as exc:
        causes = []
        cause: BaseException | None = exc
        while cause is not None and len(causes) < 6:
            causes.append(type(cause).__name__)
            cause = cause.__cause__
        result.update(
            ok=False,
            error_types=causes,
            hint="检查服务器网络及代理端口是否可用；/health 正常不代表外部服务可用。",
        )
    return result


async def main() -> int:
    proxies = {
        key: _safe_address(os.environ[key])
        for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")
        if os.environ.get(key)
    }
    checks = [_probe("github", settings.github_api_base_url.rstrip("/") + "/rate_limit", settings.github_token)]
    if settings.llm_api_key:
        checks.append(_probe("llm", settings.llm_base_url.rstrip("/") + "/models", settings.llm_api_key))
    results = list(await asyncio.gather(*checks))
    if not settings.llm_api_key:
        results.append({"service": "llm", "ok": False, "hint": "尚未配置 LLM_API_KEY。"})
    print(json.dumps({"proxies": proxies, "checks": results}, ensure_ascii=False, indent=2))
    return 0 if all(item["ok"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
