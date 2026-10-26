import httpx

class SmartTubeApiError(RuntimeError):
    pass

def base_url(tv):
    host=(tv.get("ip_address") or "").strip().rstrip("/")
    if not host:
        raise SmartTubeApiError("Kein SmartTube-Host eingetragen")
    if host.startswith(("http://", "https://")):
        return host
    return f"http://{host}:{int(tv.get('api_port') or 8090)}"

async def request(tv, method, path, params=None, timeout=8):
    try:
        async with httpx.AsyncClient(
            auth=httpx.BasicAuth(tv.get("api_username") or "admin", tv.get("api_password") or ""),
            timeout=timeout,
        ) as client:
            response=await client.request(method, f"{base_url(tv)}/api/v1{path}", params=params)
        response.raise_for_status()
        return response.json() if response.content else {}
    except httpx.HTTPStatusError as exc:
        raise SmartTubeApiError(f"HTTP {exc.response.status_code}: {exc.response.text}") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise SmartTubeApiError(f"SmartTube API nicht erreichbar: {exc}") from exc

async def playback_state(tv):
    return await request(tv, "GET", "/playbackstate")

async def play_url(tv, video_id):
    return await request(tv, "POST", "/play", {"url": f"https://www.youtube.com/watch?v={video_id}"}, 15)

async def command(tv, name, **params):
    return await request(tv, "POST", f"/playback/{name}", params or None)

async def queue_state(tv):
    return await request(tv, "GET", "/queue")

async def queue_add(tv, video_id):
    return await request(tv, "POST", "/queue/items", {"videoUrl": video_id}, 15)

async def queue_move(tv, from_index, to_index):
    return await request(tv, "POST", "/queue/items/move", {"from": from_index, "to": to_index})

async def queue_remove(tv, video_id):
    return await request(tv, "DELETE", f"/queue/items/{video_id}")
