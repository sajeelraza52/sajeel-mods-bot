// jsdom tests for Balloon Shop v2: Firebase products + Admin panel (Aliyan, 03470098911)
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf-8');

let failures = 0;
function check(name, cond, extra) {
  console.log((cond ? 'PASS' : 'FAIL') + ' — ' + name + (cond ? '' : ' :: ' + (extra || '')));
  if (!cond) failures++;
}

function makeVc(errors) {
  const vc = new VirtualConsole();
  vc.on('jsdomError', e => {
    const msg = String(e && e.message || e);
    if (/Not implemented/i.test(msg)) return;
    errors.push(msg);
  });
  return vc;
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---------- Listener-aware Fake Firebase ----------
function makeFakeFirebase(seedProducts) {
  const data = {
    products: seedProducts || null,
    users: {},
    admins: {}
  };
  const snap = v => ({ val: () => v, exists: () => v !== null && v !== undefined });
  const getAt = p => {
    const parts = p.split('/').filter(Boolean);
    let cur = data;
    for (const k of parts) { if (cur == null) return null; cur = cur[k]; }
    return cur === undefined ? null : cur;
  };
  const setAt = (p, val) => {
    const parts = p.split('/').filter(Boolean);
    let cur = data;
    for (let i = 0; i < parts.length - 1; i++) { cur[parts[i]] = cur[parts[i]] || {}; cur = cur[parts[i]]; }
    cur[parts[parts.length - 1]] = val;
  };
  const listeners = {};
  const fire = p => { (listeners[p] || []).forEach(cb => { try { cb(snap(getAt(p))); } catch (e) {} }); };
  const ref = p => ({
    on: (ev, cb) => { (listeners[p] = listeners[p] || []).push(cb); try { cb(snap(getAt(p))); } catch (e) {} return () => {}; },
    off: () => { delete listeners[p]; },
    once: () => Promise.resolve(snap(getAt(p))),
    push: val => {
      const key = 'prod' + Math.random().toString(36).slice(2, 8);
      setAt(p + '/' + key, val);
      fire(p);
      return Promise.resolve({ key });
    },
    set: val => { setAt(p, val); fire(p); return Promise.resolve(); },
    update: obj => { const cur = getAt(p) || {}; setAt(p, Object.assign({}, cur, obj)); fire(p); return Promise.resolve(); },
    remove: () => {
      const parts = p.split('/').filter(Boolean);
      let cur = data;
      for (let i = 0; i < parts.length - 1; i++) cur = cur[parts[i]];
      delete cur[parts[parts.length - 1]];
      fire(parts.slice(0, -1).join('/'));
      return Promise.resolve();
    }
  });
  const storageRef = path => ({
    put: file => Promise.resolve({ ref: { getDownloadURL: () => Promise.resolve('https://storage.fake/' + path) } })
  });
  let signOutCalls = 0;
  const authCbs = [];
  const authObj = {
    onAuthStateChanged: cb => { authCbs.push(cb); setTimeout(() => cb({ uid: 'admin-uid', email: 'aliyan@shop.com' }), 0); },
    signInWithEmailAndPassword: () => Promise.resolve({ user: { uid: 'admin-uid' } }).then(r => { authCbs.forEach(cb => { try { cb({ uid: 'admin-uid', email: 'aliyan@shop.com' }); } catch (e) {} }); return r; }),
    signOut: () => { signOutCalls++; return Promise.resolve(); }
  };
  return {
    data,
    fire,
    get signOutCalls() { return signOutCalls; },
    stub: {
      initializeApp: () => ({}),
      auth: () => authObj,
      database: () => ({ ref }),
      storage: () => ({ ref: storageRef })
    }
  };
}

async function runPlain() {
  const errors = [];
  const dom = new JSDOM(html, {
    url: 'https://aliyan-balloons.vercel.app/',
    runScripts: 'dangerously',
    pretendToBeVisual: true,
    virtualConsole: makeVc(errors)
  });
  const { window } = dom;
  const { document } = window;
  window.URL.createObjectURL = () => 'blob:fake';
  window.URL.revokeObjectURL = () => {};
  await sleep(50);

  check('no JS errors on load (plain)', errors.length === 0, errors.join(' | '));
  check('shop name is Aliyan Balloons', document.title.includes('Aliyan Balloons') && document.querySelector('.logo').textContent.includes('Aliyan'));
  check('no SAMPLE pill, no Balloon Bliss', !document.body.textContent.includes('SAMPLE') && !document.body.textContent.includes('Balloon Bliss'));
  check('14 default cards render', document.querySelectorAll('#balloonGrid .prod').length === 14);
  check('order links use client WhatsApp 923470098911', [...document.querySelectorAll('.order-btn')].every(a => a.href.includes('wa.me/923470098911')));
  check('no order link uses old 923061601587', ![...document.querySelectorAll('.order-btn')].some(a => a.href.includes('923061601587')));
  check('filter birthday shows 6', window.__BALLOON.filter('birthday') === 6 && window.__BALLOON.visibleCount() === 6);
  check('filter cartoon shows 3', window.__BALLOON.filter('cartoon') === 3);
  check('filter helium shows 1', window.__BALLOON.filter('helium') === 1);
  check('filter bouquet shows 2', window.__BALLOON.filter('bouquet') === 2);
  check('filter decor shows 2', window.__BALLOON.filter('decor') === 2);
  check('filter all shows 14', window.__BALLOON.filter('all') === 14);
  check('filter buttons show counts', document.querySelector('[data-cat="birthday"]').textContent.includes('(6)'));
  check('buildOrderUrl uses client number', window.__BALLOON.buildOrderUrl({ name: 'Test', price: 500 }).startsWith('https://wa.me/923470098911?text='));
  check('SHOP_WA is client number', window.__BALLOON.SHOP_WA === '923470098911');

  const V = window.__BALLOON.validateProduct;
  const good = { name: 'Test', price: 500, cat: 'birthday', desc: 'Nice', img: 'x.jpg' };
  check('validate: good product passes', V(good) === '');
  check('validate: missing name fails', V({ ...good, name: '' }) !== '');
  check('validate: zero price fails', V({ ...good, price: 0 }) !== '');
  check('validate: bad category fails', V({ ...good, cat: 'nope' }) !== '');
  check('validate: missing desc fails', V({ ...good, desc: '' }) !== '');
  check('validate: missing photo fails', V({ ...good, img: '' }) !== '');

  check('admin view hidden by default', document.getElementById('adminView').style.display === 'none');
  check('admin login form exists', !!document.getElementById('adminEmail') && !!document.getElementById('adminPass'));
  check('add-product form exists', !!document.getElementById('pPhoto') && !!document.getElementById('pName') && !!document.getElementById('pPrice') && !!document.getElementById('pCat') && !!document.getElementById('pDesc'));
  check('import button exists', !!document.getElementById('importBtn'));
  check('rules note has products read/write', document.getElementById('rtdbRules').textContent.includes('"products"') && document.getElementById('rtdbRules').textContent.includes('auth != null'));
  check('firebase config is placeholder (not live)', html.includes('PASTE_YOUR_API_KEY'));
}

async function runAdminHash() {
  const errors = [];
  const dom = new JSDOM(html, {
    url: 'https://aliyan-balloons.vercel.app/#admin',
    runScripts: 'dangerously',
    pretendToBeVisual: true,
    virtualConsole: makeVc(errors)
  });
  const { window } = dom;
  const { document } = window;
  window.URL.createObjectURL = () => 'blob:fake';
  window.URL.revokeObjectURL = () => {};
  await sleep(50);
  check('#admin hash opens admin view', document.getElementById('adminView').style.display === 'block' && document.querySelector('main').style.display === 'none');
  check('#admin shows Firebase setup warning (no config yet)', document.getElementById('adminErr').style.display === 'block');
}

async function runAuthed() {
  const errors = [];
  const fake = makeFakeFirebase({
    p1: { name: 'RTDB Balloon', desc: 'From database', price: 700, cat: 'birthday', img: 'https://storage.fake/a.jpg', createdAt: 100 },
    p2: { name: 'RTDB Cartoon', desc: 'From database 2', price: 400, cat: 'cartoon', img: 'https://storage.fake/b.jpg', createdAt: 200 }
  });
  const dom = new JSDOM(html, {
    url: 'https://aliyan-balloons.vercel.app/',
    runScripts: 'dangerously',
    pretendToBeVisual: true,
    virtualConsole: makeVc(errors),
    beforeParse(window) { window.firebase = fake.stub; }
  });
  const { window } = dom;
  const { document } = window;
  window.URL.createObjectURL = () => 'blob:fake';
  window.URL.revokeObjectURL = () => {};
  window.confirm = () => true;
  await sleep(100);

  check('no JS errors on load (authed)', errors.length === 0, errors.join(' | '));
  // wire the fake Firebase into the page via the test hook
  window.__BALLOON._setFirebase(fake.stub.database(), fake.stub.auth(), fake.stub.storage());
  await sleep(50);
  check('RTDB products render instead of defaults', document.querySelectorAll('#balloonGrid .prod').length === 2 && document.body.textContent.includes('RTDB Balloon'));
  check('RTDB product order link uses client number', [...document.querySelectorAll('.order-btn')].every(a => a.href.includes('wa.me/923470098911')));
  check('RTDB filter birthday shows 1', window.__BALLOON.filter('birthday') === 1);
  window.__BALLOON.filter('all');

  // admin login flow: open admin view, login via fake auth
  window.showAdmin();
  await sleep(50);
  check('admin view opens', document.getElementById('adminView').style.display === 'block');
  document.getElementById('adminEmail').value = 'aliyan@shop.com';
  document.getElementById('adminPass').value = 'secret123';
  window.doAdminLogin();
  await sleep(100);
  check('admin login shows panel', document.getElementById('adminPanel').style.display === 'block');
  check('admin list shows 2 RTDB products', document.getElementById('adminCount').textContent === '2');

  // add a product with a photo upload
  const file = new window.File(['fake-image-bytes'], 'new-balloon.jpg', { type: 'image/jpeg' });
  const photoInput = document.getElementById('pPhoto');
  Object.defineProperty(photoInput, 'files', { value: [file], configurable: true });
  document.getElementById('pName').value = 'New Pink Balloon';
  document.getElementById('pPrice').value = '650';
  document.getElementById('pCat').value = 'birthday';
  document.getElementById('pDesc').value = 'Brand new pink balloon.';
  await window.saveProduct();
  await sleep(50);
  const added = Object.values(fake.data.products).find(p => p.name === 'New Pink Balloon');
  check('saveProduct uploads photo + pushes product', !!added && added.img.startsWith('https://storage.fake/products/'));
  check('saveProduct stored price + category', !!added && added.price === 650 && added.cat === 'birthday');
  check('grid shows new product', document.body.textContent.includes('New Pink Balloon'));

  // edit the seeded product p1 (change price, keep photo)
  window.editProduct('p1');
  check('editProduct fills the form', document.getElementById('pName').value === 'RTDB Balloon');
  document.getElementById('pPrice').value = '750';
  Object.defineProperty(photoInput, 'files', { value: [], configurable: true });
  await window.saveProduct();
  await sleep(50);
  check('editProduct updates price, keeps photo', fake.data.products.p1.price === 750 && fake.data.products.p1.img === 'https://storage.fake/a.jpg');

  // delete p2
  window.deleteProduct('p2');
  await sleep(50);
  check('deleteProduct removes it', !fake.data.products.p2);
}

async function runImport() {
  const errors = [];
  const fake = makeFakeFirebase();
  const dom = new JSDOM(html, {
    url: 'https://aliyan-balloons.vercel.app/',
    runScripts: 'dangerously',
    pretendToBeVisual: true,
    virtualConsole: makeVc(errors),
    beforeParse(window) { window.firebase = fake.stub; }
  });
  const { window } = dom;
  const { document } = window;
  window.URL.createObjectURL = () => 'blob:fake';
  window.URL.revokeObjectURL = () => {};
  await sleep(100);
  check('no JS errors on load (import run)', errors.length === 0, errors.join(' | '));
  window.__BALLOON._setFirebase(fake.stub.database(), fake.stub.auth(), fake.stub.storage());
  await sleep(50);
  check('empty RTDB falls back to 14 defaults', document.querySelectorAll('#balloonGrid .prod').length === 14);
  await window.importDemo();
  await sleep(100);
  check('importDemo seeds 14 products', Object.keys(fake.data.products).length === 14);
  check('grid now renders RTDB products', document.querySelectorAll('#balloonGrid .prod').length === 14);
  await window.importDemo();
  await sleep(50);
  check('importDemo twice does not duplicate', Object.keys(fake.data.products).length === 14);
}

(async () => {
  await runPlain();
  await runAdminHash();
  await runAuthed();
  await runImport();
  console.log(failures === 0 ? 'ALL PASS' : failures + ' FAILURES');
  process.exit(failures === 0 ? 0 : 1);
})();
