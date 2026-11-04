'use strict';
/* VerveLiving VIVID: progressive visual effects. Never handles money or PayPal. */
(() => {
  const motionAllowed = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const hero = document.querySelector('.hero[data-scene]');
  if (hero) {
    const buttons = [...hero.querySelectorAll('[data-scene-to]')];
    const label = hero.querySelector('[data-scene-label]');
    const messages = [
      'A HOME WITH PETS',
      'ON THE ROAD',
      'A FRESH START'
    ];
    let timer = null;
    const setScene = index => {
      const n = ((index % 3) + 3) % 3;
      hero.dataset.scene = String(n);
      buttons.forEach(b => b.setAttribute('aria-pressed',String(Number(b.dataset.sceneTo)===n)));
      if (label) label.textContent=messages[n];
    };
    buttons.forEach(button => button.addEventListener('click',() => {
      setScene(Number(button.dataset.sceneTo));
      if (timer) window.clearInterval(timer);
      timer=null;
    }));
    if (motionAllowed) {
      timer=window.setInterval(() => {
        if (!document.hidden) setScene(Number(hero.dataset.scene||0)+1);
      },6500);
      const art=hero.querySelector('.hero-image');
      if (art && window.matchMedia('(pointer: fine)').matches) {
        hero.addEventListener('pointermove',e => {
          const r=hero.getBoundingClientRect(), x=(e.clientX-r.left)/r.width-.5, y=(e.clientY-r.top)/r.height-.5;
          art.style.setProperty('--float-x',Math.round(x*18)+'px');
          art.style.setProperty('--float-y',Math.round(y*15)+'px');
        },{passive:true});
        hero.addEventListener('pointerleave',() => {
          art.style.setProperty('--float-x','0px');
          art.style.setProperty('--float-y','0px');
        });
      }
    }
  }
  if (motionAllowed && 'IntersectionObserver' in window) {
    const nodes=[...document.querySelectorAll('.benefits>div,.story-visual,.story-copy,.feature-heading,.feature-media,.buybox,.manifesto h2,.faq>div,.end-cta,.collection-card')];
    const observer=new IntersectionObserver(entries => {
      for (const entry of entries) if(entry.isIntersecting){
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    },{threshold:.1,rootMargin:'0px 0px 28px 0px'});
    nodes.forEach((node,i) => {
      node.classList.add('reveal-up');
      node.style.transitionDelay=(i%3)*90+'ms';
      observer.observe(node);
    });
  }
  const target=document.querySelector('#home-car-glove-duo');
  if (target) {
    const link=document.createElement('a');
    link.className='floating-shop';
    link.href='/products/home-car-glove-duo/#home-car-glove-duo';
    link.textContent='SHOP THE GLOVE DUO · $10.99 →';
    document.body.append(link);
    let inView=false;
    const update=() => {
      const far=window.scrollY>420;
      link.classList.toggle('show',far && !inView);
    };
    if ('IntersectionObserver' in window) {
      const obs=new IntersectionObserver(entries=>{
        inView=entries[0]?.isIntersecting||false;
        update();
      },{threshold:.08});
      obs.observe(target);
    }
    window.addEventListener('scroll',update,{passive:true});
    update();
  }
})();
