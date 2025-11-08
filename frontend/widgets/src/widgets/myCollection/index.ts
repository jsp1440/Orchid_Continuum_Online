(function(){
  function init(el: HTMLElement){
    const apiBase = el.dataset.apiBase || "https://orchid-api.onrender.com";
    const user = el.dataset.user || "demo";
    fetch(`${apiBase}/api/v1/widgets/my-collection?user_id=${encodeURIComponent(user)}`).then(r=>r.json()).then(d=>{
      el.innerHTML = `<h3>My Collection</h3><p>Owned: ${d.owned?.length||0}</p><p>Wishlist: ${d.wishlist?.length||0}</p>`;
    }).catch(()=>el.textContent="Unable to load collection.");
  }
  const boot=()=>{const el=document.getElementById("orchid-my-collection")||document.querySelector("[data-widget=orchid-my-collection]"); if(el) init(el as HTMLElement)};
  document.readyState==="loading"?document.addEventListener("DOMContentLoaded",boot):boot();
})();
