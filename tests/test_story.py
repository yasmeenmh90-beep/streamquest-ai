import unittest,itertools
from backend.engine import initial,mutate
class StoryTests(unittest.TestCase):
 def play(self,path):
  s=mutate(initial(),'start')
  for i,w in enumerate(path):
   s=mutate(s,'open',now=0);s=mutate(s,'vote',{'user':'viewer','choice':w},now=1);s=mutate(s,'close',now=2);s=mutate(s,'approve')
  return s
 def test_earlier_choice_changes_later_resources(self):
  repaired=self.play([0,0]);unrepaired=self.play([1,0])
  self.assertTrue(any('repairs' in x for x in repaired['history'][1]['callbacks']))
  self.assertFalse(any('repairs' in x for x in unrepaired['history'][1]['callbacks']))
 def test_engineer_is_remembered_in_later_scene(self):
  s=self.play([0,0]);self.assertIn('rescued engineer',s['scene']);self.assertIn('engineer_onboard',s['facts'])
 def test_scanned_navigation_changes_final_jump(self):
  a=self.play([0,1,0,0,1]);b=self.play([0,0,0,0,1]);self.assertEqual(a['ending']['id'],'charted_jump');self.assertEqual(b['ending']['id'],'risky_jump');self.assertNotEqual(a['scene'],b['scene'])
 def test_all_243_paths_finish_with_valid_resources_and_memory(self):
  endings=set()
  for path in itertools.product(range(3),repeat=5):
   s=self.play(path);self.assertEqual(s['status'],'ended');self.assertEqual(len(s['history']),5);self.assertEqual(len(s['memory']),4)
   for k in ['oxygen','energy','chaos']:self.assertTrue(0<=s[k]<=100)
   endings.add(s['ending']['id'])
  self.assertGreaterEqual(len(endings),5)
