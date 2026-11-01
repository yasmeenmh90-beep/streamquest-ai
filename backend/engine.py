"""Deterministic single-session engine. Caller serializes mutations."""
import time,copy
from .story import remember,callback,ending
CHAPTERS=[
('A signal in the silence','Aboard the Aurora, oxygen is falling. An unfamiliar signal pulses from a sealed corridor.',['Repair life support','Investigate the signal','Send a distress call']),
('The hidden passenger','A stranded engineer and damaged navigation core await. A distant station flickers into view.',['Help the engineer','Scan the navigation core','Head for the station']),
('Through the debris','Orbital debris blocks the route. An old beacon broadcasts incomplete coordinates.',['Reinforce the shields','Follow the beacon','Take the long route']),
('The last transmission','The station answers, but its docking system is dark. A rescue shuttle can make one approach.',['Share emergency power','Attempt manual docking','Launch a rescue drone']),
('A way home','The Aurora reaches the edge of the storm. A narrow jump window opens.',['Bring everyone aboard','Chart an untested jump','Wait for the rescue fleet'])]
def initial():
 return dict(round=0,status='ready',oxygen=72,energy=85,chaos=50,votes={},history=[],remaining=45,deadline=None,version=0,scene=CHAPTERS[0][1],draft=None,narrator='Prepared story',title=CHAPTERS[0][0],choices=CHAPTERS[0][2],winner=None,seen=[],facts={},memory=[],consequences=[],ending=None,result=None)
def mutate(s,action,data=None,now=None):
 data=data or {};now=time.time()*1000 if now is None else now;s=copy.deepcopy(s)
 if action=='reset':
  n=initial();n['version']=s['version']+1;return n
 if action=='start' and s['status']=='ready':s['status']='approved'
 elif action=='open' and s['status']=='approved':s.update(status='voting',deadline=now+s['remaining']*1000)
 elif action=='pause' and s['status']=='voting':s.update(status='paused',remaining=max(0,(s['deadline']-now)/1000),deadline=None)
 elif action=='resume' and s['status']=='paused':s.update(status='voting',deadline=now+s['remaining']*1000)
 elif action=='vote':
  if s['status']!='voting' or now>=s['deadline']:raise ValueError('Voting is closed')
  user=str(data.get('user','')).strip();choice=data.get('choice');event=data.get('event')
  if not user or len(user)>100 or type(choice)!=int or choice not in range(3):raise ValueError('Invalid vote')
  if event and event in s['seen']:return s
  if event:s['seen']=(s['seen']+[event])[-5000:]
  s['votes'][user]=choice
 elif action=='close' and s['status']=='voting':
  counts=[list(s['votes'].values()).count(i) for i in range(3)];winner=counts.index(max(counts))
  before={k:s[k] for k in ['oxygen','energy','chaos']};facts=s.get('facts',{});effects={'oxygen':[10,-8,-4][winner],'energy':[-8,-5,-12][winner],'chaos':[-12,15,3][winner]};notes=[]
  if facts.get('life_support_stable'):effects['oxygen']+=2;notes.append('Earlier life-support repairs preserve 2 oxygen.')
  if facts.get('engineer_onboard'):effects['energy']+=3;notes.append('Your rescued engineer restores 3 energy.')
  if facts.get('shields_reinforced') and effects['oxygen']<0:effects['oxygen']+=min(4,-effects['oxygen']);notes.append('Your reinforced shields reduce oxygen loss.')
  for k,d in effects.items():s[k]=min(100,max(0,s[k]+d))
  old_facts=set(s.get('facts',{}));chosen=s['choices'][winner];remember(s,winner)
  consequences=[f"{k.title()} {s[k]-before[k]:+d}" for k in effects]+notes
  s['consequences']=consequences;s['history'].append(dict(round=s['round']+1,choice=chosen,votes=sum(counts),winner=winner,counts=counts,effects={k:s[k]-before[k] for k in effects},callbacks=notes))
  s['result']=dict(id=s['version']+1,round=s['round']+1,choice=chosen,winner=winner,counts=counts,total=sum(counts),tied=[i for i,c in enumerate(counts) if c==max(counts)] if sum(counts) else [],resolution='no_votes' if not sum(counts) else 'tie' if counts.count(max(counts))>1 else 'winner',effects={k:s[k]-before[k] for k in effects},new_memory=[m for m in s['memory'] if m['id'] not in old_facts],closed_at=now,reveal_until=now+7000)
  s.update(status='pending',deadline=None,winner=winner,narrator='Prepared branching story')
  n=s['round']+1;intro='No votes were cast; default A was selected. ' if not sum(counts) else 'The tie was resolved by A/B/C order. ' if counts.count(max(counts))>1 else f'Your community chose to {chosen.lower()}. ';s['draft']=intro+(CHAPTERS[n][1]+' '+callback(s) if n<5 else ending(s,winner))
 elif action=='approve' and s['status']=='pending':
  s['round']+=1;s.update(scene=s['draft'],draft=None,votes={},winner=None,remaining=45,seen=[])
  if s['round']>=5:s.update(status='ended',title='The Aurora remembers')
  else:s.update(status='approved',title=CHAPTERS[s['round']][0],choices=CHAPTERS[s['round']][2])
 else:raise ValueError('Action unavailable in current state')
 s['version']+=1;return s
