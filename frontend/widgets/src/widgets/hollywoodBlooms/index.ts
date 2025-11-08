(function(){
  function init(el: HTMLElement){
    const apiBase = el.dataset.apiBase || "https://orchid-api.onrender.com";
    const q = el.dataset.query || "";
    fetch(`${apiBase}/api/v1/widgets/hollywood-blooms?query=${encodeURIComponent(q)}`).then(r=>r.json()).then(d=>{
      const rows = (d.scenes||[]).map((s: any)=>`<li>${s.title}${s.taxon?` — <em>${s.taxon}</em>`:""}</li>`).join("");
      el.innerHTML = `<h3>Hollywood Blooms</h3><ul>${rows||"<li>No results yet.</li>"}</ul>`;
    }).catch(()=>el.textContent="Unable to load Hollywood Blooms.");
  }
  const boot=()=>{const el=document.getElementById("orchid-hollywood")||document.querySelector("[data-widget=orchid-hollywood]"); if(el) init(el as HTMLElement)};
  document.readyState==="loading"?document.addEventListener("DOMContentLoaded",boot):boot();
})();
