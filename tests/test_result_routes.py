"""Socket-free checks of the actual state/action route handlers and Host integration."""
import asyncio,json,os,tempfile,unittest
from unittest.mock import patch
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from backend.server import make_app
class ResultRouteTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  self.env=patch.dict(os.environ,{'HOST_KEY':'isolated-fixture-host-password'},clear=True);self.env.start()
  self.tmp=tempfile.TemporaryDirectory();self.app=make_app(self.tmp.name+'/state.db');self.host=self.app['host'];self.host.sessions.add('fixture-session')
  async def offline(version):pass
  self.host.narrate=offline
 async def asyncTearDown(self):self.host.db.close();self.tmp.cleanup();self.env.stop()
 async def request(self,method,path,body=None,authorized=False):
  r=make_mocked_request(method,path,headers={'Cookie':'sq_host=fixture-session'} if authorized else {},app=self.app)
  if body is not None:
   async def request_json():return body
   r.json=request_json
  match=await self.app.router.resolve(r)
  return await match.handler(r)
 async def test_overlay_redaction_and_authoritative_result(self):
  await self.host.change('start');await self.host.change('open')
  event={'metadata':{'message_type':'notification','message_id':'fixture-e1'},'payload':{'subscription':{'type':'channel.chat.message'},'event':{'broadcaster_user_id':'fixture-channel','chatter_user_id':'fixture-viewer','message':{'text':'!b'}}}}
  self.assertTrue(await self.host.handle_chat(event,'fixture-channel'))
  self.assertTrue(await self.host.handle_chat(event,'fixture-channel'))
  old=self.host.state['scene'];closed=await self.host.change('close')
  for authorized in [False,True]:
   response=await self.request('GET','/api/state?overlay='+self.host.overlay,authorized=authorized)
   s=json.loads(response.text);self.assertEqual(s['result'],closed['result']);self.assertIsNone(s['draft']);self.assertEqual(s['scene'],old)
   self.assertEqual(s['result']['counts'],[0,1,0]);self.assertEqual(s['result']['effects'],dict(oxygen=-8,energy=-5,chaos=15));self.assertNotIn('fixture-viewer',s['votes'])
  await self.request('POST','/api/action',{'action':'approve','version':self.host.state['version']},authorized=True)
  self.assertNotEqual(self.host.state['scene'],old)
 async def test_unauthorized_and_client_votes_rejected(self):
  with self.assertRaises(web.HTTPUnauthorized):await self.request('GET','/api/state?overlay=invalid')
  with self.assertRaises(web.HTTPUnauthorized):await self.request('POST','/api/action',{'action':'close'})
  with self.assertRaises(web.HTTPForbidden):await self.request('POST','/api/action',{'action':'vote','user':'fake','choice':0},authorized=True)
 async def test_concurrent_close_and_timer(self):
  await self.host.change('start');await self.host.change('open');version=self.host.state['version']
  results=await asyncio.gather(self.host.change('close',version=version),self.host.change('close',version=version),return_exceptions=True)
  self.assertEqual(sum(isinstance(r,dict) for r in results),1);self.assertEqual(len(self.host.state['history']),1)
  await self.host.change('approve');await self.host.change('open');self.host.state['deadline']=0
  task=asyncio.create_task(self.host.ticker())
  try:
   await asyncio.sleep(.3);self.assertEqual(self.host.state['status'],'pending');self.assertEqual(self.host.state['result']['resolution'],'no_votes')
  finally:task.cancel();await asyncio.gather(task,return_exceptions=True)

 async def test_asset_cache_policy_and_revision(self):
  for path in ['/', '/index.html', '/app.js?v=20261102-dream1', '/style.css?v=20261102-dream1', '/story.js?v=20261102-dream1']:
   r=make_mocked_request('GET',path,app=self.app)
   match=await self.app.router.resolve(r)
   r._match_info=match
   response=await self.app.middlewares[0](r,match.handler)
   self.assertEqual(response.status,200)
   self.assertEqual(response.headers['Cache-Control'],'no-store')
