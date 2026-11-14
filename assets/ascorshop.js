'use strict';
(()=> {
const $=s=>document.querySelector(s);
const names={fr:{heading:'Abonnements',intro:"Parcourez le catalogue, ajoutez ce qu'il vous faut à votre sélection, puis envoyez votre demande sur WhatsApp.",search:'Rechercher un abonnement...',all:'Tous',ai:'IA & Productivité',design:'Design & Création',vpn:'VPN & Sécurité',education:'Éducation',entertainment:'Divertissement',software:'Logiciels & Utilitaires',developer:'Outils développeur',only:'Disponibles uniquement',available:'Disponible',missing:'Rupture de stock',add:'＋ Ajouter à la sélection',selected:'✓ Sélectionné',price:'Prix sur demande',send:'Envoyer sur WhatsApp',request:'Demander la disponibilité',no:'Aucun produit ne correspond à votre recherche.',count:'abonnements',once:'Achat unique',you:'Votre sélection',remove:'Retirer',modal:'Ce produit est actuellement indisponible. Contactez-nous pour connaître les prix et les conditions de livraison.',flag:'FR Français'},en:{heading:'Subscriptions',intro:'Browse the catalog, add what you need to your selection, then send your request via WhatsApp.',search:'Search subscriptions...',all:'All',ai:'AI & Productivity',design:'Design & Creative',vpn:'VPN & Security',education:'Education',entertainment:'Entertainment',software:'Software & Utilities',developer:'Developer Tools',only:'Available only',available:'Available',missing:'Out of stock',add:'＋ Add to selection',selected:'✓ Selected',price:'Price on request',send:'Send on WhatsApp',request:'Request availability',no:'No matching products.',count:'subscriptions',once:'One-time',you:'Your selection',remove:'Remove',modal:'This product is out of stock. Contact us to confirm its price and fulfillment.',flag:'EN English'},ar:{heading:'الاشتراكات',intro:'تصفح الكتالوج، وأضف المنتجات المطلوبة إلى اختياراتك، ثم أرسل استفسارك عبر واتساب.',search:'ابحث عن اشتراك...',all:'الكل',ai:'الذكاء والإنتاجية',design:'التصميم والإبداع',vpn:'VPN والأمان',education:'التعليم',entertainment:'الترفيه',software:'البرامج والأدوات',developer:'أدوات المطورين',only:'المتوفر فقط',available:'متوفر',missing:'غير متوفر',add:'＋ أضف إلى الاختيار',selected:'✓ تمت الإضافة',price:'السعر عند الطلب',send:'أرسل عبر واتساب',request:'استفسر عن التوفر',no:'لا توجد منتجات مطابقة.',count:'منتجًا',once:'شراء لمرة واحدة',you:'اختياراتك',remove:'إزالة',modal:'هذا المنتج غير متوفر حاليًا. تواصل معنا للتأكد من السعر وشروط التسليم.',flag:'AR العربية'}};
const groups=[['all','▦'],['ai','✦'],['design','◉'],['vpn','⬡'],['education','⌑'],['entertainment','▣'],['software','⚒'],['developer','⌘']];
const original=[...document.querySelectorAll('.own-card')];
const selected=new Set();
const grid=$('#cards');
let category='all',term='',sort='featured',availableOnly=false,lang='fr';
const escapeHTML=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function thirdPartyCard(p){
  const c=document.createElement('article');c.className='card';c.dataset.group=p.group;c.dataset.title=p.name;c.dataset.price='';c.dataset.available='false';
  const pic=p.logo?'<img src="'+escapeHTML(p.logo)+'" alt="'+escapeHTML(p.name)+'" loading="lazy" decoding="async" onerror="this.hidden=true;this.nextElementSibling.hidden=false"><b hidden>'+escapeHTML(p.mark)+'</b>':'<b>'+escapeHTML(p.mark)+'</b>';
  c.innerHTML='<span class="label">'+escapeHTML(names[lang].missing)+'</span><div class="logo-box">'+pic+'</div><h2>'+escapeHTML(p.name)+'</h2><p class="meta">'+escapeHTML(names[lang][p.group]||p.group)+'</p><p class="description">'+escapeHTML(p.description)+'</p><ul class="perks">'+p.perks.map(x=>'<li>'+escapeHTML(x)+'</li>').join('')+'</ul><div class="card-bottom"><div class="price"><b class="no-price">—</b><span>'+escapeHTML(names[lang].price)+'</span></div><div class="status out">'+escapeHTML(names[lang].missing)+'</div><div class="buttons"><button class="add-btn" disabled>'+escapeHTML(names[lang].missing)+'</button><button class="arrow" type="button" aria-label="'+escapeHTML(names[lang].request)+'" data-ask="'+escapeHTML(p.name)+'">➜</button></div></div>';
  return c;
}
function renderFilters(){
const f=$('#filters');f.replaceChildren();
groups.forEach(([id,icon])=>{const b=document.createElement('button');b.type='button';b.className='filter'+(category===id?' active':'');b.setAttribute('aria-pressed',String(category===id));const i=document.createElement('i');i.textContent=icon;b.append(i,document.createTextNode(names[lang][id]));b.onclick=()=>{category=id;render()};f.append(b)});
const label=document.createElement('label');label.className='only-available';const box=document.createElement('input');box.type='checkbox';box.checked=availableOnly;box.onchange=()=>{availableOnly=box.checked;render()};label.append(box,document.createTextNode(names[lang].only));f.append(label);
}
function render(){
 renderFilters();
 const all=[...original.map((card,index)=>({kind:'original',node:card,index,title:card.dataset.title,price:Number(card.dataset.price),group:card.dataset.group,description:card.textContent})),...products.map((p,index)=>({kind:'external',p,index:original.length+index,title:p.name,price:Infinity,group:p.group,description:p.description+' '+p.perks.join(' ')}))];
 const found=all.filter(e=>(category==='all'||e.group===category)&&(!availableOnly||e.kind==='original')&&(e.title+' '+e.description).toLocaleLowerCase().includes(term.toLocaleLowerCase()));
 if(sort==='asc')found.sort((a,b)=>a.price-b.price||a.index-b.index);
 if(sort==='desc')found.sort((a,b)=>(Number.isFinite(b.price)?b.price:-Infinity)-(Number.isFinite(a.price)?a.price:-Infinity)||a.index-b.index);
 if(sort==='az')found.sort((a,b)=>a.title.localeCompare(b.title));
 grid.replaceChildren();
 found.forEach(e=>grid.append(e.kind==='original'?e.node:thirdPartyCard(e.p)));
 if(!found.length){let p=document.createElement('div');p.className='empty';p.textContent=names[lang].no;grid.append(p)}
 $('#counter').textContent=found.length+' '+names[lang].count;
 original.forEach(card=>{const btn=card.querySelector('[data-add]');const on=selected.has(card.dataset.owned);btn.textContent=on?names[lang].selected:names[lang].add;btn.setAttribute('aria-pressed',String(on));card.querySelector('.status').textContent=names[lang].available});
}
function draw(){
const box=$('#drawer'),list=$('#drawerRows');
$('#basketCount').textContent=selected.size;$('#drawerTitle').textContent=names[lang].you+' ('+selected.size+')';
list.replaceChildren();
const lines=[];
for(const key of selected){const card=original.find(x=>x.dataset.owned===key);if(!card)continue;const row=document.createElement('div');row.className='drawer-row';const span=document.createElement('span');span.textContent=card.dataset.title+' · $'+card.dataset.price;const btn=document.createElement('button');btn.textContent=names[lang].remove;btn.type='button';btn.onclick=()=>{selected.delete(key);draw();render()};row.append(span,btn);list.append(row);lines.push(card.dataset.title+' ($'+card.dataset.price+') — '+card.dataset.buy)}
$('#drawerSend').href='https://wa.me/212649117788?text='+encodeURIComponent('Bonjour AscorShop, je souhaite acheter ou demander conseil sur ces kits originaux :\n'+lines.join('\n')+'\nCette demande n’est pas un paiement.');
$('#drawerSend').textContent=names[lang].send+' ➜';
box.hidden=selected.size===0;
}
function availability(name){
$('#modalTitle').textContent=name;$('#modalText').textContent=names[lang].modal;$('#modalLink').textContent=names[lang].request+' ↗';
$('#modalLink').href='https://wa.me/212649117788?text='+encodeURIComponent('Bonjour AscorShop, pouvez-vous confirmer la disponibilité, le prix et la livraison de '+name+' ?');
$('#modal').hidden=false;$('#modalClose').focus();
}
function setLanguage(l){
lang=l;document.documentElement.lang=l;document.body.dir=l==='ar'?'rtl':'ltr';$('#langText').textContent=names[l].flag;
document.querySelectorAll('[data-i18n]').forEach(el=>{const key=el.dataset.i18n;if(names[l][key])el.textContent=names[l][key]});
$('#searchInput').placeholder=names[l].search;
render();if(selected.size)draw();
}
grid.addEventListener('click',e=>{const b=e.target.closest('[data-add]');if(b){const id=b.dataset.add;if(selected.has(id))selected.delete(id);else selected.add(id);draw();render();return}const ask=e.target.closest('[data-ask]');if(ask)availability(ask.dataset.ask)});
$('#searchInput').addEventListener('input',e=>{term=e.target.value.trim();render()});
$('#sortSelect').addEventListener('change',e=>{sort=e.target.value;render()});
$('#langBtn').addEventListener('click',()=>setLanguage(lang==='fr'?'ar':lang==='ar'?'en':'fr'));
$('#themeBtn').addEventListener('click',()=>document.body.classList.toggle('light-mode'));
$('#bagBtn').addEventListener('click',()=>{$('#drawer').hidden=!$('#drawer').hidden;if(!selected.size)$('#drawer').hidden=true});
$('#drawerClose').addEventListener('click',()=>$('#drawer').hidden=true);
$('#menuBtn').addEventListener('click',()=>{$('#menu').hidden=!$('#menu').hidden});
$('#menu').querySelectorAll('a').forEach(a=>a.onclick=()=>$('#menu').hidden=true);
$('#modalClose').addEventListener('click',()=>$('#modal').hidden=true);
$('#modal').addEventListener('click',e=>{if(e.target.id==='modal')$('#modal').hidden=true});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){$('#menu').hidden=true;$('#drawer').hidden=true;$('#modal').hidden=true}});
render();
})();
