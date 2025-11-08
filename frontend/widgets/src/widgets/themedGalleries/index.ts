(function(){
  function init(el: HTMLElement){
    const apiBase = el.dataset.apiBase || "https://orchid-api.onrender.com";
    const theme = el.dataset.theme || "cloud-forest";
    fetch(`${apiBase}/api/v1/widgets/themed-galleries?theme=${encodeURIComponent(theme)}`).then(r=>r.json()).then(data=>{
      const items = (data.items||[]).map((i: any)=>`<figure><img src="${i.image}" alt="${i.taxon}" style="max-width:100%"><figcaption><em>${i.taxon||""}</em></figcaption></figure>`).join("");
      el.innerHTML = `<h3>Themed Gallery: ${theme}</h3><div>${items||"No images yet."}</div>`;
    }).catch(()=>el.textContent="Unable to load themed gallery.");
  }
  const boot=()=>{document.querySelectorAll("#orchid-themed-gallery,[data-widget=orchid-themed-gallery]").forEach(e=>init(e as HTMLElement))};
  document.readyState==="loading"?document.addEventListener("DOMContentLoaded",boot):boot();
})();
