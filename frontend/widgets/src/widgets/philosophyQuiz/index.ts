(function(){
  function init(el: HTMLElement){
    const apiBase = el.dataset.apiBase || "https://orchid-api.onrender.com";
    fetch(`${apiBase}/api/v1/widgets/philosophy-quiz`).then(r=>r.json()).then(d=>{
      const q = (d.questions&&d.questions[0]) || {text:"(no questions yet)"};
      el.innerHTML = `<h3>Orchid Philosophy Quiz</h3><p>${q.text}</p><button type="button" aria-label="Next">Next</button>`;
    }).catch(()=>el.textContent="Unable to load quiz.");
  }
  const boot=()=>{const el=document.getElementById("orchid-philosophy-quiz")||document.querySelector("[data-widget=orchid-philosophy-quiz]"); if(el) init(el as HTMLElement)};
  document.readyState==="loading"?document.addEventListener("DOMContentLoaded",boot):boot();
})();
