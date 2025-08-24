(function(){
  const nav = document.querySelector('.nav');
  const btn = document.getElementById('hamburger');
  const menu = document.getElementById('main-menu');
  if(!nav || !btn || !menu) return;

  function closeMenu(){
    nav.classList.remove('open');
    btn.setAttribute('aria-expanded','false');
  }
  function openMenu(){
    nav.classList.add('open');
    btn.setAttribute('aria-expanded','true');
  }
  btn.addEventListener('click', function(e){
    e.stopPropagation();
    if(nav.classList.contains('open')) closeMenu(); else openMenu();
  });
  // Close when clicking a menu link (mobile)
  menu.addEventListener('click', function(e){
    const t = e.target.closest('a,button');
    if(t) closeMenu();
  });
  // Close when clicking outside
  document.addEventListener('click', function(e){
    if(!nav.classList.contains('open')) return;
    if(!nav.contains(e.target)) closeMenu();
  });
  // Close on ESC
  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape') closeMenu();
  });
})();
