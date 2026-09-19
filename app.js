const $ = id => document.getElementById(id);
const sample = 'Copper sample. Heated from 22°C to 42°C in 120 seconds. Mass: 50 g.';
let record, screen = 'welcome';
const fields = [['material','Material',''],['mass','Mass',' g'],['start','Start temperature','°C'],['end','End temperature','°C'],['duration','Duration',' s'],['method','Method','']];
function show(id) {
  document.querySelectorAll('.screen').forEach(el => { el.hidden = el.id !== id; });
  screen = id;
  $('back').hidden = id === 'welcome' || id === 'saved';
  window.scrollTo({top:0,behavior:'instant'});
  const heading = $(id).querySelector('h1');
  heading.tabIndex = -1;
  heading.focus({preventScroll:true});
}
function start(useSample) {
  record = {title:useSample?'Heating copper':'Untitled experiment',material:useSample?'Copper':'',mass:useSample?'50':'',start:useSample?'22':'',end:useSample?'42':'',duration:useSample?'120':'',method:'',source:useSample?sample:'',note:'',sample:useSample};
  $('source-note').textContent = record.source;
  $('user-message').hidden = !useSample;
  $('method-choices').hidden = !useSample;
  $('note').value = '';
  $('prompt').textContent = useSample ? 'I have the material, mass, temperatures and duration. What method did you use to measure temperature?' : 'Add your observation below. This demo keeps your original note; you will enter the structured details yourself.';
  show('capture');
}
function delta() {
  if(record.start === '' || record.end === '') return 'Not recorded';
  const value = Math.round((Number(record.end)-Number(record.start))*1e6)/1e6;
  if(!Number.isFinite(value)) return 'Not recorded';
  return (value>0?'+':'') + value + '°C';
}
function review() {
  $('record-title').textContent=record.title;
  $('details').replaceChildren();
  for(const [key,label,unit] of fields){
    const row=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');
    dt.textContent=label;dd.textContent=record[key] === '' ? 'Not recorded' : record[key]+unit;
    row.append(dt,dd);$('details').append(row);
  }
  $('delta').textContent=delta();show('review');
}
function edit() {
  for(const key of ['title',...fields.map(f=>f[0])]) $('details-form').elements.namedItem(key).value=record[key];
  show('edit-screen');
}
$('sample').addEventListener('click',()=>start(true));
$('own').addEventListener('click',()=>start(false));
document.querySelectorAll('[data-method]').forEach(button=>button.addEventListener('click',()=>{record.method=button.dataset.method;review();}));
$('note-form').addEventListener('submit',e=>{
  e.preventDefault();const text=$('note').value.trim();if(!text)return;
  if(!record.source){record.source=text;$('source-note').textContent=text;$('user-message').hidden=false;$('method-choices').hidden=false;$('prompt').textContent='Your original note is preserved. How was temperature measured? You can enter the remaining fields on the review screen.';}
  else {record.note=text;$('prompt').textContent='Added to the exported record as an additional note. Choose a method to review the details.';}
  $('note').value='';
});
$('edit').addEventListener('click',edit);
$('details-form').addEventListener('submit',e=>{e.preventDefault();for(const key of ['title',...fields.map(f=>f[0])])record[key]=$('details-form').elements.namedItem(key).value.trim();record.title=record.title||'Untitled experiment';review();});
$('back').addEventListener('click',()=>{if(screen==='edit-screen')review();else if(screen==='review')show('capture');else show('welcome');});
$('save').addEventListener('click',()=>{
  record.savedAt=new Date().toISOString();
  try{localStorage.setItem('fieldnote-latest-v1',JSON.stringify(record));$('save-status').textContent='Saved on this device. Download a copy to keep the record outside this browser.';}
  catch{$('save-status').textContent='Browser storage is unavailable. Your record is ready to download; it will be lost if you close this page.';}
  $('saved-title').textContent=record.title;
  $('saved-summary').textContent=(record.material||'Material not recorded')+' · '+delta()+' temperature change';
  show('saved');
});
$('return-review').addEventListener('click',review);
$('restart').addEventListener('click',()=>show('welcome'));
$('download').addEventListener('click',()=>{
  const text=['# '+record.title,'','Scripted prototype record. '+(record.sample?'Started from synthetic sample data.':'Entered by the user.'),'','## Recorded details',...fields.map(([key,label,unit])=>'- '+label+': '+(record[key]===''?'Not recorded':record[key]+unit)),'','## Derived result','Temperature change: '+delta(),'Formula: end temperature minus start temperature, in degrees Celsius. No uncertainty estimate.','','## Original note',record.source,'','## Additional note',record.note||'None recorded','','Saved at (UTC): '+record.savedAt,''].join('\n');
  const url=URL.createObjectURL(new Blob([text],{type:'text/markdown;charset=utf-8'}));
  const a=document.createElement('a');a.href=url;a.download='fieldnote-record.md';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
// Restore only data explicitly saved with Save record. No network requests.
try{const saved=JSON.parse(localStorage.getItem('fieldnote-latest-v1'));if(saved&&typeof saved==='object'&&['title','source','note','savedAt',...fields.map(f=>f[0])].every(key=>typeof saved[key]==='string')){const button=document.createElement('button');button.className='plain';button.textContent='Open last saved record';button.addEventListener('click',()=>{record=saved;$('source-note').textContent=record.source;$('user-message').hidden=!record.source;$('method-choices').hidden=!record.source;$('note').value='';$('prompt').textContent='This is your saved observation. You can add a note or choose a method before reviewing it.';review();});$('welcome').querySelector('.actions').append(button);}}catch{}
