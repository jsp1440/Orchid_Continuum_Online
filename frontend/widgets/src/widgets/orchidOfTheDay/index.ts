(function(){
  function init(el: HTMLElement){
    const apiBase = el.dataset.apiBase || "https://orchid-api.onrender.com";
    const tenant = el.dataset.tenant || "fcos";
    fetch(`${apiBase}/api/v1/widgets/ootd?tenant=${encodeURIComponent(tenant)}`).then(r=>r.json()).then(d=>{
      el.innerHTML = `<figure><img src="${d.image}" alt="${d.taxon}" style="max-width:100%"><figcaption><em>${d.taxon}</em></figcaption></figure>`;
    }).catch(()=>el.textContent="Unable to load Orchid of the Day.");
  }
  const boot=()=>{document.querySelectorAll("#orchid-ootd,[data-widget=orchid-ootd]").forEach(e=>init(e as HTMLElement))};
  document.readyState==="loading"?document.addEventListener("DOMContentLoaded",boot):boot();
})();
