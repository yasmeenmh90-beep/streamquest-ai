"""Exercise the real Host without binding sockets or contacting Twitch/providers."""
import tempfile,unittest
from backend.server import Host
class ResultPersistenceTests(unittest.IsolatedAsyncioTestCase):
 async def test_close_public_result_persists_and_duplicate_close_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   path=d+'/fixture.db';h=Host(path)
   try:
    await h.change('start');await h.change('open')
    await h.change('vote',{'user':'fixture-viewer','choice':1,'event':'fixture-event'})
    # Avoid scheduling the optional provider entirely in this offline fixture.
    async def no_narration(version):pass
    h.narrate=no_narration
    old_scene=h.state['scene'];s=await h.change('close');r=s['result']
    self.assertEqual(r['counts'],[0,1,0]);self.assertEqual(r['effects'],dict(oxygen=-8,energy=-5,chaos=15));self.assertEqual(r['new_memory'][0]['id'],'signal_decoded')
    self.assertEqual(s['scene'],old_scene)
    with self.assertRaises(ValueError):await h.change('close')
    await h.change('approve');self.assertEqual(h.public()['result'],r)
   finally:h.db.close()
   restored=Host(path)
   try:self.assertEqual(restored.public()['result'],r)
   finally:restored.db.close()
