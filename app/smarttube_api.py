import httpx
class SmartTubeApiError(RuntimeError): pass

def base_url(tv):
 host=(tv.get("ip_address") or "").strip().rstrip("/")
 if not host: raise SmartTubeApiError("Kein SmartTube-Host eingetragen")
 return host if host.startswith(("http://","https://")) else f"http://{host}:{int(tv.get('api_port') or 8090)}"

async def request(tv,method,path,params=None,timeout=8):
 try:
  async with httpx.AsyncClient(auth=httpx.BasicAuth(tv.get("api_username") or "admin",tv.get("api_password") or ""),timeout=timeout) as c:
   r=await c.request(method,f"{base_url(tv)}/api/v1{path}",params=params)
  r.raise_for_status();return r.json() if r.content else {}
 except httpx.HTTPStatusError as e: raise SmartTubeApiError(f"HTTP {e.response.status_code}: {e.response.text}") from e
 except (httpx.HTTPError,ValueError) as e: raise SmartTubeApiError(f"SmartTube API nicht erreichbar: {e}") from e
async def playback_state(tv): return await request(tv,'GET','/playbackstate')
async def play_url(tv,video_id): return await request(tv,'POST','/play',{'url':f'https://www.youtube.com/watch?v={video_id}'},15)
async def command(tv,name,**params): return await request(tv,'POST',f'/playback/{name}',params or None)
