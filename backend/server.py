"""Local-first StreamQuest host with SQLite, OAuth and Twitch EventSub."""
import asyncio,json,os,secrets,sqlite3,time,hmac
from pathlib import Path
from urllib.parse import urlencode
from aiohttp import web,ClientSession,ClientTimeout
from .engine import initial,mutate
ROOT=Path(__file__).resolve().parents[1]
class Host:
 def __init__(self,path):
  self.db=sqlite3.connect(path);self.db.execute('CREATE TABLE IF NOT EXISTS kv(k TEXT PRIMARY KEY,v TEXT)');self.lock=asyncio.Lock();self.sessions=set();self.oauth={};self.twitch='Not connected';self.http=None
  self.overlay=self.get('overlay') or secrets.token_urlsafe(32);self.put('overlay',self.overlay)
  self.state=self.get('state') or initial()
  for key,value in initial().items():self.state.setdefault(key,value)
  if self.state['status']=='voting':self.state=mutate(self.state,'pause');self.put('state',self.state)
 def get(self,k):
  r=self.db.execute('SELECT v FROM kv WHERE k=?',(k,)).fetchone();return json.loads(r[0]) if r else None
 def put(self,k,v):self.db.execute('INSERT OR REPLACE INTO kv VALUES(?,?)',(k,json.dumps(v)));self.db.commit()
 def save(self):self.put('state',self.state)
 def authorized(self,r):return r.cookies.get('sq_host') in self.sessions
 async def change(self,a,data=None,version=None):
  async with self.lock:
   if version is not None and version!=self.state['version']:raise ValueError('State changed; try again')
   self.state=mutate(self.state,a,data);self.save()
   if a=='close':asyncio.create_task(self.narrate(self.state['version']))
   return self.public()
 def public(self):
  s=dict(self.state);s.pop('seen',None);s['votes']={str(i):v for i,v in enumerate(s['votes'].values())};return s
 async def narrate(self,version):
  if not os.getenv('STORY_API_KEY') or not os.getenv('STORY_MODEL'):return
  snapshot=json.loads(json.dumps(self.state));context={k:snapshot[k] for k in ['round','oxygen','energy','chaos','history','draft','facts','memory','ending']}
  try:
   async with self.http.post(os.getenv('STORY_API_URL','https://api.openai.com/v1/chat/completions'),headers={'Authorization':'Bearer '+os.environ['STORY_API_KEY']},json={'model':os.environ['STORY_MODEL'],'messages':[{'role':'system','content':'Write a family-friendly space adventure scene, under 100 words, consistent with supplied facts and draft. Do not change resources or vote outcomes. Return JSON with one field: scene_text. No tools.'},{'role':'user','content':json.dumps(context)}],'response_format':{'type':'json_object'},'max_completion_tokens':350},timeout=ClientTimeout(total=18)) as r:
    if r.status!=200:return
    j=await r.json();text=json.loads(j['choices'][0]['message']['content'])['scene_text']
    if not isinstance(text,str) or not text.strip() or len(text.split())>110 or len(text)>1400:return
   async with self.lock:
    if self.state['version']==version and self.state['status']=='pending':self.state.update(draft=text,narrator='AI generated · awaiting host review',version=version+1);self.save()
  except (Exception,):pass # Existing fallback remains available. Never expose provider errors/secrets.
 async def ticker(self):
  while True:
   await asyncio.sleep(.2)
   if self.state['status']=='voting' and time.time()*1000>=self.state['deadline']:
    try:await self.change('close')
    except ValueError:pass
 async def disconnect(self,label):
  self.twitch=label
  if self.state['status']=='voting':
   try:await self.change('pause')
   except ValueError:pass
 async def handle_chat(self,message,broadcaster):
  if message.get('metadata',{}).get('message_type')!='notification':return False
  payload=message.get('payload',{})
  if payload.get('subscription',{}).get('type')!='channel.chat.message':return False
  e=payload.get('event',{});cmd=e.get('message',{}).get('text','').strip().lower()
  if e.get('broadcaster_user_id')!=broadcaster or cmd not in ('!a','!b','!c'):return False
  user=e.get('chatter_user_id');event=message.get('metadata',{}).get('message_id')
  if not user or not event:return False
  try:await self.change('vote',{'user':user,'choice':'abc'.index(cmd[1]),'event':event});return True
  except ValueError:return False
 async def twitch_loop(self):
  while True:
   tokens=self.get('twitch_tokens')
   if not tokens:await asyncio.sleep(2);continue
   try:
    async with self.http.get('https://id.twitch.tv/oauth2/validate',headers={'Authorization':'OAuth '+tokens['access_token']}) as r:
     if r.status!=200:
      if tokens.get('refresh_token'):
       async with self.http.post('https://id.twitch.tv/oauth2/token',data={'grant_type':'refresh_token','refresh_token':tokens['refresh_token'],'client_id':os.environ['TWITCH_CLIENT_ID'],'client_secret':os.environ['TWITCH_CLIENT_SECRET']}) as rr:
        if rr.status==200:self.put('twitch_tokens',await rr.json());continue
      await self.disconnect('Authorization expired. Reconnect Twitch.');await asyncio.sleep(15);continue
     identity=await r.json()
    user=identity['user_id'];url='wss://eventsub.wss.twitch.tv/ws';handoff=False
    while True:
     async with self.http.ws_connect(url,heartbeat=None,receive_timeout=80) as ws:
      async for msg in ws:
       if msg.type!=web.WSMsgType.TEXT:continue
       j=json.loads(msg.data);kind=j['metadata']['message_type'];payload=j['payload']
       if kind=='session_welcome':
        if not handoff:
         async with self.http.post('https://api.twitch.tv/helix/eventsub/subscriptions',headers={'Client-Id':os.environ['TWITCH_CLIENT_ID'],'Authorization':'Bearer '+tokens['access_token']},json={'type':'channel.chat.message','version':'1','condition':{'broadcaster_user_id':user,'user_id':user},'transport':{'method':'websocket','session_id':payload['session']['id']}}) as r:
          if r.status!=202:raise RuntimeError('Subscription rejected')
        handoff=False;self.twitch='Connected to '+identity.get('login','your channel')
       elif kind=='session_reconnect':
        candidate=payload['session']['reconnect_url']
        if not candidate.startswith('wss://eventsub.wss.twitch.tv/'):raise RuntimeError('Invalid reconnect host')
        url=candidate;handoff=True;break
       elif kind=='revocation':raise RuntimeError('Twitch authorization revoked')
       elif kind=='notification':
        await self.handle_chat(j,user)
     if not handoff:raise RuntimeError('Connection interrupted')
   except asyncio.CancelledError:raise
   except Exception:await self.disconnect('Twitch disconnected. Reconnecting; voting paused.');await asyncio.sleep(5)
def make_app(db_path=None):
 host_key=os.getenv('HOST_KEY','')
 if len(host_key)<16:raise RuntimeError('Set HOST_KEY to at least 16 characters before starting.')
 data=Path(db_path or os.getenv('DATABASE_PATH',str(ROOT/'data'/'streamquest.db')));data.parent.mkdir(parents=True,exist_ok=True);h=Host(data)
 @web.middleware
 async def security(r,handler):
  if r.method=='POST':
   origin=r.headers.get('Origin');expected=os.getenv('APP_BASE_URL','http://localhost:8080').rstrip('/')
   if origin and origin!=expected:return web.json_response({'error':'Origin rejected'},status=403)
  try:response=await handler(r)
  except ValueError as e:response=web.json_response({'error':str(e)},status=409)
  # Revalidate entry points and modules on every OBS/browser refresh.
  response.headers['Cache-Control']='no-store'
  response.headers['X-Content-Type-Options']='nosniff';response.headers['Referrer-Policy']='no-referrer';return response
 app=web.Application(middlewares=[security],client_max_size=10000);app['host']=h
 async def login(r):
  j=await r.json()
  if not hmac.compare_digest(str(j.get('key','')),host_key):await asyncio.sleep(.5);return web.json_response({'error':'Invalid key'},status=401)
  sid=secrets.token_urlsafe(32);h.sessions.add(sid);resp=web.json_response({'ok':True});resp.set_cookie('sq_host',sid,httponly=True,samesite='Lax',secure=os.getenv('APP_BASE_URL','').startswith('https:'));return resp
 async def logout(r):h.sessions.discard(r.cookies.get('sq_host'));resp=web.json_response({'ok':True});resp.del_cookie('sq_host');return resp
 def require(r):
  if not h.authorized(r):raise web.HTTPUnauthorized()
 async def state(r):
  if not h.authorized(r) and not hmac.compare_digest(r.query.get('overlay',''),h.overlay):raise web.HTTPUnauthorized()
  snapshot=h.public()
  if 'overlay' in r.query or not h.authorized(r):snapshot['draft']=None
  return web.json_response(snapshot)
 async def config(r):require(r);return web.json_response({'twitch':h.twitch,'ai':bool(os.getenv('STORY_API_KEY') and os.getenv('STORY_MODEL')),'overlay_token':h.overlay})
 async def action(r):
  require(r);j=await r.json()
  if j.get('action')=='vote':raise web.HTTPForbidden(text='Live votes must come from Twitch')
  return web.json_response(await h.change(j.get('action'),version=j.get('version')))
 async def oauth(r):
  require(r)
  if not os.getenv('TWITCH_CLIENT_ID') or not os.getenv('TWITCH_CLIENT_SECRET'):return web.Response(text='Configure TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET in the backend environment.',status=503)
  state=secrets.token_urlsafe(32);h.oauth[state]=(r.cookies['sq_host'],time.time()+600)
  raise web.HTTPFound('https://id.twitch.tv/oauth2/authorize?'+urlencode({'client_id':os.environ['TWITCH_CLIENT_ID'],'redirect_uri':os.getenv('TWITCH_REDIRECT_URI','http://localhost:8080/auth/callback'),'response_type':'code','scope':'user:read:chat','state':state}))
 async def callback(r):
  require(r);record=h.oauth.pop(r.query.get('state',''),None)
  if not record or record[0]!=r.cookies.get('sq_host') or record[1]<time.time():raise web.HTTPForbidden()
  if not r.query.get('code'):return web.Response(text='Authorization declined. Return to Connections.',status=400)
  async with h.http.post('https://id.twitch.tv/oauth2/token',data={'client_id':os.environ['TWITCH_CLIENT_ID'],'client_secret':os.environ['TWITCH_CLIENT_SECRET'],'code':r.query['code'],'grant_type':'authorization_code','redirect_uri':os.getenv('TWITCH_REDIRECT_URI','http://localhost:8080/auth/callback')}) as rr:
   if rr.status!=200:return web.Response(text='Twitch authorization failed. Retry Connections.',status=502)
   h.put('twitch_tokens',await rr.json())
  raise web.HTTPFound('/')
 async def health(r):return web.json_response({'service':'streamquest','ok':True})
 async def index(r):return web.FileResponse(ROOT/'dist'/'index.html')
 app.router.add_get('/api/health',health);app.router.add_post('/api/login',login);app.router.add_post('/api/logout',logout);app.router.add_get('/api/state',state);app.router.add_get('/api/config',config);app.router.add_post('/api/action',action);app.router.add_get('/auth/twitch',oauth);app.router.add_get('/auth/callback',callback);app.router.add_get('/',index);app.router.add_static('/',ROOT/'dist',show_index=False)
 async def context(app):
  h.http=ClientSession(trust_env=True);tasks=[asyncio.create_task(h.ticker()),asyncio.create_task(h.twitch_loop())];yield
  for t in tasks:t.cancel()
  await asyncio.gather(*tasks,return_exceptions=True);await h.http.close();h.db.close()
 app.cleanup_ctx.append(context);return app
if __name__=='__main__':web.run_app(make_app(),host='127.0.0.1',port=int(os.getenv('PORT','8080')))
