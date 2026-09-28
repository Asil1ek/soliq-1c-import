let currentMode = 'nomenklaturno';
let lastCardSumRaw = 0;
let allSotuvItems = [];
let allQaytItems = [];
let filteredItems = [];
let currentFilter = 'all';
let currentPage = 1;
const pageSize = 20;

// Mode configurations
const MODE_CONFIG = {
  nomenklaturno: {
    label: 'Пономенклатурно',
    searchField: 'Номенклатура (nomi)',
    searchCol: 2,
    dlSotuv: 'sotuv_nomenklaturno',
    dlQayt: 'qayt_nomenklaturno',
    desc: 'Tovar nomi bo\'yicha qidiriladi (Поле поиска = 2-ustun)',
  },
  ikpu: {
    label: 'По ИКПУ (МХИК)',
    searchField: 'ИКПУ',
    searchCol: 4,
    dlSotuv: 'sotuv_ikpu',
    dlQayt: 'qayt_ikpu',
    desc: '17 xonali MXIK kodi bo\'yicha qidiriladi (Поле поиска = 4-ustun)',
  },
  artikul: {
    label: 'По Артикулу (Штрихкод)',
    searchField: 'Артикул',
    searchCol: 3,
    dlSotuv: 'sotuv_artikul',
    dlQayt: 'qayt_artikul',
    desc: 'Shtrixkod bo\'yicha qidiriladi (Поле поиска = 3-ustun)',
  },
  kod: {
    label: 'По Коду номенклатуры',
    searchField: 'Код номенклатуры',
    searchCol: 1,
    dlSotuv: 'sotuv_kod',
    dlQayt: 'qayt_kod',
    desc: '1C nomenklatura kodi bo\'yicha qidiriladi (Поле поиска = 1-ustun)',
  }
};

document.addEventListener('DOMContentLoaded', () => {
  checkStatus();
  setupDragAndDrop();
  renderSettingsGuide('nomenklaturno');
  updateDownloadLinks('nomenklaturno');
});

function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  let icon = '✅';
  if (type === 'info') icon = 'ℹ️';
  if (type === 'error') icon = '⚠️';

  toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function formatMoney(val) {
  if (val === undefined || val === null) return "0.00 so'm";
  return new Intl.NumberFormat('uz-UZ', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(val) + " so'm";
}

async function checkStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    if (data.detected_files && data.detected_files.sotuv && data.detected_files.sotuv.length > 0) {
      const banner = document.getElementById('detected-banner');
      const list = document.getElementById('detected-files-list');
      const allFiles = [
        ...data.detected_files.sotuv,
        ...data.detected_files.qaytarish,
        ...data.detected_files.nomenklatura
      ];
      list.textContent = allFiles.join(' | ');
      banner.classList.remove('hidden');
    }
  } catch (e) {
    console.log("Status error:", e);
  }
}

function setupDragAndDrop() {
  ['sotuv', 'qayt', 'nom'].forEach(key => {
    const card = document.getElementById(`drop-${key}`);
    const input = document.getElementById(`file-${key}`);
    const chip = document.getElementById(`info-${key}`);

    input.addEventListener('change', () => {
      if (input.files.length > 0) {
        chip.textContent = input.files[0].name;
        chip.classList.add('selected');
      } else {
        chip.textContent = "Faylni tanlang";
        chip.classList.remove('selected');
      }
    });

    ['dragenter', 'dragover'].forEach(evt => {
      card.addEventListener(evt, (e) => {
        e.preventDefault();
        card.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(evt => {
      card.addEventListener(evt, (e) => {
        e.preventDefault();
        card.classList.remove('dragover');
      });
    });

    card.addEventListener('drop', (e) => {
      if (e.dataTransfer.files.length > 0) {
        input.files = e.dataTransfer.files;
        chip.textContent = input.files[0].name;
        chip.classList.add('selected');
        showToast(`${input.files[0].name} yuklandi`, 'info');
      }
    });
  });
}

function processExistingFiles() {
  submitFiles();
}

async function submitFiles() {
  const btn = document.getElementById('btn-process');
  const spinner = document.getElementById('btn-spinner');
  btn.disabled = true;
  spinner.classList.remove('hidden');

  const form = new FormData();
  const fileSotuv = document.getElementById('file-sotuv').files[0];
  const fileQayt = document.getElementById('file-qayt').files[0];
  const fileNom = document.getElementById('file-nom').files[0];

  if (fileSotuv) form.append('sotuv_file', fileSotuv);
  if (fileQayt) form.append('qayt_file', fileQayt);
  if (fileNom) form.append('nom_file', fileNom);

  try {
    const res = await fetch('/api/process', {
      method: 'POST',
      body: form
    });
    const data = await res.json();

    if (!res.ok) {
      showToast(data.error || "Tahlil jarayonida xatolik yuz berdi", 'error');
      return;
    }

    showToast("Cheklar muvaffaqiyatli tahlil qilindi! Qaytarishlar ayrilgan.", 'success');
    displayResults(data);

  } catch (err) {
    showToast("Server bilan aloqa uzildi: " + err.message, 'error');
  } finally {
    btn.disabled = false;
    spinner.classList.add('hidden');
  }
}

function displayResults(data) {
  document.getElementById('results-wrapper').classList.remove('hidden');
  document.getElementById('wf-step-2').classList.add('active');
  document.getElementById('wf-step-3').classList.add('active');

  const s = data.sotuv;     // Original sotuv
  const n = data.net;       // NET sotuv (sotuv - qaytarish)
  const q = data.qaytarish; // Qaytarish

  // NET metrics (main display)
  document.getElementById('sotuv-total-sum').textContent = formatMoney(n.total_sum);
  document.getElementById('sotuv-cash-sum').textContent = formatMoney(n.total_cash);
  document.getElementById('sotuv-vat-sum').textContent = formatMoney(n.total_vat);
  document.getElementById('sotuv-items-count').textContent = n.unique_products.toLocaleString() + " ta";
  document.getElementById('sotuv-rows-count').textContent = s.unique_receipts.toLocaleString() + " ta";
  document.getElementById('sotuv-receipts-badge').textContent = s.unique_receipts.toLocaleString() + " ta chek";

  // Original sotuv va qaytarish summary
  document.getElementById('sotuv-original-sum').textContent = formatMoney(s.total_sum);
  document.getElementById('sotuv-return-sum').textContent = q ? formatMoney(q.total_sum) : formatMoney(0);

  // Card sum (NET)
  lastCardSumRaw = n.total_card;
  document.getElementById('sotuv-card-sum').textContent = formatMoney(n.total_card);

  if (data.sotuv_file_name) {
    document.getElementById('sotuv-file-label').textContent = "(" + data.sotuv_file_name + ")";
  }

  // Payment percentages (based on original)
  const total = s.total_cash + s.total_card;
  if (total > 0) {
    const cashPct = ((s.total_cash / total) * 100).toFixed(1);
    const cardPct = ((s.total_card / total) * 100).toFixed(1);
    document.getElementById('cash-percent-label').textContent = `Naqd: ${cashPct}%`;
    document.getElementById('card-percent-label').textContent = `Karta: ${cardPct}%`;
    document.getElementById('split-bar-cash').style.width = cashPct + '%';
    document.getElementById('split-bar-card').style.width = cardPct + '%';
  }

  // Qaytarish
  if (q) {
    document.getElementById('qayt-total-sum').textContent = formatMoney(q.total_sum);
    document.getElementById('qayt-cash-sum').textContent = formatMoney(q.total_cash);
    document.getElementById('qayt-card-sum').textContent = formatMoney(q.total_card);
    document.getElementById('qayt-vat-sum').textContent = formatMoney(q.total_vat);
    document.getElementById('qayt-items-count').textContent = q.unique_products.toLocaleString() + " ta";
    document.getElementById('qayt-receipts-badge').textContent = q.unique_receipts.toLocaleString() + " ta chek";
    if (data.qayt_file_name) {
      document.getElementById('qayt-file-label').textContent = "(" + data.qayt_file_name + ")";
    }
  } else {
    document.getElementById('qayt-total-sum').textContent = "0.00 so'm";
    document.getElementById('qayt-cash-sum').textContent = "0.00 so'm";
    document.getElementById('qayt-card-sum').textContent = "0.00 so'm";
    document.getElementById('qayt-vat-sum').textContent = "0.00 so'm";
    document.getElementById('qayt-items-count').textContent = "0 ta";
    document.getElementById('qayt-receipts-badge').textContent = "Qaytarish cheki yo'q";
  }

  // Mapping stats
  if (data.mapping_stats) {
    const ms = data.mapping_stats;
    document.getElementById('mapping-stats-banner').classList.remove('hidden');
    document.getElementById('stat-total-nom').textContent = ms.total_nomenklatura.toLocaleString() + " ta";
    document.getElementById('stat-matched').textContent = (s.matched_codes || 0).toLocaleString() + " ta";
    document.getElementById('stat-unmatched').textContent = (s.unmatched_codes || 0).toLocaleString() + " ta";
    document.getElementById('stat-nom-files').textContent = (data.nom_files || []).length + " ta (" + (data.nom_files || []).join(', ') + ")";
  }

  // Store data for search & filter
  allSotuvItems = (data.items_sotuv || []).map(item => ({ ...item, _type: 'sotuv' }));
  allQaytItems = (data.items_qayt || []).map(item => ({ ...item, _type: 'qayt' }));

  filterTable('all');

  // 1C yuborish tugmasini faollashtirish
  const sendBtn = document.getElementById('btn-send-1c');
  if (sendBtn) {
    sendBtn.disabled = false;
    sendBtn.style.opacity = '1';
    sendBtn.style.cursor = 'pointer';
  }
  // Sanani bugungi qiymat bilan to'ldirish
  const dateInput = document.getElementById('send-doc-date');
  if (dateInput && !dateInput.value) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.value = today;
  }

  // Smooth scroll
  document.getElementById('results-wrapper').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function sendTo1C() {
  const btn       = document.getElementById('btn-send-1c');
  const statusDiv = document.getElementById('send-1c-status');
  const dateVal   = document.getElementById('send-doc-date').value;
  const sendQayt  = document.getElementById('chk-send-qaytarish').checked;

  if (!dateVal) {
    _setStatus(statusDiv, 'error', '&#x26A0; Iltimos, hujjat sanasini tanlang!');
    return;
  }

  btn.disabled = true;
  btn.innerHTML = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> Yuborilmoqda...';
  _setStatus(statusDiv, 'info', '&#x23F3; 1C ga ulanmoqda...');

  try {
    // 1. Job boshlash — darhol qaytadi (timeout yo'q)
    const res = await fetch('/api/send_to_1c', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ doc_date: dateVal, send_sotuv: true, send_qaytarish: sendQayt })
    });
    const startData = await res.json();

    if (startData.error) {
      _setStatus(statusDiv, 'error', '&#x274C; ' + startData.error);
      _resetBtn(btn);
      return;
    }

    const jobId = startData.job_id;
    _setStatus(statusDiv, 'info',
      `&#x23F3; Jarayon boshlandi (Job: <code>${jobId}</code>)...<br>` +
      `&nbsp;&nbsp;Nomenklatura yuklanmoqda va hujjat tayyorlanmoqda...`);

    // 2. Polling — har 3 soniyada holat tekshirish
    let attempts = 0;
    const pollInterval = setInterval(async () => {
      attempts++;
      if (attempts > 120) { // 6 daqiqa max
        clearInterval(pollInterval);
        _setStatus(statusDiv, 'error', '&#x274C; Vaqt tugadi. Server logini tekshiring.');
        _resetBtn(btn);
        return;
      }
      try {
        const sRes = await fetch(`/api/send_to_1c/status/${jobId}`);
        const job  = await sRes.json();

        if (job.status === 'running') {
          _setStatus(statusDiv, 'info',
            `&#x23F3; ${job.log || 'Ishlanmoqda...'} <small style="opacity:0.6">(${attempts * 3}s)</small>`);

        } else if (job.status === 'done') {
          clearInterval(pollInterval);
          const s = job.results?.sotuv;
          const q = job.results?.qaytarish;
          let msg = '&#x2705; <b>Muvaffaqiyatli yuborildi!</b><br>';
          if (s?.number)  msg += `&nbsp;&nbsp;&#x2022; Sotuv: <b>${s.number}</b> — ${s.items_count || '?'} ta tovar<br>`;
          if (s?.ref_key) msg += `&nbsp;&nbsp;&nbsp;&nbsp;<small>Ref: ${s.ref_key.slice(0,12)}...</small><br>`;
          if (q?.number)  msg += `&nbsp;&nbsp;&#x2022; Qaytarish: <b>${q.number}</b><br>`;
          if (q?.info)    msg += `&nbsp;&nbsp;&#x2022; ${q.info}`;
          _setStatus(statusDiv, 'success', msg);
          showToast('1C ga muvaffaqiyatli yuborildi!', 'success');
          _resetBtn(btn);

        } else if (job.status === 'error') {
          clearInterval(pollInterval);
          const errMsg = (job.error || 'Noma\'lum xato').slice(0, 500);
          _setStatus(statusDiv, 'error',
            `&#x274C; <b>Xato:</b><br><code style="font-size:11px;word-break:break-all;">${errMsg}</code>`);
          showToast('Xato yuz berdi!', 'error');
          _resetBtn(btn);
        }
      } catch (_) { /* network xato — polling davom etadi */ }
    }, 3000);

  } catch (err) {
    _setStatus(statusDiv, 'error', '&#x274C; Server bilan aloqa uzildi: ' + err.message);
    _resetBtn(btn);
  }
}

function _setStatus(div, type, html) {
  div.style.display = 'block';
  const s = {
    info:    ['rgba(59,130,246,0.12)',  'rgba(59,130,246,0.25)',  '#93C5FD'],
    success: ['rgba(34,197,94,0.12)',   'rgba(34,197,94,0.3)',    '#86EFAC'],
    error:   ['rgba(239,68,68,0.12)',   'rgba(239,68,68,0.3)',    '#FCA5A5'],
  };
  const [bg, border, color] = s[type] || s.info;
  div.style.background = bg;
  div.style.border     = `1px solid ${border}`;
  div.style.color      = color;
  div.innerHTML        = html;
}

function _resetBtn(btn) {
  btn.disabled  = false;
  btn.innerHTML = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M22 2L11 13"/><path d="M22 2L15 22 11 13 2 9l20-7z"/></svg> 1C ga yuborish';
  btn.style.opacity = '1';
}

function switchMode(mode) {
  currentMode = mode;
  document.querySelectorAll('.mode-pill').forEach(pill => pill.classList.remove('active'));

  const pills = document.querySelectorAll('.mode-pill');
  const modes = ['nomenklaturno', 'ikpu', 'artikul', 'kod'];
  const idx = modes.indexOf(mode);
  if (idx >= 0 && pills[idx]) pills[idx].classList.add('active');

  renderSettingsGuide(mode);
  updateDownloadLinks(mode);
}

function updateDownloadLinks(mode) {
  const cfg = MODE_CONFIG[mode];
  if (!cfg) return;

  // Sotuv download
  document.getElementById('dl-sotuv-link').href = '/api/download/' + cfg.dlSotuv;
  document.getElementById('dl-sotuv-mode-label').textContent = cfg.label;
  document.getElementById('dl-sotuv-title').textContent = 'NET Sotuv Fayli (Qaytarishlar ayrilgan)';
  document.getElementById('dl-sotuv-desc').textContent = cfg.desc;

  // Qaytarish download
  document.getElementById('dl-qayt-link').href = '/api/download/' + cfg.dlQayt;
  document.getElementById('dl-qayt-title').textContent = 'Qaytarish — ' + cfg.label;
  document.getElementById('dl-qayt-desc').textContent = cfg.desc;
}

function renderSettingsGuide(mode) {
  const tbody = document.getElementById('guide-table-body');
  const badge = document.getElementById('guide-active-mode');
  tbody.innerHTML = '';

  const cfg = MODE_CONFIG[mode];
  badge.textContent = "Faol rejim: " + cfg.label;

  const rows = [
    {
      name: 'Код номенклатуры',
      num: 1,
      isSearch: mode === 'kod',
      desc: mode === 'kod' ? '🌟 Asosiy qidiruv kaliti (1C kodi bo\'yicha izlaydi)' : 'Excel faylidagi 1-ustun'
    },
    {
      name: 'Номенклатура',
      num: 2,
      isSearch: mode === 'nomenklaturno',
      desc: mode === 'nomenklaturno' ? '🌟 Asosiy qidiruv kaliti (Tovar nomi bo\'yicha izlaydi)' : 'Tovar / Xizmat nomi (Exceldagi 2-ustun)'
    },
    {
      name: 'Артикул',
      num: 3,
      isSearch: mode === 'artikul',
      desc: mode === 'artikul' ? '🌟 Asosiy qidiruv kaliti (Shtrixkod bo\'yicha izlaydi)' : 'Excel faylidagi 3-ustun'
    },
    {
      name: 'ИКПУ',
      num: 4,
      isSearch: mode === 'ikpu',
      desc: mode === 'ikpu' ? '🌟 Asosiy qidiruv kaliti (17 xonali MXIK kodi bo\'yicha)' : 'Excel faylidagi 4-ustun'
    },
    {
      name: 'Количество',
      num: 5,
      isSearch: false,
      desc: 'Sotilgan mahsulot miqdori (Exceldagi 5-ustun)'
    },
    {
      name: 'Цена',
      num: 6,
      isSearch: false,
      desc: 'Bir birlik narxi (QQS bilan)'
    },
    {
      name: 'Сумма',
      num: 7,
      isSearch: false,
      desc: 'Qatorning jami summasi (QQS bilan)'
    },
    {
      name: 'Ставка НДС',
      num: 8,
      isSearch: false,
      desc: '12% stavkasi (Exceldagi 8-ustun)'
    },
    {
      name: 'Сумма НДС',
      num: 9,
      isSearch: false,
      desc: '12% QQS summasi (Exceldagi 9-ustun)'
    }
  ];

  rows.forEach(r => {
    const tr = document.createElement('tr');
    if (r.isSearch) tr.classList.add('active-search-row');

    tr.innerHTML = `
      <td><strong>${r.name}</strong></td>
      <td>
        <span class="col-number-badge ${r.isSearch ? 'badge-highlight' : 'badge-normal'}">${r.num}</span>
      </td>
      <td>
        ${r.isSearch ? '<span class="badge-check-yes">✓ Qidiruv maydoni (Поле поиска)</span>' : '<span style="color:var(--text-dim);">—</span>'}
      </td>
      <td>${r.desc}</td>
    `;
    tbody.appendChild(tr);
  });
}

function copyCardSum() {
  if (!lastCardSumRaw) {
    showToast("Karta summasi topilmadi", "error");
    return;
  }
  const text = lastCardSumRaw.toFixed(2);
  navigator.clipboard.writeText(text).then(() => {
    showToast(`Karta summasi nusxalandi: ${text} so'm! 1C ga qo'yishingiz mumkin.`, "success");
  }).catch(() => {
    prompt("Nusxalash uchun Ctrl+C bosing:", text);
  });
}

/* Table Search and Filtering */
function filterTable(type) {
  currentFilter = type;
  document.querySelectorAll('.segment-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`seg-${type}`).classList.add('active');

  applySearchAndFilter();
}

function handleSearch() {
  currentPage = 1;
  applySearchAndFilter();
}

function applySearchAndFilter() {
  const query = document.getElementById('table-search').value.toLowerCase().trim();

  let pool = [];
  if (currentFilter === 'all') {
    pool = [...allSotuvItems, ...allQaytItems];
  } else if (currentFilter === 'sotuv') {
    pool = [...allSotuvItems];
  } else if (currentFilter === 'qayt') {
    pool = [...allQaytItems];
  }

  if (!query) {
    filteredItems = pool;
  } else {
    filteredItems = pool.filter(item => {
      const nm = (item.TovarNomi || '').toLowerCase();
      const bc = (item.Barcode || '').toLowerCase();
      const ik = (item.IKPU || '').toLowerCase();
      const kd = (item.Kod || '').toLowerCase();
      return nm.includes(query) || bc.includes(query) || ik.includes(query) || kd.includes(query);
    });
  }

  renderTablePage();
}

function renderTablePage() {
  const tbody = document.getElementById('data-grid-body');
  tbody.innerHTML = '';

  const total = filteredItems.length;
  const totalPages = Math.ceil(total / pageSize) || 1;
  if (currentPage > totalPages) currentPage = totalPages;

  const start = (currentPage - 1) * pageSize;
  const end = Math.min(start + pageSize, total);
  const pageRows = filteredItems.slice(start, end);

  if (pageRows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" class="text-center" style="padding: 28px; color: var(--text-dim);">Hech qanday tovar topilmadi.</td></tr>`;
    document.getElementById('pagination-info').textContent = `0 ta tovar`;
    document.getElementById('pagination-controls').innerHTML = '';
    return;
  }

  pageRows.forEach((r, idx) => {
    const tr = document.createElement('tr');
    const isReturn = r._type === 'qayt';
    const hasCode = r.Kod && r.Kod.trim() !== '';

    tr.innerHTML = `
      <td style="color: var(--text-dim);">${start + idx + 1}</td>
      <td class="mono-cell ${!hasCode ? 'code-missing' : ''}">${hasCode ? r.Kod : '⚠️ —'}</td>
      <td>
        <strong>${r.TovarNomi}</strong>
        ${isReturn ? '<span class="badge badge-rose" style="font-size:0.65rem; margin-left:6px;">Qaytarish</span>' : ''}
      </td>
      <td class="mono-cell">${r.Barcode || '-'}</td>
      <td class="mono-cell">${r.IKPU || '-'}</td>
      <td class="text-right"><strong>${Number(r.Miqdori).toLocaleString()}</strong></td>
      <td class="text-right">${Number(r.Narxi).toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
      <td class="text-right" style="color: ${isReturn ? '#fb7185' : '#60a5fa'}; font-weight:700;">
        ${Number(r.Summa).toLocaleString(undefined, {minimumFractionDigits: 2})}
      </td>
      <td class="text-center"><span class="badge-tag-vat">${r.StavkaNDS || '12%'}</span></td>
      <td class="text-right">${Number(r.QQS).toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
    `;
    tbody.appendChild(tr);
  });

  document.getElementById('pagination-info').textContent = `${total} ta tovardan ${start + 1}-${end} tasi ko'rsatilmoqda`;

  renderPaginationControls(totalPages);
}

function renderPaginationControls(totalPages) {
  const container = document.getElementById('pagination-controls');
  container.innerHTML = '';

  if (totalPages <= 1) return;

  const maxButtons = 5;
  let startP = Math.max(1, currentPage - 2);
  let endP = Math.min(totalPages, startP + maxButtons - 1);

  if (endP - startP < maxButtons - 1) {
    startP = Math.max(1, endP - maxButtons + 1);
  }

  if (currentPage > 1) {
    const prev = document.createElement('button');
    prev.className = 'page-btn';
    prev.textContent = '« Oldingi';
    prev.onclick = () => { currentPage--; renderTablePage(); };
    container.appendChild(prev);
  }

  for (let p = startP; p <= endP; p++) {
    const btn = document.createElement('button');
    btn.className = `page-btn ${p === currentPage ? 'active' : ''}`;
    btn.textContent = p;
    btn.onclick = () => { currentPage = p; renderTablePage(); };
    container.appendChild(btn);
  }

  if (currentPage < totalPages) {
    const next = document.createElement('button');
    next.className = 'page-btn';
    next.textContent = 'Keyingi »';
    next.onclick = () => { currentPage++; renderTablePage(); };
    container.appendChild(next);
  }
}

function resetAll() {
  location.reload();
}
