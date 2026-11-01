import os,tempfile,unittest
from unittest.mock import patch
from aiohttp.test_utils import TestClient,TestServer
from backend.server import make_app
class ServerTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  # Keep credentials/configuration isolated, and clean up even if binding fails.
  env=patch.dict(os.environ,{'HOST_KEY':'test-host-password-123456'},clear=True)
  env.start();self.addCleanup(env.stop)
  self.tmp=tempfile.TemporaryDirectory(prefix='streamquest-http-test-')
  self.addCleanup(self.tmp.cleanup)
  self.app=make_app(self.tmp.name+'/test.db')
  self.host=self.app['host']
  self.c=TestClient(TestServer(self.app,host='127.0.0.1',port=0))
  self.addAsyncCleanup(self.c.close)
  await self.c.start_server()
 async def test_host_and_overlay_permissions(self):
  self.assertEqual((await self.c.get('/api/state')).status,401)
  self.assertEqual((await self.c.post('/api/login',json={'key':'bad'})).status,401)
  self.assertEqual((await self.c.post('/api/login',json={'key':'test-host-password-123456'})).status,200)
  conf=await (await self.c.get('/api/config')).json();self.assertIn('overlay_token',conf)
  self.assertEqual((await self.c.post('/api/action',json={'action':'start','version':0})).status,200)
  self.assertEqual((await self.c.post('/api/action',json={'action':'open','version':0})).status,409)
  self.assertEqual((await self.c.post('/api/action',json={'action':'vote','user':'fake','choice':0})).status,403)
  await self.c.post('/api/logout');r=await self.c.get('/api/state?overlay='+conf['overlay_token']);self.assertEqual(r.status,200)
  s=await r.json();self.assertNotIn('seen',s)
  self.assertEqual((await self.c.post('/api/action',json={'action':'open','version':1})).status,401)
 async def test_origin_rejected_and_static(self):
  self.assertEqual((await self.c.post('/api/login',json={'key':'test-host-password-123456'},headers={'Origin':'https://evil.example'})).status,403)
  for path in ['/', '/index.html', '/app.js?v=20261102-dream1', '/style.css?v=20261102-dream1', '/story.js?v=20261102-dream1']:
   r=await self.c.get(path)
   self.assertEqual(r.status,200)
   self.assertEqual(r.headers.get('Cache-Control'),'no-store')
  page=await (await self.c.get('/')).text()
  self.assertIn('app.js?v=20261102-dream1',page)
  self.assertIn('style.css?v=20261102-dream1',page)
if __name__=='__main__':unittest.main()
