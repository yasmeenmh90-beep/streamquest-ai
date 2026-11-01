"""State-derived story continuity. No model controls game rules."""
FACTS = {
 'life_support_stable':('Life support repaired','Repairs preserve 2 extra oxygen on later rounds.'),
 'signal_decoded':('Signal decoded','The signal contains a rescue frequency that returns in the finale.'),
 'rescue_contact':('Rescue fleet contacted','An early distress call gives the crew a confirmed rescue route.'),
 'engineer_onboard':('Engineer rescued','The engineer restores 3 energy on later rounds.'),
 'navigation_mapped':('Navigation mapped','The scanned core provides coordinates for the final jump.'),
 'station_route':('Station route charted','The crew has a known destination for evacuation.'),
 'shields_reinforced':('Shields reinforced','Reinforced shields prevent up to 4 oxygen loss on later rounds.'),
 'beacon_followed':('Beacon followed','The beacon leads the crew to a hidden passage.'),
 'safe_detour':('Safe detour taken','The crew avoided the densest debris.'),
 'station_powered':('Station power restored','The station can support an evacuation.'),
 'manual_dock':('Manual docking completed','The ship has a direct escape corridor.'),
 'drone_deployed':('Rescue drone deployed','The drone can guide the rescue fleet.')
}
ROUND_FACTS=[['life_support_stable','signal_decoded','rescue_contact'],['engineer_onboard','navigation_mapped','station_route'],['shields_reinforced','beacon_followed','safe_detour'],['station_powered','manual_dock','drone_deployed']]
def memory(s):
 return [dict(id=k,title=FACTS[k][0],description=FACTS[k][1]) for k in s.get('facts',{}) if k in FACTS]
def remember(s,winner):
 s.setdefault('facts',{})
 if s['round']<len(ROUND_FACTS):s['facts'][ROUND_FACTS[s['round']][winner]]=True
 s['memory']=memory(s)
def callback(s):
 f=s.get('facts',{});n=s['round']+1
 if n==1:
  return 'Your repaired life support buys time to help the stranger.' if f.get('life_support_stable') else 'The decoded signal belongs to the engineer; they recognize your rescue frequency.' if f.get('signal_decoded') else 'The rescue fleet confirms it heard your distress call, but needs a safe rendezvous.'
 if n==2:
  return 'The rescued engineer recognizes the beacon and promises to restore energy as you travel.' if f.get('engineer_onboard') else 'Coordinates from your scanned navigation core reveal a gap in the debris.' if f.get('navigation_mapped') else 'Your chosen station route now crosses the debris field; the destination is known, but the crossing remains uncertain.'
 if n==3:
  return 'The shields you reinforced absorb the worst impacts, protecting your remaining oxygen.' if f.get('shields_reinforced') else 'Following the beacon reveals a hidden approach to the station.' if f.get('beacon_followed') else 'Your safe detour avoided the worst debris and brings you to the station from the far side.'
 return 'The power you shared has brought the docking lights back online.' if f.get('station_powered') else 'Your manual docking created a direct escape corridor for the final jump.' if f.get('manual_dock') else 'Your rescue drone broadcasts the ship location to the waiting fleet.'
def ending(s,winner):
 f=s.get('facts',{})
 if s['oxygen']==0 or s['energy']==0:
  route='emergency_rescue';text='The Aurora exhausts its reserves. The crew abandons the ship and signals for emergency rescue; survival now depends on outside help.'
 elif winner==0:
  route='crew_reunion';text='Everyone boards the Aurora for a shared journey home.'+(' The engineer you rescued keeps the engines running.' if f.get('engineer_onboard') else ' The crew works together to stabilize the engines.')
 elif winner==1:
  route='charted_jump' if f.get('navigation_mapped') else 'beacon_jump' if f.get('beacon_followed') else 'risky_jump'
  text='The scanned coordinates turn your final jump into a mapped passage home.' if route=='charted_jump' else 'The beacon you followed lights a hidden jump corridor home.' if route=='beacon_jump' else 'Without mapped coordinates, the crew makes a risky jump and emerges far from the intended destination.'
 else:
  confirmed=any(f.get(k) for k in ['rescue_contact','signal_decoded','drone_deployed'])
  route='fleet_rendezvous' if confirmed else 'uncertain_wait';text='Your earlier rescue signal guides the fleet directly to the Aurora.' if confirmed else 'No rescue link was established earlier. The crew waits at the station and broadcasts a new call for help.'
 s['ending']=dict(id=route,title=route.replace('_',' ').title());return text+f" Final reserves: {s['oxygen']}% oxygen and {s['energy']}% energy."
