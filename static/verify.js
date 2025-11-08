async function fetchNext() {
  const memberId = localStorage.getItem('member_id') || '';
  const r = await fetch('/verify/api/next?exclude_voted=true', {
    headers: memberId ? {'X-Member-ID': memberId} : {}
  });
  const data = await r.json();
  const box = document.getElementById('content');
  const pill = document.getElementById('status-pill');

  if (!data.item) { box.innerHTML = '<p>No items available. Try again later.</p>'; pill.textContent=''; return; }

  const it = data.item;
  pill.textContent = it.ai_guess.status || 'pending';

  const links = [];
  if (it.links.powo) links.push(`<a href="${it.links.powo}" target="_blank" rel="noopener">POWO</a>`);
  if (it.links.gbif) links.push(`<a href="${it.links.gbif}" target="_blank" rel="noopener">GBIF</a>`);
  if (it.links.eol)  links.push(`<a href="${it.links.eol}"  target="_blank" rel="noopener">EOL</a>`);

  box.innerHTML = `
    <div style="margin-bottom:8px">
      <label style="font-size:12px;color:#444">Member ID (temp):
        <input id="member_id_input" style="width:100px" placeholder="e.g. 1">
        <button onclick="saveMemberId()">Set</button>
        <span style="font-size:12px;color:#666">(experts have higher weight)</span>
      </label>
    </div>
    <div class="row">
      <div style="flex:1;min-width:300px">
        <img src="${it.image_path}" alt="Orchid ${it.orchid_id}">
      </div>
      <div style="flex:1;min-width:260px">
        <div class="meta"><strong>AI Guess:</strong> ${it.ai_guess.genus || '(?)'} ${it.ai_guess.species || ''} ${it.ai_guess.confidence!=null?` · ${(it.ai_guess.confidence*100).toFixed(0)}%`:''}</div>
        <div class="meta" style="margin:8px 0">${links.join(' ') || '(no links)'}</div>
        <div class="actions">
          <button onclick="vote('${it.result_id}','agree')">Agree ✅</button>
          <button onclick="vote('${it.result_id}','disagree')">Disagree ❌</button>
          <button onclick="toggleCorrect()">Suggest correction ✍️</button>
          <button onclick="fetchNext()">Skip ➡️</button>
        </div>
        <div id="correctBox" class="hidden">
          <div class="field"><label>Correct Genus: <input id="corr_genus" placeholder="Genus"></label></div>
          <div class="field"><label>Correct Species: <input id="corr_species" placeholder="species"></label></div>
          <div class="field"><label>Notes: <input id="corr_notes" placeholder="(optional)"></label></div>
          <button onclick="submitCorrection('${it.result_id}')">Submit correction</button>
        </div>
        <div id="msg" class="meta" style="margin-top:10px;"></div>
      </div>
    </div>
  `;
}
function toggleCorrect(){ document.getElementById('correctBox').classList.toggle('hidden'); }
function saveMemberId(){
  const v = document.getElementById('member_id_input').value.trim();
  if(!v){ alert('Enter a numeric member id (e.g., 1)'); return; }
  localStorage.setItem('member_id', v); alert('Member ID set to '+v);
}
async function vote(result_id, decision){
  const body = { result_id, decision };
  const memberId = localStorage.getItem('member_id') || '';
  const r = await fetch('/verify/api/vote', {
    method:'POST',
    headers: Object.assign({'Content-Type':'application/json'}, memberId? {'X-Member-ID':memberId} : {}),
    body: JSON.stringify(body)
  });
  const data = await r.json(); const msg = document.getElementById('msg');
  if(!data.ok){ msg.textContent='Error: '+(data.error||'unable to vote'); return; }
  msg.textContent = `Recorded. Status: ${data.result_status}. Weighted — agree: ${data.weighted.agree?.toFixed(1)||0}, corrected: ${data.weighted.corrected?.toFixed(1)||0}`;
  setTimeout(fetchNext, 600);
}
async function submitCorrection(result_id){
  const genus=document.getElementById('corr_genus').value.trim();
  const species=document.getElementById('corr_species').value.trim();
  const notes=document.getElementById('corr_notes').value.trim();
  if(!genus){ alert('Please enter a genus for correction.'); return; }
  const body={result_id, decision:'corrected', suggested_genus:genus||null, suggested_species:species||null, notes:notes||null};
  const memberId = localStorage.getItem('member_id') || '';
  const r = await fetch('/verify/api/vote',{method:'POST', headers:Object.assign({'Content-Type':'application/json'}, memberId? {'X-Member-ID':memberId} : {}), body:JSON.stringify(body)});
  const data=await r.json(); const msg=document.getElementById('msg');
  if(!data.ok){ msg.textContent='Error: '+(data.error||'unable to submit correction'); return; }
  msg.textContent=`Correction saved. Status: ${data.result_status}.`; setTimeout(fetchNext, 600);
}
window.addEventListener('load', fetchNext);
