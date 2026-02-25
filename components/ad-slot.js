(function(){
  const AD_CLIENT = 'ca-pub-7734599043419848';

  function mount(el){
    if(el.dataset.loaded === '1') return;
    const slot = el.dataset.slot || '';
    const format = el.dataset.format || 'auto';
    el.dataset.loaded = '1';
    el.innerHTML = `<ins class="adsbygoogle" style="display:block" data-ad-client="${AD_CLIENT}" data-ad-slot="${slot}" data-ad-format="${format}" data-full-width-responsive="true"></ins>`;
    try { (window.adsbygoogle = window.adsbygoogle || []).push({}); } catch(e) {}
  }

  function init(){
    const slots = [...document.querySelectorAll('.ad-slot')];
    if(!slots.length) return;

    if('IntersectionObserver' in window){
      const io = new IntersectionObserver((entries)=>{
        entries.forEach(entry=>{
          if(entry.isIntersecting){
            mount(entry.target);
            io.unobserve(entry.target);
          }
        });
      }, { rootMargin: '220px 0px' });
      slots.forEach(s=>io.observe(s));
    } else {
      slots.forEach(mount);
    }
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
