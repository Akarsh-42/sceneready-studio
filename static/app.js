'use strict';
const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let report = null, previous = null, activeTab = 'tasks', controller = null, reviewing = null;
const example = 'EXT. MUMBAI STREET — NIGHT\n\nA courier leaves a small café and walks down the pavement. Two adult actors cross paths under a streetlight.\n\nProduction notes: six crew members, one handheld camera, two battery-powered LED lights. No drone, no stunts, no road closure, no minors, and no animals. Exact street, shoot date, and location permission are not yet confirmed.';
function loadExample() {
  $('title').value = 'The Last Local'; $('city').value = 'Mumbai, India'; $('crew').value = '6';
  $('location').value = ''; $('date').value = ''; $('script').value = example; countCharacters();
  $('status').textContent = 'Example brief loaded. Select Build production plan to start.';
}
function countCharacters(){ $('character-count').textContent = `${$('script').value.length.toLocaleString()} / 12,000`; }
function safeLink(url, text) {
  try { const u = new URL(url); if (!['https:','http:'].includes(u.protocol)) return esc(text); }
  catch { return esc(text); }
  return `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(text)} ↗</a>`;
}
function tags(task) {
  return `<div class="tags"><span class="tag ${task.priority === 'high' ? 'high' : ''}">${esc(task.priority)} priority</span><span class="tag">${esc(task.department)}</span><span class="tag ${task.evidence_status === 'excerpt_matched' ? 'matched' : ''}">${task.evidence_status === 'excerpt_matched' ? 'Excerpt matched' : 'Needs evidence'}</span>${task.review_status === 'reviewed' ? '<span class="tag reviewed">Reviewed</span>' : ''}</div>`;
}
function citationHTML(c) { return `<div class="citations">${safeLink(c.url,c.title)}<blockquote>“${esc(c.quote)}”</blockquote></div>`; }
function renderTasks() {
  const filter = $('task-filter').value;
  const tasks = report.tasks.filter(t => filter === 'all' || t.review_status === filter || t.priority === filter || t.evidence_status === filter);
  if (!tasks.length) return '<div class="empty-state"><h3>No tasks in this view.</h3><p>Choose another filter to see the rest of the plan.</p></div>';
  return tasks.map(t => `<article class="task-card"><div class="task-top">${tags(t)}<span class="task-id">${esc(t.id)}</span></div><h3>${esc(t.title)}</h3><p class="action">${esc(t.edited_action || t.action)}</p><p>${esc(t.rationale)}</p><details><summary>Evidence & verification</summary>${t.citations.length ? t.citations.map(citationHTML).join('') : '<p>No matching source excerpt supports this task. Treat it as a planning suggestion or an unresolved question.</p>'}<p><b>Verify:</b> ${esc(t.needs_verification)}</p>${t.edited_action ? '<p>The action was edited by a reviewer; source citations belong to the original generated task.</p>' : ''}</details>${t.review_note ? `<p><b>Review note:</b> ${esc(t.review_note)}</p>` : ''}<div class="task-bottom"><span>${esc(t.scene_ids.join(', ') || 'Production-wide')} · ${esc(t.owner || t.department)}</span><button class="secondary" data-review="${esc(t.id)}">${t.review_status === 'reviewed' ? 'Edit review' : 'Review & assign'} ↗</button></div></article>`).join('');
}
function renderScenes() {
  return `<div class="scene-card"><p>${esc(report.breakdown.summary)}</p></div>` + report.breakdown.scenes.map(s=>`<article class="scene-card"><div class="tags"><span class="tag">${esc(s.id)}</span><span class="tag">${esc(s.setting)}</span><span class="tag">${esc(s.time_of_day)}</span></div><h3>${esc(s.heading)}</h3>${s.script_excerpt ? `<blockquote>${esc(s.script_excerpt)}</blockquote>` : '<p>No matching script excerpt. Review this extraction.</p>'}<div class="scene-grid"><div><b>People</b><p>${esc(s.people.join(', ') || 'Not specified')}</p></div><div><b>Equipment</b><p>${esc(s.equipment.join(', ') || 'Not specified')}</p></div></div><p><b>Production needs:</b> ${esc(s.production_needs.join(' · ') || 'Not specified')}</p></article>`).join('');
}
function renderSources() {
  if (!report.sources.length) return '<div class="empty-state"><h3>No evidence to inspect yet.</h3><p>This run returned no usable sources. Requirements remain unknown.</p></div>';
  return '<p class="fineprint">Domain labels describe the host only. They do not verify accuracy, publication date, or applicability.</p>' + report.sources.map(s=>`<article class="source-card"><div class="tags"><span class="tag">${esc(s.id)}</span><span class="tag">${s.government_domain ? 'Government domain' : 'Check source authority'}</span></div><h3>${esc(s.title)}</h3>${safeLink(s.url,s.domain)}<p>Retrieved ${esc(new Date(s.retrieved_at).toLocaleString())} · Publication date not checked</p><details><summary>Inspect retrieved excerpts</summary>${s.excerpts.map(x=>`<blockquote>${esc(x)}</blockquote>`).join('') || '<p>No excerpts returned.</p>'}</details></article>`).join('');
}
function renderTrace() {
  return `<div class="trace-card"><div class="tags"><span class="tag">${esc(report.mode.replaceAll('_',' '))}</span><span class="tag">${esc(report.prompt_version)}</span></div><p>Run <span class="mono">${esc(report.run_id)}</span> · ${esc(report.elapsed_seconds)} seconds</p>${report.trace.map(t=>`<div class="trace-row"><b>${esc(t.stage)}</b><span>${esc(t.seconds)}s</span></div>${t.searches ? `<ul>${t.searches.map(s=>`<li>${esc(s.query)} — ${esc(s.status)}</li>`).join('')}</ul>` : ''}`).join('')}<p>Stages run in a fixed order. Model outputs can vary. Quoted text is matched in Python; truth and applicability still need review.</p><p>No permits were submitted, payments made, or messages sent.</p></div>`;
}
function render() {
  if (!report) return;
  $('scene-count').textContent = report.breakdown.scenes.length;
  $('source-count').textContent = report.sources.length;
  $('task-count').textContent = report.tasks.filter(t=>t.review_status !== 'reviewed').length;
  $('match-count').textContent = report.tasks.filter(t=>t.evidence_status === 'excerpt_matched').length;
  $('report-label').textContent = `${report.brief.title} · ${report.brief.city} · Run ${report.run_id}${report.mode === 'offline_rehearsal' ? ' · OFFLINE REHEARSAL' : ''}`;
  $('task-toolbar').hidden = activeTab !== 'tasks';
  $('report-content').innerHTML = ({tasks:renderTasks,scenes:renderScenes,evidence:renderSources,trace:renderTrace})[activeTab]();
  $('report-content').setAttribute('aria-labelledby', `tab-${activeTab}`);
  $('warning-box').hidden = !report.warnings.length;
  $('warning-box').innerHTML = `<details><summary>${report.warnings.length} research or validation notes to review</summary><ul>${report.warnings.map(w=>`<li>${esc(w)}</li>`).join('')}</ul></details>`;
  const questions = [...new Set([...report.breakdown.missing_details,...report.questions])];
  $('questions').hidden = !questions.length;
  $('questions').innerHTML = `<span class="eyebrow">BEFORE THE NEXT TAKE</span><h3>A few details will make this sharper.</h3><ul>${questions.map(q=>`<li>${esc(q)}</li>`).join('')}</ul><p class="fineprint">Update the brief and run it again. Each new plan requires a fresh review.</p>`;
  $('export-json').disabled = false; $('export-md').disabled = false;
}
function compareRuns() {
  $('comparison').hidden = !previous;
  if (!previous) return;
  const older = new Set(previous.tasks.map(t=>t.title.toLowerCase()));
  const newer = new Set(report.tasks.map(t=>t.title.toLowerCase()));
  const added = [...newer].filter(t=>!older.has(t)).length;
  const removed = [...older].filter(t=>!newer.has(t)).length;
  const changedFields = ['city','location','shoot_date','crew_size','script'].filter(k=>report.brief[k] !== previous.brief[k]);
  $('comparison').textContent = `Revision comparison: ${changedFields.length ? changedFields.map(x=>x.replaceAll('_',' ')).join(', ') + ' changed' : 'same brief rerun'}. ${added} task titles added; ${removed} removed. Title changes can reflect model wording. Reviews reset for the new run.`;
}
function selectTab(name) {
  activeTab = name;
  document.querySelectorAll('[data-tab]').forEach(b=>{const selected=b.dataset.tab===name;b.classList.toggle('selected',selected);b.setAttribute('aria-selected',String(selected));b.tabIndex=selected?0:-1;});
  render();
}
document.querySelectorAll('[data-tab]').forEach(b=>{
  b.addEventListener('click',()=>selectTab(b.dataset.tab));
  b.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key)) return;e.preventDefault();const tabs=[...document.querySelectorAll('[data-tab]')];let i=tabs.indexOf(b);i=e.key==='Home'?0:e.key==='End'?tabs.length-1:(i+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;tabs[i].click();tabs[i].focus();});
});
$('task-filter').addEventListener('change',render);
$('script').addEventListener('input',countCharacters);
$('example-button').addEventListener('click',loadExample);
$('empty-example').addEventListener('click',loadExample);
$('guide-button').addEventListener('click',()=>{$('guide').hidden=!$('guide').hidden;});
$('script-file').addEventListener('change',async event=>{
  const file=event.target.files[0]; if(!file) return;
  const isPdf=file.type==='application/pdf'||file.name.toLowerCase().endsWith('.pdf');
  try {
    if(!isPdf){
      if(file.size>50000 || !file.name.toLowerCase().endsWith('.txt')) throw new Error('Choose a plain .txt file under 50 KB or a PDF under 8 MiB.');
      const text=await file.text();
      if(text.length>12000)throw new Error('The text exceeds 12,000 characters. Use a shorter excerpt.');
      $('script').value=text;countCharacters();$('status').textContent='Text imported. Review it before building the plan.';
      return;
    }
    if(file.size>8*1024*1024)throw new Error('Choose a PDF under 8 MiB.');
    const headers={'Content-Type':'application/pdf'};
    const accessCode=$('access-code').value;
    if(accessCode)headers.Authorization=`Bearer ${accessCode}`;
    $('status').textContent='Gemini is extracting the screenplay…';
    const response=await fetch('/api/extract-document',{method:'POST',headers,body:file});
    let body={};try{body=await response.json();}catch{}
    if(!response.ok)throw new Error(typeof body.detail==='string'?body.detail:`PDF extraction failed (${response.status}).`);
    if(typeof body.text!=='string'||body.text.length<30)throw new Error('The PDF did not contain enough usable screenplay text.');
    $('script').value=body.text;countCharacters();
    $('status').textContent=body.truncated?'PDF imported and limited to 12,000 characters. Review the ending before building the plan.':'PDF imported with Gemini. Review the extracted text before building the plan.';
  } catch(error) {
    $('status').textContent=error.message;
  } finally {
    event.target.value='';
  }
});
function eventReceived(event) {
  if(event.type==='stage') {
    const node=document.querySelector(`[data-stage="${event.stage}"]`);
    if(node) node.className=event.status;
    $('status').textContent=`${event.stage.charAt(0).toUpperCase()+event.stage.slice(1)}: ${event.status === 'running' ? 'in progress…' : 'complete'}`;
  }
  if(event.type==='research') $('status').textContent=`Research ${event.completed}/${event.total}: ${event.status.replaceAll('_',' ')}`;
  if(event.type==='error') throw new Error(event.message);
  if(event.type==='result') { previous=report;report=event.report;render();compareRuns();$('run-time').textContent=`Completed in ${report.elapsed_seconds}s`;$('status').textContent='Plan created. Review the actions and evidence before using it.'; }
}
$('brief-form').addEventListener('submit',async event=>{
  event.preventDefault();if(controller) return;
  const brief={title:$('title').value,city:$('city').value,crew_size:Number($('crew').value),location:$('location').value,shoot_date:$('date').value||null,script:$('script').value};
  controller=new AbortController();$('brief-fields').disabled=true;$('example-button').disabled=true;$('cancel-button').hidden=false;
  $('export-json').disabled=true;$('export-md').disabled=true;$('task-toolbar').hidden=true;$('questions').hidden=true;$('warning-box').hidden=true;$('comparison').hidden=true;
  document.querySelectorAll('[data-stage]').forEach(n=>n.className='');
  document.querySelectorAll('[data-tab]').forEach(n=>n.disabled=true);
  $('report-content').innerHTML='<div class="empty-state"><div class="empty-icon">◷</div><h3>Your production desk is at work.</h3><p>The live stages above show what is happening.<br>A completed plan appears after validation.</p></div>';
  $('status').textContent='Starting the workflow…';$('run-time').textContent='Run in progress';
  let completed=false;
  try {
    const headers = {'Content-Type': 'application/json'};
    const accessCode = $('access-code').value;
    if (accessCode) headers.Authorization = `Bearer ${accessCode}`;
    const response=await fetch('/api/run',{method:'POST',headers,body:JSON.stringify(brief),signal:controller.signal});
    if(!response.ok){let message=`Request failed (${response.status}).`;try{const body=await response.json();if(typeof body.detail==='string')message=body.detail;else if(Array.isArray(body.detail))message=body.detail.map(e=>`${e.loc.at(-1)}: ${e.msg}`).join('; ');}catch{}throw new Error(message);}
    const reader=response.body.getReader(), decoder=new TextDecoder();let buffer='';
    const consume=line=>{if(!line.trim())return;const parsed=JSON.parse(line);eventReceived(parsed);if(parsed.type==='result')completed=true;};
    while(true){const {done,value}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});let newline;while((newline=buffer.indexOf('\n'))>=0){consume(buffer.slice(0,newline));buffer=buffer.slice(newline+1);}}
    buffer+=decoder.decode();consume(buffer);
    if(!completed)throw new Error('The connection ended before a completed report arrived.');
  } catch(error) {
    controller.abort();
    const message=error.name==='AbortError'?'Run cancelled. Provider work already started may still incur usage.':error.message;
    $('status').textContent=message+(report?' Showing the last completed report.':'');$('run-time').textContent='Run not completed';
    document.querySelectorAll('[data-stage].running').forEach(n=>n.className='failed');
    if(report){render();compareRuns();}else $('report-content').innerHTML=`<div class="empty-state"><h3>This run needs another take.</h3><p>${esc(message)}</p><p>Your brief is still available on the left.</p></div>`;
  } finally {
    controller=null;$('brief-fields').disabled=false;$('example-button').disabled=false;$('cancel-button').hidden=true;
    document.querySelectorAll('[data-tab]').forEach(n=>n.disabled=false);
  }
});
$('cancel-button').addEventListener('click',()=>controller?.abort());
$('report-content').addEventListener('click',event=>{
  const button=event.target.closest('[data-review]');if(!button||!report)return;
  reviewing=report.tasks.find(t=>t.id===button.dataset.review);if(!reviewing)return;
  $('review-title').textContent=reviewing.title;$('review-action').value=reviewing.edited_action||reviewing.action;
  $('review-owner').value=reviewing.owner||reviewing.department;$('review-note').value=reviewing.review_note;
  $('review-checked').checked=reviewing.review_status==='reviewed';$('review-dialog').showModal();
});
$('close-dialog').addEventListener('click',()=>$('review-dialog').close());
$('review-form').addEventListener('submit',event=>{
  event.preventDefault();if(!reviewing)return;
  const edited=$('review-action').value.trim();
  if(!edited){$('review-action').setCustomValidity('Enter an action.');$('review-action').reportValidity();return;}
  reviewing.edited_action=edited===reviewing.action?'':edited;
  reviewing.owner=$('review-owner').value.trim();reviewing.review_note=$('review-note').value.trim();
  reviewing.review_status=$('review-checked').checked?'reviewed':'open';reviewing.reviewed_at=new Date().toISOString();
  $('review-dialog').close();render();
});
$('review-action').addEventListener('input',()=>$('review-action').setCustomValidity(''));
function download(content,extension,type){const blob=new Blob([content],{type});const a=document.createElement('a');const url=URL.createObjectURL(blob);a.href=url;a.download=`sceneready-${report.run_id}.${extension}`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
// Escape untrusted prose for Markdown export. JSON retains exact original content.
const md=value=>String(value??'').replace(/[\\`*_{}\[\]<>#!|]/g,'\\$&').replace(/^([ \t]*)([-+])/gm,'$1\\$2');
$('export-json').addEventListener('click',()=>{if(report)download(JSON.stringify(report,null,2),'json','application/json');});
$('export-md').addEventListener('click',()=>{
  if(!report)return;
  const lines=[`# ${md(report.brief.title)} — production review`,'',`Mode: ${report.mode} | Run: ${report.run_id} | ${report.created_at}`,'',report.notice,'',`City: ${md(report.brief.city)} | Location: ${md(report.brief.location||'Unknown')} | Date: ${report.brief.shoot_date||'Unknown'} | Crew: ${report.brief.crew_size}`,'','## Scene breakdown','',md(report.breakdown.summary),''];
  for(const scene of report.breakdown.scenes)lines.push(`### ${md(scene.id)} — ${md(scene.heading)}`,'',md(scene.script_excerpt||'No matching script excerpt.'),'',`Needs: ${md(scene.production_needs.join('; '))}`,'');
  lines.push('## Actions to review','');
  for(const t of report.tasks){lines.push(`### ${md(t.id)} — ${md(t.title)}`,'',`Priority: ${t.priority} | Owner: ${md(t.owner||t.department)} | Review: ${t.review_status}`,'',md(t.edited_action||t.action),'',md(t.rationale),'',`Verify: ${md(t.needs_verification)}`,'',`Evidence status: ${t.evidence_status}`,'');if(t.edited_action)lines.push(`Original generated action: ${md(t.action)}`,'','The reviewer edited this action; citations refer to the original task.','');for(const c of t.citations)lines.push(`Source ${md(c.source_id)}: ${md(c.url)}`,'',`Quote: ${md(c.quote)}`,'');if(t.review_note)lines.push(`Review note: ${md(t.review_note)}`,'');}
  lines.push('## Source register','');for(const s of report.sources)lines.push(`${md(s.id)}: ${md(s.title)}`,md(s.url),`Retrieved: ${s.retrieved_at}. Publication date and applicability not verified.`,'');
  lines.push('## Open questions','',...[...new Set([...report.breakdown.missing_details,...report.questions])].map(q=>`- ${md(q)}`),'','## Run notes','',...report.warnings.map(w=>`- ${md(w)}`),'','## Stage timings','',...report.trace.map(t=>`- ${t.stage}: ${t.seconds}s`));download(lines.join('\n'),'md','text/markdown');
});
async function initialize(){
  try{const response=await fetch('/api/config');if(!response.ok)throw new Error();const config=await response.json();$('connection').textContent=config.demo?'Offline rehearsal':config.configured?'Live research configured':'Setup needed';$('access-field').hidden=!config.access_required;
    if(config.demo){$('mode-banner').hidden=false;$('mode-banner').textContent='OFFLINE REHEARSAL — interface practice only. No Gemini or Parallel calls are made; output is illustrative and has no external evidence.';}
    else if(!config.configured){$('mode-banner').hidden=false;$('mode-banner').textContent='Live credentials are not loaded. Start the app with scripts/run_local.py before running a plan.';}
  }catch{$('connection').textContent='Server unavailable';$('status').textContent='The app server is unavailable. Check the terminal running SceneReady.';}
}
initialize();
