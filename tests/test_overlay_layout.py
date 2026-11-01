"""Real Chrome layout checks, skipped when headless Chrome cannot run.
Uses only temporary files and an isolated Chrome profile, never the saved DB.
"""
import html,json,os,re,shutil,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class OverlayLayoutTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.chrome=shutil.which('google-chrome') or shutil.which('chromium')
  mac='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
  if not cls.chrome and Path(mac).exists():cls.chrome=mac
  if not cls.chrome:raise unittest.SkipTest('Chrome/Chromium not installed')
  with tempfile.TemporaryDirectory(prefix='streamquest-browser-probe-') as d:
   try:r=subprocess.run([cls.chrome,'--headless','--disable-gpu','--no-first-run','--user-data-dir='+d,'--dump-dom','about:blank'],capture_output=True,timeout=20)
   except (OSError,subprocess.TimeoutExpired):raise unittest.SkipTest('Headless Chrome unavailable in this environment')
   if r.returncode:raise unittest.SkipTest('Headless Chrome launch blocked in this environment')
 def check_layout(self,width,height,reveal=False,reduced=False):
  source=(ROOT/'dist/app.js').read_text()
  source=re.sub(r'^import .*;\n','',source)
  source=re.sub(r'boot\(\);\s*$','',source)
  fixture="""
  live=true;received=true;connection='Connected';state=initial();state.status='pending';
  state.scene='extraordinary '.repeat(100).trim();state.draft='PRIVATE DRAFT';
  """
  if reveal:fixture+="""state.result={id:1,choice:'Investigate the signal',winner:1,counts:[0,1,1],total:2,tied:[1,2],resolution:'tie',effects:{oxygen:-8,energy:-5,chaos:15},new_memory:[{id:'signal_decoded',title:'Signal decoded',description:'The signal contains a rescue frequency that returns in the finale.'}],reveal_until:Date.now()+7000};"""
  fixture+="""
  render();
  const selectors=['.broadcast-mode',... (state.result?['.result-card','.result-card h3','.result-effects','.result-memory','.result-card small']:['.broadcast-story h1','.broadcast-story p','.broadcast-vote','.broadcast-choices>div'])];
  const boxes=selectors.flatMap(s=>[...document.querySelectorAll(s)].map(e=>{const r=e.getBoundingClientRect();return {selector:s,left:r.left,top:r.top,right:r.right,bottom:r.bottom}}));
  const card=document.querySelector('.result-card');
  const report={width:innerWidth,height:innerHeight,boxes,scrollHeight:document.documentElement.scrollHeight,animation:card?getComputedStyle(card).animationName:null,privateDraft:document.querySelector('#app').textContent.includes('PRIVATE DRAFT')};
  const pre=document.createElement('pre');pre.id='layout-report';pre.textContent=JSON.stringify(report);document.body.append(pre);
  """
  with tempfile.TemporaryDirectory(prefix='streamquest-layout-') as d:
   page=Path(d)/'fixture.html'
   css=(ROOT/'dist/style.css').read_text()
   page.write_text('<!doctype html><meta charset="utf-8"><style>'+css+'</style><div id="app"></div><div id="toast"></div><script>'+source+fixture+'</script>')
   args=[self.chrome,'--headless','--disable-gpu','--no-first-run','--hide-scrollbars','--user-data-dir='+d+'/profile',f'--window-size={width},{height}','--dump-dom']
   if reduced:args+=['--force-prefers-reduced-motion=reduce']
   r=subprocess.run(args+[page.as_uri()+'?overlay=fixture'],capture_output=True,text=True,timeout=30)
   self.assertEqual(r.returncode,0,'Headless Chrome failed')
   match=re.search(r'<pre id="layout-report">(.*?)</pre>',r.stdout,re.S)
   self.assertIsNotNone(match,'Layout script did not finish')
   report=json.loads(html.unescape(match[1]))
  self.assertFalse(report['privateDraft'])
  self.assertEqual(len(report['boxes']),6 if reveal else 7)
  for box in report['boxes']:
   self.assertGreaterEqual(box['left'],-1,box);self.assertGreaterEqual(box['top'],-1,box)
   self.assertLessEqual(box['right'],report['width']+1,box);self.assertLessEqual(box['bottom'],report['height']+1,box)
  self.assertLessEqual(report['scrollHeight'],report['height']+1,report)
  if reduced and reveal:self.assertEqual(report['animation'],'none')
 def test_long_story_and_all_choices_at_both_sizes(self):
  for size in [(1000,550),(1920,1080)]:
   with self.subTest(size=size):self.check_layout(*size)
 def test_reveal_and_reduced_motion_at_both_sizes(self):
  for size in [(1000,550),(1920,1080)]:
   for reduced in [False,True]:
    with self.subTest(size=size,reduced=reduced):self.check_layout(*size,reveal=True,reduced=reduced)
