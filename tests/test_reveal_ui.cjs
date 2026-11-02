// Socket-free UI regression tests using the shipped module and a minimal DOM.
const {readFileSync}=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
let now=1000;const intervals=[];
const app={innerHTML:''},body={classList:{add(){},toggle(){}}};
const context={URLSearchParams,location:{search:'?overlay=private-test-token'},localStorage:{getItem(){return null}},document:{body,querySelector(s){return s==='#app'?app:null},querySelectorAll(){return []}},window:{addEventListener(){}},setInterval(fn){intervals.push(fn)},setTimeout(){},clearTimeout(){},fetch:async()=>{throw Error('offline')},Date:class extends Date{static now(){return now}},console};
vm.createContext(context);
const source=readFileSync('dist/app.js','utf8').replace(/^import .*;\r?\n/,'').replace(/boot\(\);\s*$/,'');
vm.runInContext(source,context);
function run(code){return vm.runInContext(code,context)}
run('render()');assert.match(app.innerHTML,/Connecting to live session/);assert.doesNotMatch(app.innerHTML,/A signal in the silence/);
run(`live=true;received=true;connection='Connected';state=initial();state.status='pending';state.draft='PRIVATE NEXT SCENE';state.result={id:1,choice:'<b>Repair</b>',winner:0,counts:[0,0,0],total:0,tied:[],resolution:'no_votes',effects:{oxygen:1,energy:-2,chaos:-3},new_memory:[],closed_at:1000,reveal_until:8000};render()`);
assert.match(app.innerHTML,/No votes · default A/);assert.match(app.innerHTML,/A: 0 · B: 0 · C: 0/);assert.match(app.innerHTML,/oxygen \+1/);assert.match(app.innerHTML,/No new facts gained/);assert.match(app.innerHTML,/&lt;b&gt;Repair/);assert.doesNotMatch(app.innerHTML,/PRIVATE NEXT SCENE/);
run(`state.result.resolution='tie';state.result.tied=[1,2];render()`);assert.match(app.innerHTML,/Tie B \/ C/);
assert.match(app.innerHTML,/20261102-dream1/);assert.doesNotMatch(app.innerHTML,/Your story preview/);
now=7999;assert.equal(run('!!revealing()'),true);intervals[0]();assert.match(app.innerHTML,/result-card/);now=8000;assert.equal(run('!!revealing()'),false);intervals[0]();assert.doesNotMatch(app.innerHTML,/result-card/);assert.match(app.innerHTML,/awaiting host approval/);assert.doesNotMatch(app.innerHTML,/PRIVATE NEXT SCENE/);assert.match(app.innerHTML,/!a/);assert.match(app.innerHTML,/!b/);assert.match(app.innerHTML,/!c/);
run(`state.votes={one:1,two:1,three:2};render()`);
assert.match(app.innerHTML,/class="broadcast-percent">67%/);assert.match(app.innerHTML,/class="broadcast-percent">33%/);assert.match(app.innerHTML,/class="broadcast-count">2 votes/);assert.match(app.innerHTML,/class="broadcast-count">1 vote/);assert.match(app.innerHTML,/class="broadcast-count">0 votes/);
assert.match(app.innerHTML,/Oxygen/);assert.match(app.innerHTML,/Energy/);assert.match(app.innerHTML,/Chaos/);
run(`state.result.reveal_until=15000;state.status='approved';state.title='Approved Chapter 2';render()`);assert.match(app.innerHTML,/result-card/);assert.doesNotMatch(app.innerHTML,/Approved Chapter 2/);now=15000;intervals[0]();assert.match(app.innerHTML,/Approved Chapter 2/);
run(`live=false;received=false;connection='Offline'`);assert.match(run(`token==='demo'?'sample':broadcast()`),/LIVE OVERLAY/);
async function checkRecovery(){
 run(`live=false;received=false;connection='Disconnected';`);
 context.fetch=async()=>({ok:true,json:async()=>run('JSON.parse(JSON.stringify(state))')});
 await run('refresh()');assert.equal(run('live'),true);assert.match(app.innerHTML,/LIVE MODE · Connected/);
 context.fetch=async()=>{throw Error('offline')};await run('refresh()');assert.match(app.innerHTML,/Disconnected/);
 context.fetch=async()=>({ok:true,json:async()=>run('JSON.parse(JSON.stringify(state))')});
 await run('refresh()');assert.match(app.innerHTML,/LIVE MODE · Connected/);assert.doesNotMatch(app.innerHTML,/Disconnected/);
 context.fetch=async()=>({ok:false});await run('refresh()');assert.match(app.innerHTML,/Access unavailable/);assert.doesNotMatch(app.innerHTML,/A signal in the silence/);
}
checkRecovery().then(()=>console.log('Reveal UI checks passed: timing, totals, deltas, ties, empty memory, escaping, approval privacy, unavailable live source, identical-state reconnect, initial recovery, access rejection.')).catch(e=>{console.error(e);process.exitCode=1});
