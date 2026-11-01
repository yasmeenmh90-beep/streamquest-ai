import unittest
from backend.engine import initial,mutate
class EngineTests(unittest.TestCase):
 def voting(self):return mutate(mutate(initial(),'start',now=0),'open',now=0)
 def test_replace_and_dedupe(self):
  s=self.voting();s=mutate(s,'vote',{'user':'a','choice':0,'event':'1'},now=1);s=mutate(s,'vote',{'user':'a','choice':1,'event':'2'},now=2)
  self.assertEqual(s['votes'],{'a':1});self.assertEqual(mutate(s,'vote',{'user':'b','choice':2,'event':'2'},now=3),s)
 def test_deadline_and_invalid_vote(self):
  for d in [{'user':'x','choice':3},{'user':'','choice':1},{'user':'x','choice':True}]:
   with self.assertRaises(ValueError):mutate(self.voting(),'vote',d,now=1)
  with self.assertRaises(ValueError):mutate(self.voting(),'vote',{'user':'x','choice':0},now=45000)
 def test_pause_preserves_time(self):
  s=mutate(self.voting(),'pause',now=10000);self.assertEqual(s['remaining'],35);s=mutate(s,'resume',now=50000);self.assertEqual(s['deadline'],85000)
 def test_tie_default_and_one_close(self):
  s=mutate(self.voting(),'close',now=1);self.assertEqual(s['winner'],0)
  with self.assertRaises(ValueError):mutate(s,'close',now=2)
  s=self.voting()
  for u,c in [('x',1),('y',2)]:s=mutate(s,'vote',{'user':u,'choice':c},now=1)
  self.assertEqual(mutate(s,'close',now=2)['winner'],1)
 def test_five_rounds_and_approval(self):
  s=mutate(initial(),'start')
  for i in range(5):
   s=mutate(s,'open',now=0);old=s['scene'];s=mutate(s,'close',now=1);self.assertEqual(s['scene'],old);s=mutate(s,'approve');self.assertTrue(0<=s['oxygen']<=100)
  self.assertEqual(s['status'],'ended');self.assertEqual(len(s['history']),5)
 def test_reset_version_monotonic(self):
  s=mutate(self.voting(),'reset');self.assertEqual(s['version'],3);self.assertEqual(s['status'],'ready')
if __name__=='__main__':unittest.main()

class ResultTests(unittest.TestCase):
 def close(self,choices=(),**values):
  s=initial();s.update(values);s=mutate(mutate(s,'start',now=0),'open',now=0)
  for i,c in enumerate(choices):s=mutate(s,'vote',{'user':str(i),'choice':c},now=1)
  return mutate(s,'close',now=100)
 def test_honest_tie_and_zero(self):
  for votes,resolution,counts,winner,tied in [((),'no_votes',[0,0,0],0,[]),((1,2),'tie',[0,1,1],1,[1,2]),((2,2,0),'winner',[1,0,2],2,[2])]:
   r=self.close(votes)['result'];self.assertEqual((r['resolution'],r['counts'],r['winner'],r['tied']),(resolution,counts,winner,tied));self.assertEqual(r['total'],len(votes));self.assertEqual(r['reveal_until']-r['closed_at'],7000)
 def test_actual_clamped_effects_and_new_memory(self):
  s=self.close((0,),oxygen=99,energy=2,chaos=3);r=s['result']
  self.assertEqual(r['effects'],dict(oxygen=1,energy=-2,chaos=-3));self.assertEqual([m['id'] for m in r['new_memory']],['life_support_stable'])
  self.assertEqual(s['scene'],initial()['scene']);self.assertEqual(mutate(s,'approve',now=101)['result'],r)
 def test_previous_facts_not_reported_as_new(self):
  s=self.close((0,),facts={'life_support_stable':True});self.assertEqual(s['result']['new_memory'],[])

class HonestNarrationTests(unittest.TestCase):
 def test_zero_votes_do_not_claim_community_decision(self):
  s=mutate(mutate(initial(),'start',now=0),'open',now=0)
  s=mutate(s,'close',now=100)
  self.assertIn('No votes were cast; default A was selected.',s['draft'])
  self.assertNotIn('Your community chose',s['draft'])
