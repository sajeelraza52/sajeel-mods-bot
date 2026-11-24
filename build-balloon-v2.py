#!/usr/bin/env python3
"""Balloon Shop v2 for Aliyan (WhatsApp 03470098911) — demo + Firebase Admin Panel.
- Branding: Balloon Bliss -> Aliyan Balloons; WhatsApp 923061601587 -> 923470098911 (orders).
- Products render from JS (DEFAULT_PRODUCTS = the 14 demo products) + live RTDB `products`
  when Firebase is configured; admin can add/edit/delete with photo upload to Storage.
- Admin panel (#admin): Firebase Auth login, add-product form, import-demo button, rules note.
- Firebase config is a placeholder — Sajeel creates the project (SETUP.txt steps) and pastes it.
Run: python3 build-balloon-v2.py  (reads ../balloon-shop-demo/index.html, writes ../balloon-shop-v2/)
"""
import os, shutil, re

SRC_DIR = os.path.expanduser('~/workspace/balloon-shop-demo')
DST_DIR = os.path.expanduser('~/workspace/balloon-shop-v2')

with open(os.path.join(SRC_DIR, 'index.html'), encoding='utf-8') as f:
    html = f.read()

orig_len = len(html)
edits = []

def rep(old, new, label, count=1):
    global html
    n = html.count(old)
    assert n == count, f'{label}: expected {count}, found {n}'
    html = html.replace(old, new)
    edits.append(label)

# ---------- 1. Branding ----------
rep('<title>Balloon Bliss — Party Balloons &amp; Birthday Decor</title>',
    '<title>Aliyan Balloons — Party Balloons &amp; Birthday Decor</title>', 'title')
rep('<a class="logo" href="#top">🎈 <b>Balloon</b> <span>Bliss</span><span class="sample-pill">SAMPLE</span></a>',
    '<a class="logo" href="#top">🎈 <b>Aliyan</b> <span>Balloons</span></a>', 'logo')
rep('<b>🎈 Balloon Bliss</b>', '<b>🎈 Aliyan Balloons</b>', 'footer name')
rep('Demo website by SAJEEL MODS — Shop website Rs 1,000, 1 din mein tayyar • WhatsApp 0306 1601587',
    'Website by SAJEEL MODS — Shop website Rs 1,000, 1 din mein tayyar • WhatsApp 0306 1601587', 'footer credit')

# ---------- 2. Hero title letters: ALIYAN BALLOONS ----------
h1_start = html.index('<h1 id="heroTitle">')
h1_end = html.index('</h1>', h1_start) + len('</h1>')
letters = []
delay = 0.05
for ch in 'ALIYAN':
    letters.append(f'<span class="l" style="animation-delay:{delay:.2f}s">{ch}</span>')
    delay += 0.05
letters.append(f'<span class="l" style="animation-delay:{delay:.2f}s">&nbsp;</span>')
delay += 0.05
for ch in 'BALLOONS':
    letters.append(f'<span class="l" style="animation-delay:{delay:.2f}s"><em>{ch}</em></span>')
    delay += 0.05
html = html[:h1_start] + '<h1 id="heroTitle">' + ''.join(letters) + '</h1>' + html[h1_end:]
edits.append('hero letters')

# ---------- 3. Client WhatsApp (orders) ----------
n_wa = html.count('923061601587')
assert n_wa >= 5, f'expected >=5 order WA links, found {n_wa}'
html = html.replace('https://wa.me/923061601587', 'https://wa.me/923470098911')
edits.append(f'wa links x{n_wa}')
rep('WhatsApp par Order Karo — 0306 1601587', 'WhatsApp par Order Karo — 0347 0098911', 'visit btn text')

# ---------- 4. Product grid -> JS-rendered ----------
g_start = html.index('<div class="grid" id="balloonGrid">')
g_end = html.index('  </section>', g_start)
html = html[:g_start] + '      <div class="grid" id="balloonGrid"></div>\n    </div>\n' + html[g_end:]
edits.append('grid js-rendered')

# ---------- 5. Admin CSS (append before </style>) ----------
ADMIN_CSS = '''
/* ---------- admin panel (v2) ---------- */
.admin-wrap{max-width:780px;margin:0 auto}
.admin-card{background:#fff;border:1px solid var(--line);border-radius:20px;padding:26px;box-shadow:var(--shadow);margin-bottom:22px}
.admin-card h2{font-size:1.3rem;margin-bottom:6px}
.admin-card .hint{color:var(--ink2);font-size:.9rem;margin-bottom:18px}
.field{margin-bottom:14px}
.field label{display:block;font-weight:800;font-size:.85rem;margin-bottom:6px}
.field input,.field textarea,.field select{width:100%;padding:12px 14px;border:2px solid var(--line);border-radius:12px;font:inherit;font-size:.95rem;background:#fff}
.field input:focus,.field textarea:focus,.field select:focus{border-color:var(--pink);outline:none}
.field textarea{min-height:74px;resize:vertical}
#photoPreview{max-width:180px;border-radius:12px;margin-top:10px;display:none}
.admin-list .arow{display:flex;gap:12px;align-items:center;padding:10px 0;border-bottom:1px solid var(--line)}
.admin-list .arow:last-child{border-bottom:0}
.admin-list img{width:58px;height:58px;object-fit:cover;border-radius:10px;flex:none}
.admin-list .nm{font-weight:800;font-size:.95rem}
.admin-list .meta{color:var(--ink2);font-size:.82rem}
.abtn{border:0;cursor:pointer;font-weight:800;font-size:.82rem;padding:8px 14px;border-radius:999px}
.abtn.edit{background:#ede9fe;color:#6d28d9}
.abtn.del{background:#fee2e2;color:#b91c1c}
.abtn:disabled{opacity:.5;cursor:wait}
.msg{font-size:.9rem;font-weight:700;margin-top:10px}
.msg.err{color:#dc2626}.msg.ok{color:#15803d}
.rules-note{background:#fff7fb;border:1px dashed var(--pink);border-radius:16px;padding:18px;margin-top:6px}
.rules-note pre{background:#22103a;color:#ffe45e;padding:14px;border-radius:12px;overflow:auto;font-size:.7rem;line-height:1.5;margin-top:10px;white-space:pre-wrap;word-break:break-all}
.admin-link{color:#cfc4e8;font-size:.85rem}
.admin-link:hover{color:#fff}
'''
rep('</style>', ADMIN_CSS + '</style>', 'admin css')

# ---------- 6. Admin HTML (insert before wa-float) ----------
ADMIN_HTML = '''
<!-- ─── ADMIN PANEL (v2) ─── -->
<section id="adminView" style="display:none;padding:64px 0">
  <div class="wrap admin-wrap">
    <div class="admin-card" id="adminLoginCard">
      <h2>🔐 Admin Login</h2>
      <p class="hint">Sirf Aliyan (shop owner) login karega — email aur password Firebase mein banaya gaya hai.</p>
      <div class="field"><label>Email</label><input id="adminEmail" type="email" placeholder="admin email"></div>
      <div class="field"><label>Password</label><input id="adminPass" type="password" placeholder="password"></div>
      <div class="msg err" id="adminErr" style="display:none"></div>
      <button class="btn btn-pink" id="adminLoginBtn" onclick="doAdminLogin()">Login</button>
      <p style="margin-top:14px"><a href="#" onclick="showShop();return false">← Shop par wapas jao</a></p>
    </div>
    <div id="adminPanel" style="display:none">
      <div class="admin-card">
        <h2>➕ Naya Product Add Karo</h2>
        <p class="hint">Photo upload karo, naam, price aur description likho — Save karte hi product shop par live aa jayega.</p>
        <div class="field"><label>Photo *</label><input id="pPhoto" type="file" accept="image/*"><img id="photoPreview" alt="preview"></div>
        <div class="field"><label>Naam *</label><input id="pName" placeholder="e.g. Pink Birthday Balloon Set"></div>
        <div class="field"><label>Price (Rs) *</label><input id="pPrice" type="number" min="1" placeholder="e.g. 500"></div>
        <div class="field"><label>Category *</label><select id="pCat"><option value="birthday">Birthday</option><option value="cartoon">Cartoon</option><option value="helium">Helium</option><option value="bouquet">Bouquet</option><option value="decor">Decor</option></select></div>
        <div class="field"><label>Description *</label><textarea id="pDesc" placeholder="e.g. Pink stars aur hearts — birthday ke liye perfect set."></textarea></div>
        <div class="msg err" id="prodErr" style="display:none"></div>
        <div class="msg ok" id="prodOk" style="display:none"></div>
        <button class="btn btn-pink" id="saveProdBtn" onclick="saveProduct()">💾 Save Product</button>
        <button class="btn btn-ghost" id="cancelEditBtn" style="display:none;margin-left:8px" onclick="cancelEdit()">Cancel</button>
      </div>
      <div class="admin-card">
        <h2>📦 Products (<span id="adminCount">0</span>)</h2>
        <p class="hint">Neeche wale products abhi shop par dikh rahe hain. Edit ya Delete dabao.</p>
        <button class="btn btn-ghost" id="importBtn" onclick="importDemo()">📥 Demo wale 14 products import karo</button>
        <p class="hint" style="margin-top:10px">Sirf tab dabao jab products khaali hon — warna kuch nahi hoga. Agar saare products delete kar do ge to demo wale 14 phir dikhne lagenge.</p>
        <div class="admin-list" id="adminList"></div>
      </div>
      <div class="admin-card rules-note">
        <b>🔐 Firebase Rules:</b> Ye rules Firebase Console mein paste karo (pehle RTDB, phir Storage) — warna upload kaam nahi karega.
        <p style="margin-top:8px;font-size:.85rem"><b>Realtime Database → Rules:</b></p>
        <pre id="rtdbRules">{"rules":{"products":{".read":true,".write":"auth != null"}}}</pre>
        <p style="margin-top:8px;font-size:.85rem"><b>Storage → Rules:</b></p>
        <pre>rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /products/{fileName} {
      allow read: if true;
      allow write: if request.auth != null;
    }
  }
}</pre>
      </div>
      <button class="btn btn-ghost" onclick="doAdminLogout()">Logout</button>
      <a href="#" onclick="showShop();return false" style="margin-left:14px">← Shop Dekho</a>
    </div>
  </div>
</section>

'''
rep('<a class="wa-float"', ADMIN_HTML + '<a class="wa-float"', 'admin html')

# footer admin link
rep('<p class="gold">Website by SAJEEL MODS — Shop website Rs 1,000, 1 din mein tayyar • WhatsApp 0306 1601587</p>',
    '<p class="gold">Website by SAJEEL MODS — Shop website Rs 1,000, 1 din mein tayyar • WhatsApp 0306 1601587</p>\n    <p style="margin-top:14px"><a class="admin-link" href="#admin" onclick="showAdmin();return false">Admin Login</a></p>',
    'footer admin link')

# ---------- 7. Firebase SDK + new main script ----------
NEW_SCRIPT = '''<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-auth-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-database-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-storage-compat.js"></script>
<script>
// ===== Aliyan Balloons v2 — Firebase products + Admin =====
var SHOP_WA = '923470098911';
// TODO (SETUP.txt): Firebase project banao aur yahan apna config paste karo.
var firebaseConfig = {
  apiKey: "PASTE_YOUR_API_KEY",
  authDomain: "PASTE_YOUR_PROJECT.firebaseapp.com",
  databaseURL: "https://PASTE_YOUR_PROJECT-default-rtdb.firebaseio.com",
  projectId: "PASTE_YOUR_PROJECT",
  storageBucket: "PASTE_YOUR_PROJECT.appspot.com",
  messagingSenderId: "PASTE_YOUR_SENDER_ID",
  appId: "PASTE_YOUR_APP_ID"
};
var FIREBASE_ON = !!(firebaseConfig.apiKey && firebaseConfig.apiKey.indexOf('PASTE') !== 0);

var CATS = { birthday: 'Birthday', cartoon: 'Cartoon', helium: 'Helium', bouquet: 'Bouquet', decor: 'Decor' };
var DEFAULT_PRODUCTS = [
  { name: 'Unicorn & Cartoon Foil Balloons', desc: 'Unicorn, Doraemon aur troll — bachon ke favourite characters.', price: 300, cat: 'cartoon', img: 'balloon-1.jpg' },
  { name: 'Jungle Birthday Theme Set', desc: 'Gold HAPPY BIRTHDAY + tiger, lion, zebra, giraffe — poora jungle theme.', price: 2500, cat: 'birthday', img: 'balloon-2.jpg' },
  { name: '"50" Number Foil Balloons', desc: '50th birthday ke liye bare pink number balloons — showstopper.', price: 800, cat: 'birthday', img: 'balloon-3.jpg' },
  { name: 'Happy Birthday Foil Balloon — Helium', desc: 'Navy blue foil, helium filled — upar tairta hai, der tak chalta hai.', price: 350, cat: 'helium', img: 'balloon-4.jpg' },
  { name: 'Pink Birthday Foil Balloon Set', desc: 'Stars, hearts aur Happy Birthday rounds — pink theme set.', price: 1200, cat: 'birthday', img: 'balloon-5.jpg' },
  { name: 'Navy & Gold Birthday Bouquet', desc: '"Best Day" bubble + navy, marble aur gold confetti balloons.', price: 1800, cat: 'bouquet', img: 'balloon-6.jpg' },
  { name: 'Colorful Happy Birthday Foil Set', desc: 'Red, yellow, blue aur star — colorful birthday set.', price: 900, cat: 'birthday', img: 'balloon-7.jpg' },
  { name: 'Silver Star & Red Heart Bouquet', desc: 'Silver stars aur red hearts — asmaan jaisa khubsurat bouquet.', price: 1000, cat: 'bouquet', img: 'balloon-8.jpg' },
  { name: 'Colorful Party Balloon Bunches', desc: 'Blue, yellow, pink, white — poora room sajao, party tayyar.', price: 1500, cat: 'decor', img: 'balloon-9.jpg' },
  { name: 'Gold & White Ceiling Balloon Decor', desc: 'Gold aur white ceiling decor — premium birthday setup.', price: 2500, cat: 'decor', img: 'balloon-10.jpg' },
  { name: '“You’re So Special” Foil Balloons', desc: 'Star print foil — kisi khaas ko gift karo, muskurahat pakki.', price: 400, cat: 'birthday', img: 'balloon-11.jpg' },
  { name: 'Red Heart Foil Balloons', desc: 'Red hearts bunch — anniversary aur birthday ke liye perfect.', price: 600, cat: 'birthday', img: 'balloon-12.jpg' },
  { name: 'Cat, Dora & Hello Kitty Foil Balloons', desc: 'Cat, Dora aur Hello Kitty — bachon ki sab se bari pasand.', price: 350, cat: 'cartoon', img: 'balloon-13.jpg' },
  { name: 'Animal Hand Balloons — Set of 10', desc: 'Astronaut, cat, dino, lion — 10 cute animal balloons, ek sath.', price: 500, cat: 'cartoon', img: 'balloon-14.jpg' }
];

var allProducts = DEFAULT_PRODUCTS.slice();
var activeCat = 'all';
var fbApp = null, fbDb = null, fbAuth = null, fbStorage = null;
var isAdmin = false, productsBound = false, editingId = null;

function esc(s){ s = String(s == null ? '' : s); var m = {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}; return s.replace(/[&<>"']/g, function(c){ return m[c]; }); }
function orderUrl(p){ return 'https://wa.me/' + SHOP_WA + '?text=' + encodeURIComponent('Assalam-o-Alaikum! Mujhe ' + p.name + ' (Rs ' + p.price + ') order karna hai.'); }

function cardHTML(p){
  return '<article class="prod reveal" data-cat="' + esc(p.cat) + '"><div class="ph"><img src="' + esc(p.img) + '" alt="' + esc(p.name) + '" loading="lazy"><span class="badge">' + esc(CATS[p.cat] || p.cat) + '</span></div><div class="body"><h3>' + esc(p.name) + '</h3><p>' + esc(p.desc) + '</p><div class="row"><span class="price">Rs ' + Number(p.price).toLocaleString('en-US') + '</span><a class="order-btn" href="' + orderUrl(p) + '" target="_blank" rel="noopener">Order Karo</a></div></div></article>';
}
function observeReveals(){
  var targets = document.querySelectorAll('#balloonGrid .reveal:not(.in)');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
    }, { threshold: 0.12 });
    targets.forEach(function (t) { io.observe(t); });
  } else {
    targets.forEach(function (t) { t.classList.add('in'); });
  }
}
function updateFilterLabels(){
  var counts = { all: allProducts.length, birthday: 0, cartoon: 0, helium: 0, bouquet: 0, decor: 0 };
  allProducts.forEach(function (p) { if (counts[p.cat] != null) counts[p.cat]++; });
  var labels = { all: 'Sab', birthday: 'Birthday', cartoon: 'Cartoon', helium: 'Helium', bouquet: 'Bouquet', decor: 'Decor' };
  document.querySelectorAll('#filters .fbtn').forEach(function (b) {
    var c = b.getAttribute('data-cat');
    b.textContent = labels[c] + ' (' + (counts[c] || 0) + ')';
  });
  var note = document.getElementById('countNote');
  var shown = allProducts.filter(function (p) { return activeCat === 'all' || p.cat === activeCat; }).length;
  note.textContent = shown + ' balloons — ' + (activeCat === 'all' ? 'sab categories' : (CATS[activeCat] || activeCat));
}
function renderProducts(list){
  allProducts = list.slice();
  document.getElementById('balloonGrid').innerHTML = list.map(cardHTML).join('');
  updateFilterLabels();
  applyFilter(activeCat, true);
  observeReveals();
}
function applyFilter(cat, skipNote){
  activeCat = cat;
  var shown = 0;
  document.querySelectorAll('#balloonGrid .prod').forEach(function (c) {
    var show = cat === 'all' || c.getAttribute('data-cat') === cat;
    c.style.display = show ? '' : 'none';
    if (show) shown++;
  });
  if (!skipNote) {
    document.getElementById('countNote').textContent = shown + ' balloons — ' + (cat === 'all' ? 'sab categories' : (CATS[cat] || cat));
  }
  document.querySelectorAll('#filters .fbtn').forEach(function (b) {
    b.classList.toggle('active', b.getAttribute('data-cat') === cat);
  });
  return shown;
}

// ---------- Firebase ----------
function initFirebase(){
  if (!FIREBASE_ON || typeof firebase === 'undefined') return;
  try {
    fbApp = firebase.initializeApp(firebaseConfig);
    fbDb = firebase.database();
    fbAuth = firebase.auth();
    fbStorage = firebase.storage();
    bindAuthListener();
    startProductsListener();
  } catch (e) { /* Firebase off — demo products dikhenge */ }
}
function bindAuthListener(){
  if (!fbAuth) return;
  fbAuth.onAuthStateChanged(function (u) {
    isAdmin = !!u;
    if (u && document.getElementById('adminView').style.display !== 'none') showAdminPanel();
  });
}
function startProductsListener(){
  if (!fbDb || productsBound) return;
  productsBound = true;
  fbDb.ref('products').on('value', function (snap) {
    var v = snap.val();
    if (v && Object.keys(v).length) {
      var list = Object.keys(v).map(function (k) { var p = v[k]; p.id = k; return p; });
      list.sort(function (a, b) { return (a.createdAt || 0) - (b.createdAt || 0); });
      renderProducts(list);
      if (isAdmin) renderAdminList(list);
    } else {
      renderProducts(DEFAULT_PRODUCTS);
      if (isAdmin) renderAdminList(DEFAULT_PRODUCTS);
    }
  });
}

// ---------- Admin ----------
function showAdmin(){
  document.querySelector('main').style.display = 'none';
  document.getElementById('adminView').style.display = 'block';
  window.scrollTo(0, 0);
  if (!FIREBASE_ON) {
    var e = document.getElementById('adminErr');
    e.textContent = '❌ Firebase setup nahi hua — pehle SETUP.txt wale steps karo aur firebaseConfig paste karo.';
    e.style.display = 'block';
  }
  if (fbAuth && fbAuth.currentUser) showAdminPanel();
  else { document.getElementById('adminLoginCard').style.display = 'block'; document.getElementById('adminPanel').style.display = 'none'; }
}
function showShop(){
  document.getElementById('adminView').style.display = 'none';
  document.querySelector('main').style.display = '';
  if (location.hash === '#admin') history.replaceState(null, '', location.pathname);
}
function showAdminPanel(){
  document.getElementById('adminLoginCard').style.display = 'none';
  document.getElementById('adminPanel').style.display = 'block';
  renderAdminList(allProducts);
}
function doAdminLogin(){
  var err = document.getElementById('adminErr');
  err.style.display = 'none';
  var email = (document.getElementById('adminEmail').value || '').trim();
  var pass = document.getElementById('adminPass').value;
  if (!email || !pass) { err.textContent = '❌ Email aur password likho.'; err.style.display = 'block'; return; }
  if (!fbAuth) { err.textContent = '❌ Firebase not connected.'; err.style.display = 'block'; return; }
  fbAuth.signInWithEmailAndPassword(email, pass).catch(function (e) {
    err.textContent = '❌ Login failed: ' + (e.code === 'auth/user-not-found' ? 'User not found.' : e.code === 'auth/wrong-password' ? 'Wrong password.' : e.message);
    err.style.display = 'block';
  });
}
function doAdminLogout(){
  if (fbAuth) fbAuth.signOut();
  isAdmin = false;
  showShop();
}
function validateProduct(p){
  if (!p.name) return 'Naam likho.';
  if (!(p.price > 0)) return 'Sahi price likho (Rs).';
  if (!p.cat || !CATS[p.cat]) return 'Category chuno.';
  if (!p.desc) return 'Description likho.';
  if (!p.img) return 'Photo chuno.';
  return '';
}
function readFormProduct(){
  return {
    name: (document.getElementById('pName').value || '').trim(),
    price: parseInt(document.getElementById('pPrice').value, 10) || 0,
    cat: document.getElementById('pCat').value,
    desc: (document.getElementById('pDesc').value || '').trim(),
    img: window.__pendingPhotoUrl || ''
  };
}
function clearForm(){
  ['pName', 'pPrice', 'pDesc'].forEach(function (id) { document.getElementById(id).value = ''; });
  document.getElementById('pPhoto').value = '';
  document.getElementById('photoPreview').style.display = 'none';
  window.__pendingPhotoUrl = '';
  editingId = null;
  document.getElementById('saveProdBtn').textContent = '💾 Save Product';
  document.getElementById('cancelEditBtn').style.display = 'none';
}
function showProdMsg(kind, msg){
  var e = document.getElementById(kind === 'err' ? 'prodErr' : 'prodOk');
  var o = document.getElementById(kind === 'err' ? 'prodOk' : 'prodErr');
  o.style.display = 'none';
  e.textContent = msg; e.style.display = 'block';
}
async function saveProduct(){
  var btn = document.getElementById('saveProdBtn');
  var p = readFormProduct();
  var file = document.getElementById('pPhoto').files[0];
  if (editingId && !file) {
    var cur = allProducts.find(function (x) { return x.id === editingId; });
    if (cur) p.img = cur.img;
  }
  if (!file && !p.img) { showProdMsg('err', '❌ Photo chuno.'); return; }
  var v = validateProduct(file ? Object.assign({}, p, { img: 'file-chosen' }) : p);
  if (v) { showProdMsg('err', '❌ ' + v); return; }
  if (!fbDb) { showProdMsg('err', '❌ Firebase not connected — SETUP.txt dekho.'); return; }
  btn.disabled = true;
  btn.textContent = file ? '⏳ Photo upload ho rahi hai...' : '⏳ Save ho raha hai...';
  try {
    if (file) {
      var path = 'products/' + Date.now() + '_' + file.name.replace(/[^a-zA-Z0-9._-]/g, '_');
      var snap = await fbStorage.ref(path).put(file);
      p.img = await snap.ref.getDownloadURL();
    }
    if (editingId) {
      await fbDb.ref('products/' + editingId).update(p);
      showProdMsg('ok', '✅ Product update ho gaya!');
    } else {
      p.createdAt = Date.now();
      await fbDb.ref('products').push(p);
      showProdMsg('ok', '✅ Product add ho gaya — shop par live hai!');
    }
    clearForm();
  } catch (e) {
    showProdMsg('err', '❌ Save nahi hua: ' + (e.message || e));
  } finally {
    btn.disabled = false;
    btn.textContent = '💾 Save Product';
  }
}
function editProduct(id){
  var p = allProducts.find(function (x) { return x.id === id || x.name === id; });
  if (!p) return;
  editingId = p.id || p.name;
  document.getElementById('pName').value = p.name;
  document.getElementById('pPrice').value = p.price;
  document.getElementById('pCat').value = p.cat;
  document.getElementById('pDesc').value = p.desc;
  window.__pendingPhotoUrl = p.img || '';
  var prev = document.getElementById('photoPreview');
  if (p.img) { prev.src = p.img; prev.style.display = 'block'; }
  document.getElementById('saveProdBtn').textContent = '💾 Update Product';
  document.getElementById('cancelEditBtn').style.display = 'inline-flex';
  var top = document.getElementById('adminLoginCard');
  if (top && top.scrollIntoView) top.scrollIntoView({ behavior: 'smooth' });
  window.scrollTo(0, 0);
}
function cancelEdit(){ clearForm(); }
function deleteProduct(id){
  if (!confirm('Ye product delete kar dun?')) return;
  if (!fbDb) return;
  fbDb.ref('products/' + id).remove();
}
function renderAdminList(list){
  var box = document.getElementById('adminList');
  document.getElementById('adminCount').textContent = list.length;
  if (!list.length) { box.innerHTML = '<p class="hint">Koi product nahi — upar se add karo ya demo wale import karo.</p>'; return; }
  box.innerHTML = list.map(function (p) {
    var key = p.id || p.name;
    return '<div class="arow"><img src="' + esc(p.img) + '" alt=""><div style="flex:1"><div class="nm">' + esc(p.name) + '</div><div class="meta">Rs ' + Number(p.price).toLocaleString('en-US') + ' • ' + esc(CATS[p.cat] || p.cat) + '</div></div>' +
      (p.id ? '<button class="abtn edit" onclick="editProduct(\\'' + String(p.id).replace(/'/g, '') + '\\')">Edit</button><button class="abtn del" onclick="deleteProduct(\\'' + String(p.id).replace(/'/g, '') + '\\')">Delete</button>' : '<span class="meta">demo</span>') + '</div>';
  }).join('');
}
async function importDemo(){
  var btn = document.getElementById('importBtn');
  if (!fbDb) { showProdMsg('err', '❌ Firebase not connected — SETUP.txt dekho.'); return; }
  var snap = await fbDb.ref('products').once('value');
  if (snap.val()) { showProdMsg('err', 'Products pehle se hain — import ki zaroorat nahi.'); return; }
  btn.disabled = true; btn.textContent = '⏳ Import ho raha hai...';
  try {
    for (var i = 0; i < DEFAULT_PRODUCTS.length; i++) {
      var p = Object.assign({}, DEFAULT_PRODUCTS[i]);
      p.createdAt = Date.now() + i;
      await fbDb.ref('products').push(p);
    }
    showProdMsg('ok', '✅ 14 demo products import ho gaye!');
  } catch (e) {
    showProdMsg('err', '❌ Import nahi hua: ' + (e.message || e));
  } finally {
    btn.disabled = false; btn.textContent = '📥 Demo wale 14 products import karo';
  }
}

// ---------- photo preview ----------
document.getElementById('pPhoto').addEventListener('change', function (e) {
  var f = e.target.files[0];
  var prev = document.getElementById('photoPreview');
  if (f) { prev.src = URL.createObjectURL(f); prev.style.display = 'block'; }
  else { prev.style.display = 'none'; }
});

// ---------- init ----------
(function () {
  renderProducts(DEFAULT_PRODUCTS);
  document.getElementById('filters').addEventListener('click', function (e) {
    var b = e.target && e.target.closest ? e.target.closest('.fbtn') : null;
    if (b) applyFilter(b.getAttribute('data-cat'));
  });
  if (location.hash === '#admin') showAdmin();
  initFirebase();
  window.__BALLOON = {
    filter: applyFilter,
    visibleCount: function () {
      var n = 0;
      document.querySelectorAll('#balloonGrid .prod').forEach(function (c) { if (c.style.display !== 'none') n++; });
      return n;
    },
    getProducts: function () { return allProducts; },
    validateProduct: validateProduct,
    renderProducts: renderProducts,
    buildOrderUrl: orderUrl,
    DEFAULT_PRODUCTS: DEFAULT_PRODUCTS,
    SHOP_WA: SHOP_WA,
    _setFirebase: function (db, auth, storage) { fbDb = db; fbAuth = auth; fbStorage = storage; bindAuthListener(); startProductsListener(); },
    _getFbDb: function () { return fbDb; }
  };
})();
</script>
</body>
</html>'''

s_start = html.index('<script>\n(function () {')
s_end = html.index('</script>', s_start) + len('</script>')
html = html[:s_start] + NEW_SCRIPT + html[s_end:]
edits.append('firebase sdk + new script')

# ---------- write out ----------
os.makedirs(DST_DIR, exist_ok=True)
with open(os.path.join(DST_DIR, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(html)
for i in range(1, 15):
    shutil.copy(os.path.join(SRC_DIR, f'balloon-{i}.jpg'), os.path.join(DST_DIR, f'balloon-{i}.jpg'))

print(f'OK: {len(edits)} edits applied: ' + ', '.join(edits))
print(f'chars: {orig_len} -> {len(html)}')
print(f'files in {DST_DIR}: ' + ', '.join(sorted(os.listdir(DST_DIR))))
