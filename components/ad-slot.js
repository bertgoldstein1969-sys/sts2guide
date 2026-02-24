(function(){
  function render(el){
    const slot = el.dataset.slot || '';
    const format = el.dataset.format || 'auto';
    el.innerHTML = `
      <ins class="adsbygoogle"
           style="display:block"
           data-ad-client="ca-pub-7734599043419848"
           data-ad-slot="${slot}"
           data-ad-format="${format}"
           data-full-width-responsive="true"></ins>`;
    try{ (adsbygoogle = window.adsbygoogle || []).push({}); }catch(e){}
  }
  document.addEventListener('DOMContentLoaded',()=>{
    document.querySelectorAll('.ad-slot').forEach(render);
  });
})();
