'use strict';
(()=> {
const $=s=>document.querySelector(s);
const names={fr:{heading:'Abonnements',intro:"Parcourez le catalogue, ajoutez ce qu'il vous faut à votre sélection, puis envoyez votre demande sur WhatsApp.",search:'Rechercher un abonnement...',all:'Tous',ai:'IA & Productivité',design:'Design & Création',vpn:'VPN & Sécurité',education:'Éducation',entertainment:'Divertissement',software:'Logiciels & Utilitaires',developer:'Outils développeur',only:'Disponibles uniquement',available:'Disponible',missing:'Rupture de stock',add:'＋ Ajouter à la sélection',selected:'✓ Sélectionné',price:'Prix sur demande',send:'Envoyer sur WhatsApp',request:'Demander la disponibilité',no:'Aucun produit ne correspond à votre recherche.',count:'abonnements',once:'Achat unique',you:'Votre sélection',remove:'Retirer',modal:'Ce produit est actuellement indisponible. Contactez-nous pour connaître les prix et les conditions de livraison.',flag:'FR Français'},en:{heading:'Subscriptions',intro:'Browse the catalog, add what you need to your selection, then send your request via WhatsApp.',search:'Search subscriptions...',all:'All',ai:'AI & Productivity',design:'Design & Creative',vpn:'VPN & Security',education:'Education',entertainment:'Entertainment',software:'Software & Utilities',developer:'Developer Tools',only:'Available only',available:'Available',missing:'Out of stock',add:'＋ Add to selection',selected:'✓ Selected',price:'Price on request',send:'Send on WhatsApp',request:'Request availability',no:'No matching products.',count:'subscriptions',once:'One-time',you:'Your selection',remove:'Remove',modal:'This product is out of stock. Contact us to confirm its price and fulfillment.',flag:'EN English'},ar:{heading:'الاشتراكات',intro:'تصفح الكتالوج، وأضف المنتجات المطلوبة إلى اختياراتك، ثم أرسل استفسارك عبر واتساب.',search:'ابحث عن اشتراك...',all:'الكل',ai:'الذكاء والإنتاجية',design:'التصميم والإبداع',vpn:'VPN والأمان',education:'التعليم',entertainment:'الترفيه',software:'البرامج والأدوات',developer:'أدوات المطورين',only:'المتوفر فقط',available:'متوفر',missing:'غير متوفر',add:'＋ أضف إلى الاختيار',selected:'✓ تمت الإضافة',price:'السعر عند الطلب',send:'أرسل عبر واتساب',request:'استفسر عن التوفر',no:'لا توجد منتجات مطابقة.',count:'منتجًا',once:'شراء لمرة واحدة',you:'اختياراتك',remove:'إزالة',modal:'هذا المنتج غير متوفر حاليًا. تواصل معنا للتأكد من السعر وشروط التسليم.',flag:'AR العربية'}};

const extraUI={
fr:{sortFeatured:'Recommandés',sortPriceLow:'Prix : croissant',sortPriceHigh:'Prix : décroissant',sortAz:'Nom A–Z',navSubs:'Abonnements',navHow:'Comment ça marche',navFaq:'FAQ',navContact:'Contact',howTitle:'Comment ça marche',howText:"Choisissez un kit original disponible, puis achetez-le via Gumroad ou contactez-nous sur WhatsApp. Aucun paiement n'est collecté directement sur ce site.",faqQ:'Les abonnements tiers sont-ils disponibles ?',faqA:"Non. Leur disponibilité, le prix et le mode de livraison doivent être vérifiés avant toute commande.",catalogNote:"Les abonnements tiers sont en rupture de stock jusqu'à confirmation du fournisseur et de la livraison. Nos kits d'origine sont vendus sur Gumroad.",buyDirect:'Acheter via Gumroad ↗',drawerInfo:"Envoyez votre sélection sur WhatsApp ; ce n'est pas un paiement.",drawerFoot:'Les kits originaux sont livrés via Gumroad.',footerExplorer:'Explorer',footerSupport:'Support',footerAvailability:'Demander disponibilité',footerSlogan:'Solutions numériques, IA et outils pour créateurs et développeurs.',footerCopyright:'© 2026 AscorShop — Askoure Digital. Les achats des kits originaux sont réalisés sur Gumroad.'},
en:{sortFeatured:'Recommended',sortPriceLow:'Price: low to high',sortPriceHigh:'Price: high to low',sortAz:'Name A–Z',navSubs:'Subscriptions',navHow:'How it works',navFaq:'FAQ',navContact:'Contact',howTitle:'How it works',howText:'Choose an available original kit, then purchase on Gumroad or contact us on WhatsApp. This website does not collect payments directly.',faqQ:'Are third-party subscriptions available?',faqA:'No. Supplier stock, final price and delivery must be verified before an order can be accepted.',catalogNote:'Third-party subscriptions remain out of stock until their supplier and delivery are verified. Our original kits are sold on Gumroad.',buyDirect:'Buy on Gumroad ↗',drawerInfo:'Send your selection through WhatsApp. This is an inquiry, not payment.',drawerFoot:'Original kits are delivered through Gumroad.',footerExplorer:'Explore',footerSupport:'Support',footerAvailability:'Request availability',footerSlogan:'Digital tools, AI and solutions for creators and developers.',footerCopyright:'© 2026 AscorShop — Askoure Digital. Original kit payments are handled by Gumroad.'},
ar:{sortFeatured:'موصى بها',sortPriceLow:'السعر: من الأقل',sortPriceHigh:'السعر: من الأعلى',sortAz:'الاسم أ–ي',navSubs:'الاشتراكات',navHow:'كيف يعمل',navFaq:'الأسئلة',navContact:'اتصل بنا',howTitle:'كيف يعمل',howText:'اختر حزمة أصلية متوفرة واشترها عبر Gumroad، أو تواصل معنا على واتساب. هذا الموقع لا يحصّل المدفوعات مباشرة.',faqQ:'هل الاشتراكات الخارجية متوفرة؟',faqA:'لا. يجب التحقق من مخزون المورد والسعر النهائي وطريقة التسليم قبل قبول الطلب.',catalogNote:'تبقى الاشتراكات الخارجية غير متوفرة حتى تأكيد المورد وطريقة التسليم. تباع حزمنا الأصلية عبر Gumroad.',buyDirect:'الشراء عبر Gumroad ↗',drawerInfo:'أرسل اختياراتك عبر واتساب. هذه رسالة استفسار وليست عملية دفع.',drawerFoot:'تُسلَّم الحزم الأصلية عبر Gumroad.',footerExplorer:'استكشف',footerSupport:'الدعم',footerAvailability:'استفسر عن التوفر',footerSlogan:'أدوات رقمية وحلول ذكاء اصطناعي للمبدعين والمطورين.',footerCopyright:'© 2026 AscorShop — Askoure Digital. تُعالج مدفوعات الحزم الأصلية عبر Gumroad.'}
};
for(const l of Object.keys(extraUI))Object.assign(names[l],extraUI[l]);
const originalDescriptions={
'n8n-workflow-preflight-auditor':{
 en:{meta:'Developer Tools · One-time purchase',desc:'Check exported n8n workflows before handing them over to clients.',perks:['Inspect workflow JSON','Offline pre-delivery checks','Downloadable toolkit']},
 ar:{meta:'أدوات المطورين · شراء لمرة واحدة',desc:'افحص ملفات عمل n8n المصدّرة قبل تسليمها إلى العملاء.',perks:['فحص ملفات JSON لسير العمل','تدقيق محلي قبل التسليم','حزمة رقمية قابلة للتنزيل']}},
'llm-reliability-rescue-kit':{
 en:{meta:'Developer Tools · One-time purchase',desc:'Make structured AI outputs more reliable using Python, FastAPI and regression tests.',perks:['Pydantic JSON validation','FastAPI regression tests','LLM reliability tools']},
 ar:{meta:'أدوات المطورين · شراء لمرة واحدة',desc:'ارفع موثوقية مخرجات الذكاء الاصطناعي باستخدام Python وFastAPI والاختبارات.',perks:['التحقق من JSON عبر Pydantic','اختبارات FastAPI','أدوات موثوقية النماذج']}},
'agent-runaway-guard-kit':{
 en:{meta:'AI & Productivity · One-time purchase',desc:'Prevent repeated tool calls, retry storms and runaway agent budgets.',perks:['Tool-call repetition limits','Retry controls','Agent budget safeguards']},
 ar:{meta:'الذكاء والإنتاجية · شراء لمرة واحدة',desc:'امنع تكرار استدعاءات الأدوات والعواصف المتكررة وتجاوز ميزانية الوكلاء.',perks:['حدود تكرار استدعاء الأدوات','التحكم في إعادة المحاولة','حماية ميزانية الوكلاء']}}
};
const externalDescriptions={
en:{
'ChatGPT':['AI assistance for writing, research and productivity.',['Writing and analysis','Research assistance','Plans to be confirmed']],
'Canva':['A design platform for visuals, creative work and professional templates.',['Graphic design tools','Content templates','Plans to be confirmed']],
'Claude':['AI assistant for analysis, writing and summaries.',['Document analysis','Writing and summaries','Plans to be confirmed']],
'Midjourney':['AI-powered images and creative visual concepts.',['Image creation','Creative concepts','Plans to be confirmed']],
'Runway':['AI video creation and editing tools.',['Video generation','Creative editing','Offers to be confirmed']],
'ElevenLabs':['AI voice generation and audio creation tools.',['Text-to-speech','Audio creation','Offers to be confirmed']],
'Cursor':['AI-assisted software development environment.',['AI coding editor','Developer assistance','Offers to be confirmed']],
'Notion AI':['Organize documents and knowledge with AI assistance.',['Docs and notes','Task management','Offers to be confirmed']],
'Perplexity':['AI-assisted research and cited answers.',['Assisted research','Cited answers','Offers to be confirmed']],
'CapCut':['Video editing and creative templates for content creators.',['Video editing','Creative templates','Offers to be confirmed']],
'n8n':['Visual workflow automation and service integrations.',['Connected workflows','Automation','Offers to be confirmed']],
'AI Prompt & Template Packs':['Digital templates and prompts for repeatable workflows.',['Digital prompts','Workflow templates','Offers to be confirmed']]
},
ar:{
'ChatGPT':['مساعد ذكي للكتابة والبحث وزيادة الإنتاجية.',['الكتابة والتحليل','البحث والمساعدة','الخطط تحتاج تأكيدًا']],
'Canva':['منصة للتصميم وصناعة المحتوى والقوالب الاحترافية.',['أدوات التصميم','قوالب المحتوى','الخطط تحتاج تأكيدًا']],
'Claude':['مساعد ذكاء اصطناعي للتحليل والكتابة والتلخيص.',['تحليل المستندات','الكتابة والتلخيص','الخطط تحتاج تأكيدًا']],
'Midjourney':['إنشاء الصور والمفاهيم الإبداعية بالذكاء الاصطناعي.',['توليد الصور','الأفكار الفنية','الخطط تحتاج تأكيدًا']],
'Runway':['أدوات إنشاء الفيديو وتحريره بالذكاء الاصطناعي.',['توليد الفيديو','التحرير الإبداعي','العروض تحتاج تأكيدًا']],
'ElevenLabs':['أدوات توليد الصوت والمحتوى السمعي بالذكاء الاصطناعي.',['تحويل النص إلى صوت','إنشاء المحتوى الصوتي','العروض تحتاج تأكيدًا']],
'Cursor':['بيئة تطوير برمجيات مدعومة بالذكاء الاصطناعي.',['محرر برمجي ذكي','مساعدة المطورين','العروض تحتاج تأكيدًا']],
'Notion AI':['تنظيم الوثائق والمعرفة بالذكاء الاصطناعي.',['الوثائق والملاحظات','إدارة المهام','العروض تحتاج تأكيدًا']],
'Perplexity':['بحث ذكي وإجابات مدعومة بالمصادر.',['البحث المساعد','إجابات بالمصادر','العروض تحتاج تأكيدًا']],
'CapCut':['تحرير الفيديو والقوالب الإبداعية لصنّاع المحتوى.',['مونتاج الفيديو','قوالب إبداعية','العروض تحتاج تأكيدًا']],
'n8n':['أتمتة سير العمل وربط الخدمات.',['سير عمل مترابط','الأتمتة','العروض تحتاج تأكيدًا']],
'AI Prompt & Template Packs':['حزم أوامر وقوالب رقمية للمهام المتكررة.',['أوامر رقمية','قوالب سير العمل','العروض تحتاج تأكيدًا']]
}
};

function localizeOriginals(){
 for(const card of original){
  const copy=lang==='fr'?originalFrench.get(card.dataset.owned):originalDescriptions[card.dataset.owned]?.[lang];
  if(!copy)continue;
  card.querySelector('.meta').textContent=copy.meta;
  card.querySelector('.description').textContent=copy.desc;
  card.querySelectorAll('.perks li').forEach((el,i)=>{if(copy.perks[i])el.textContent=copy.perks[i]});
  card.querySelector('.price span').textContent='/ '+names[lang].once;
  card.querySelector('.direct').textContent=names[lang].buyDirect;
 }
}

const groups=[['all','▦'],['ai','✦'],['design','◉'],['vpn','⬡'],['education','⌑'],['entertainment','▣'],['software','⚒'],['developer','⌘']];
const original=[...document.querySelectorAll('.own-card')];
const originalFrench=new Map(original.map(card=>[card.dataset.owned,{
 meta:card.querySelector('.meta')?.textContent||'',
 desc:card.querySelector('.description')?.textContent||'',
 perks:[...card.querySelectorAll('.perks li')].map(e=>e.textContent)
}]));
const selected=new Set();
const grid=$('#cards');
let category='all',term='',sort='featured',availableOnly=false,lang='fr';
const escapeHTML=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function thirdPartyCard(p){
  const c=document.createElement('article');c.className='card';c.dataset.group=p.group;c.dataset.title=p.name;c.dataset.price='';c.dataset.available='false';
  const copy=externalDescriptions[lang]?.[p.name];const description=copy?.[0]||p.description;const perks=copy?.[1]||p.perks;
  const pic=p.logo?'<img src="'+escapeHTML(p.logo)+'" alt="'+escapeHTML(p.name)+'" loading="lazy" decoding="async" onerror="this.hidden=true;this.nextElementSibling.hidden=false"><b hidden>'+escapeHTML(p.mark)+'</b>':'<b>'+escapeHTML(p.mark)+'</b>';
  c.innerHTML='<span class="label">'+escapeHTML(names[lang].missing)+'</span><div class="logo-box">'+pic+'</div><h2>'+escapeHTML(p.name)+'</h2><p class="meta">'+escapeHTML(names[lang][p.group]||p.group)+'</p><p class="description">'+escapeHTML(description)+'</p><ul class="perks">'+perks.map(x=>'<li>'+escapeHTML(x)+'</li>').join('')+'</ul><div class="card-bottom"><div class="price"><b class="no-price">—</b><span>'+escapeHTML(names[lang].price)+'</span></div><div class="status out">'+escapeHTML(names[lang].missing)+'</div><div class="buttons"><button class="add-btn" disabled>'+escapeHTML(names[lang].missing)+'</button><button class="arrow" type="button" aria-label="'+escapeHTML(names[lang].request)+'" data-ask="'+escapeHTML(p.name)+'">➜</button></div></div>';
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
if(!selected.size)box.hidden=true;
}
function availability(name){
$('#modalTitle').textContent=name;$('#modalText').textContent=names[lang].modal;$('#modalLink').textContent=names[lang].request+' ↗';
$('#modalLink').href='https://wa.me/212649117788?text='+encodeURIComponent('Bonjour AscorShop, pouvez-vous confirmer la disponibilité, le prix et la livraison de '+name+' ?');
$('#modal').hidden=false;$('#modalClose').focus();
}
function setLanguage(l){
lang=l;document.documentElement.lang=l;document.body.dir=l==='ar'?'rtl':'ltr';$('#langText').textContent=names[l].flag;
$('#langBtn').setAttribute('aria-label',l==='ar'?'تغيير اللغة':l==='en'?'Change language':'Changer la langue');
document.querySelectorAll('[data-i18n]').forEach(el=>{const key=el.dataset.i18n;if(names[l][key])el.textContent=names[l][key]});
$('#searchInput').placeholder=names[l].search;$('#searchInput').setAttribute('aria-label',names[l].search);
const labels=['sortFeatured','sortPriceLow','sortPriceHigh','sortAz'];[...$('#sortSelect').options].forEach((o,i)=>o.textContent=names[l][labels[i]]);
localizeOriginals();render();if(selected.size)draw();
try{localStorage.setItem('ascorshop-lang',l)}catch(e){/* storage optional */}

}
grid.addEventListener('click',e=>{const b=e.target.closest('[data-add]');if(b){const id=b.dataset.add;if(selected.has(id))selected.delete(id);else selected.add(id);draw();render();return}const ask=e.target.closest('[data-ask]');if(ask)availability(ask.dataset.ask)});
$('#searchInput').addEventListener('input',e=>{term=e.target.value.trim();render()});
$('#sortSelect').addEventListener('change',e=>{sort=e.target.value;render()});
$('#langBtn').addEventListener('click',()=>setLanguage(lang==='fr'?'ar':lang==='ar'?'en':'fr'));
$('#themeBtn').addEventListener('click',()=>{const enabled=document.body.classList.toggle('light-mode');$('#themeBtn').setAttribute('aria-pressed',String(enabled));$('#themeBtn').textContent=enabled?'☀':'☾';document.querySelector('meta[name="theme-color"]')?.setAttribute('content',enabled?'#f7f9fc':'#090e1b')});
$('#bagBtn').addEventListener('click',()=>{$('#drawer').hidden=!$('#drawer').hidden;if(!selected.size)$('#drawer').hidden=true});
$('#drawerClose').addEventListener('click',()=>$('#drawer').hidden=true);
$('#menuBtn').addEventListener('click',()=>{const menu=$('#menu');menu.hidden=!menu.hidden;$('#menuBtn').setAttribute('aria-expanded',String(!menu.hidden))});
$('#menu').querySelectorAll('a').forEach(a=>a.onclick=()=>{$('#menu').hidden=true;$('#menuBtn').setAttribute('aria-expanded','false')});
$('#modalClose').addEventListener('click',()=>$('#modal').hidden=true);
$('#modal').addEventListener('click',e=>{if(e.target.id==='modal')$('#modal').hidden=true});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){$('#menu').hidden=true;$('#drawer').hidden=true;$('#modal').hidden=true}});
let preferred='fr';try{preferred=localStorage.getItem('ascorshop-lang')||'fr'}catch(e){/* storage optional */}setLanguage(names[preferred]?preferred:'fr');
})();
