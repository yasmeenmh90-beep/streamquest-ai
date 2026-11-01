"""Local integration fixtures. These are NOT real Twitch viewer evidence."""
import os,tempfile,unittest,asyncio
from unittest.mock import patch
from aiohttp.test_utils import TestClient,TestServer
from backend.server import make_app
class LiveFlowTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  # Keep credentials/configuration isolated, and clean up even if binding fails.
  env=patch.dict(os.environ,{'HOST_KEY':'local-test-password-123'},clear=True)
  env.start();self.addCleanup(env.stop)
  self.tmp=tempfile.TemporaryDirectory(prefix='streamquest-http-test-')
  self.addCleanup(self.tmp.cleanup)
  self.app=make_app(self.tmp.name+'/state.db')
  self.host=self.app['host']
  self.client=TestClient(TestServer(self.app,host='127.0.0.1',port=0))
  self.addAsyncCleanup(self.client.close)
  await self.client.start_server()
  response=await self.client.post('/api/login',json={'key':'local-test-password-123'})
  self.assertEqual(response.status,200)
 def event(self,user,command,id,channel='channel1'):
  return {'metadata':{'message_type':'notification','message_id':id},'payload':{'subscription':{'type':'channel.chat.message'},'event':{'broadcaster_user_id':channel,'chatter_user_id':user,'message':{'text':command}}}}
 async def action(self,action):
  r=await self.client.post('/api/action',json={'action':action,'version':self.host.state['version']});self.assertEqual(r.status,200);return await r.json()
 async def test_two_viewer_vote_to_approval_and_overlay(self):
  await self.action('start');await self.action('open')
  self.assertTrue(await self.host.handle_chat(self.event('u1','!a','e1'),'channel1'))
  await self.host.handle_chat(self.event('u1','!b','e2'),'channel1');await self.host.handle_chat(self.event('u2','!b','e3'),'channel1');await self.host.handle_chat(self.event('u2','!b','e3'),'channel1')
  old=self.host.state['scene'];s=await self.action('close');self.assertEqual(s['winner'],1);self.assertEqual(s['history'][0]['counts'],[0,2,0]);self.assertEqual(s['scene'],old);self.assertIsNotNone(s['draft'])
  token=self.host.overlay;host_preview=await (await self.client.get('/api/state?overlay='+token)).json();self.assertIsNone(host_preview['draft']);await self.client.post('/api/logout');r=await self.client.get('/api/state?overlay='+token);public=await r.json();self.assertIsNone(public['draft']);self.assertEqual(public['scene'],old);self.assertEqual(public['result'],s['result']);self.assertEqual(public['result']['counts'],[0,2,0]);self.assertEqual(public['result']['effects'],{'oxygen':-8,'energy':-5,'chaos':15});self.assertEqual(public['result']['new_memory'][0]['id'],'signal_decoded')
  self.assertEqual((await self.client.post('/api/action',json={'action':'approve'})).status,401)
  await self.client.post('/api/login',json={'key':'local-test-password-123'});s=await self.action('approve');self.assertEqual(s['round'],1);self.assertIn('engineer',s['scene']);self.assertIsNone(s['draft'])
 async def test_wrong_channel_invalid_and_late_events(self):
  await self.action('start');await self.action('open')
  self.assertFalse(await self.host.handle_chat(self.event('u1','!a','e1','other'),'channel1'));self.assertFalse(await self.host.handle_chat(self.event('u1','hello','e2'),'channel1'))
  await self.action('close');self.assertFalse(await self.host.handle_chat(self.event('u1','!a','e3'),'channel1'))
 async def test_concurrent_resolution_applies_effects_once(self):
  await self.action('start');await self.action('open');v=self.host.state['version']
  results=await asyncio.gather(self.host.change('close',version=v),self.host.change('close',version=v),return_exceptions=True)
  self.assertEqual(sum(isinstance(x,dict) for x in results),1);self.assertEqual(len(self.host.state['history']),1)
 async def test_timer_closes_and_disconnect_pauses(self):
  await self.action('start');await self.action('open');self.host.state['deadline']=0
  await asyncio.sleep(.3);self.assertEqual(self.host.state['status'],'pending')
  await self.action('approve');await self.action('open');await self.host.disconnect('Fixture disconnect');self.assertEqual(self.host.state['status'],'paused')
