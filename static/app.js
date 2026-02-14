const form = document.getElementById('searchForm');
const input = document.getElementById('searchInput');
const btn = document.getElementById('searchBtn');
const errorDiv = document.getElementById('errorMsg');
const results = document.getElementById('results');
const grid = document.getElementById('sourcesGrid');
const sidebar = document.getElementById('sidebar');
const navList = document.getElementById('navList');

const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const progressCount = document.getElementById('progressCount');

const SOURCE_ICONS = {
    'mctiers.com': '⚔️',
    'pvptiers.com': '🗡️',
    'centraltierlist.com': '🏆',
    'hypixel (plancke)': '🎮',
    'minecraftearth.org': '🌍',
    'jartexnetwork.com': '🔮',
    'playhive.com': '🐝',
    '6b6t.org': '💀',
    'pika-network.net': '⚡',
    'reafystats.com': '📊',
    'mcsrranked.com': '🏁',
    'mccisland': '🏝️',
    'manacube.com': '🧊',
};

let sourceBuffer = [];
let totalSources = 0;


form.addEventListener('submit', (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if (!q) return;

    errorDiv.classList.remove('active');
    results.classList.remove('active');
    sidebar.classList.remove('active');
    grid.innerHTML = '';
    navList.innerHTML = '';
    sourceBuffer = [];
    totalSources = 0;
    btn.disabled = true;

    progressContainer.classList.add('active');
    progressFill.style.width = '0%';
    progressText.textContent = 'Resolving player…';
    progressCount.textContent = '0 / ?';

    const evtSource = new EventSource(`/api/search?q=${encodeURIComponent(q)}`);

    evtSource.onmessage = (event) => {
        const msg = JSON.parse(event.data);

        switch (msg.type) {
            case 'error':
                evtSource.close();
                errorDiv.textContent = msg.message;
                errorDiv.classList.add('active');
                progressContainer.classList.remove('active');
                btn.disabled = false;
                break;

            case 'player':
                document.getElementById('playerName').textContent = msg.username;
                document.getElementById('playerUUID').textContent =
                    msg.uuid ? msg.uuid : (msg.xuid ? 'XUID: ' + msg.xuid : 'Bedrock Edition');
                const skinImg = document.getElementById('playerSkin');
                skinImg.onerror = () => { skinImg.src = 'https://mc-heads.net/body/MHF_Steve/right'; };
                skinImg.src = msg.skin_url;
                const badge = document.getElementById('platformBadge');
                badge.textContent = msg.platform === 'bedrock' ? '🪨 Bedrock' : '☕ Java';
                badge.className = 'platform-badge platform-' + msg.platform;
                results.classList.add('active');
                progressText.textContent = 'Fetching sources…';
                progressCount.textContent = '0 / ?';
                break;

            case 'source':
                totalSources = msg.total;
                sourceBuffer.push({ label: msg.label, data: msg.data, error: msg.error });
                progressCount.textContent = `${msg.fetched} / ${msg.total}`;
                progressFill.style.width = `${(msg.fetched / msg.total) * 100}%`;
                progressText.textContent = msg.fetched < msg.total
                    ? 'Fetching sources…'
                    : 'Done!';
                break;

            case 'done':
                evtSource.close();
                btn.disabled = false;
                renderAllSources();
                setTimeout(() => progressContainer.classList.remove('active'), 800);
                break;
        }
    };

    evtSource.onerror = () => {
        evtSource.close();
        errorDiv.textContent = 'Connection lost';
        errorDiv.classList.add('active');
        progressContainer.classList.remove('active');
        btn.disabled = false;
    };
});


function renderAllSources() {
    const ok = sourceBuffer.filter(s => !s.error);
    const err = sourceBuffer.filter(s => s.error);
    const sorted = [...ok, ...err];

    grid.innerHTML = '';
    navList.innerHTML = '';

    sorted.forEach((src, i) => {
        const id = `source-${i}`;
        appendSourceCard(src.label, src.data, src.error, id);
        appendNavItem(src.label, src.error, id);
    });

    sidebar.classList.add('active');
    setupScrollSpy();
}


function appendSourceCard(label, data, error, id) {
    const card = document.createElement('div');
    card.className = 'source-card open';
    card.id = id;

    const icon = SOURCE_ICONS[label] || '📊';
    const badge = error
        ? '<span class="source-badge badge-err">Error</span>'
        : '<span class="source-badge badge-ok">OK</span>';

    const bodyHTML = error
        ? renderError(error)
        : renderSourceData(data, label);

    card.innerHTML = `
        <div class="source-header">
            <span class="source-name">${icon} ${esc(label)} ${badge}</span>
            <span class="toggle-arrow">▼</span>
        </div>
        <div class="source-body">
            <div class="source-content">${bodyHTML}</div>
        </div>
    `;

    card.querySelector('.source-header').addEventListener('click', () => {
        card.classList.toggle('open');
    });

    grid.appendChild(card);
}


function appendNavItem(label, error, targetId) {
    const icon = SOURCE_ICONS[label] || '📊';
    const li = document.createElement('li');
    li.className = 'nav-item' + (error ? ' nav-item--err' : '');
    li.dataset.target = targetId;

    li.innerHTML = `
        <a href="#${targetId}" class="nav-link">
            <span class="nav-icon">${icon}</span>
            <span class="nav-label">${esc(label)}</span>
            ${error ? '<span class="nav-status nav-status--err">✘</span>' : '<span class="nav-status nav-status--ok">✔</span>'}
        </a>
    `;

    li.querySelector('a').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById(targetId).scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    navList.appendChild(li);
}


function setupScrollSpy() {
    const cards = grid.querySelectorAll('.source-card');
    const items = navList.querySelectorAll('.nav-item');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                items.forEach(it => it.classList.remove('active'));
                const match = navList.querySelector(`[data-target="${entry.target.id}"]`);
                if (match) match.classList.add('active');
            }
        });
    }, { rootMargin: '-10% 0px -70% 0px', threshold: 0 });

    cards.forEach(c => observer.observe(c));
}


function renderError(msg) {
    return `<div class="source-error">⚠ ${esc(msg)}</div>`;
}

function renderSourceData(data, sourceName) {
    if (sourceName === 'mctiers.com') return renderMcTiers(data);
    if (sourceName === 'pvptiers.com') return renderMcTiers(data);
    if (sourceName === 'hypixel (plancke)') return renderHypixel(data);
    if (sourceName === 'playhive.com') return renderHive(data);
    if (sourceName === '6b6t.org') return render6b6t(data);
    return renderObject(data);
}


function render6b6t(data) {
    let html = '';
    const meta = {};
    for (const [k, v] of Object.entries(data)) {
        if (k !== 'player_stats' && v !== null && typeof v !== 'object') meta[k] = v;
    }
    if (Object.keys(meta).length) html += renderKVSection('Player', meta);

    if (data.player_stats && typeof data.player_stats === 'object') {
        html += `<div class="data-section"><div class="section-title">Stats</div>`;
        html += '<div class="data-table-wrap"><table class="data-table">';
        html += '<thead><tr><th>Stat</th><th>7 days</th><th>30 days</th><th>Total</th></tr></thead><tbody>';
        for (const [name, vals] of Object.entries(data.player_stats)) {
            html += `<tr><td>${esc(name)}</td><td>${esc(vals['7d'] || '0')}</td><td>${esc(vals['30d'] || '0')}</td><td>${esc(vals.total || '0')}</td></tr>`;
        }
        html += '</tbody></table></div></div>';
    }

    return html || '<span style="color:var(--text-dim)">No data</span>';
}


function renderHive(data) {
    let html = '';
    const SKIP_KEYS = new Set([
        'hub_title_unlocked', 'avatar_unlocked', 'costume_unlocked',
        'hat_unlocked', 'cosmetics.backbling', 'paid_ranks', 'pets',
        'mounts', 'friends', 'avatar_count', 'costume_count', 'hat_count',
        'backbling_count', 'friend_count', 'quest_count', 'equipped_avatar',
        'equipped_hub_title',
    ]);
    const GAME_KEYS = new Set([
        'hide', 'dr', 'wars', 'murder', 'sg', 'sky', 'ctf', 'drop',
        'ground', 'build', 'party', 'bridge', 'grav', 'bed', 'parkour',
        'sky-classic', 'sky-kits',
    ]);

    if (data.main) {
        const profile = {};
        for (const [k, v] of Object.entries(data.main)) {
            if (SKIP_KEYS.has(k) || GAME_KEYS.has(k)) continue;
            if (v !== null && typeof v !== 'object') profile[k] = v;
        }
        if (Object.keys(profile).length) html += renderKVSection('Profile', profile);
    }

    html += `<div class="data-section"><div class="section-title">Games</div>`;
    for (const [key, gdata] of Object.entries(data)) {
        if (key === 'main' || !GAME_KEYS.has(key) || typeof gdata !== 'object') continue;
        const stats = {};
        for (const [k, v] of Object.entries(gdata)) {
            if (k === 'UUID' || k === 'parkours' || k === 'selected_kit') continue;
            if (v !== null && typeof v !== 'object') {
                if (k === 'first_played' && typeof v === 'number' && v > 1e12) {
                    stats[k] = new Date(v).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
                } else {
                    stats[k] = v;
                }
            }
        }
        if (Object.keys(stats).length) {
            html += renderGameBlock(key, { stats });
        }
    }
    html += `</div>`;

    return html || '<span style="color:var(--text-dim)">No data</span>';
}


function renderMcTiers(data) {
    let html = '';

    const top = {};
    for (const [k, v] of Object.entries(data)) {
        if (k === 'rankings' || k === 'badges' || k === 'tests') continue;
        if (v !== null && typeof v !== 'object') top[k] = v;
    }
    if (Object.keys(top).length) html += renderKVSection('Player', top);

    if (data.rankings && typeof data.rankings === 'object') {
        html += `<div class="data-section"><div class="section-title">Rankings</div>`;
        for (const [mode, info] of Object.entries(data.rankings)) {
            html += renderRankingCard(mode, info);
        }
        html += `</div>`;
    }

    if (data.badges && data.badges.length) {
        html += renderKVSection('Badges', Object.fromEntries(data.badges.map((b, i) => [i, b])));
    }

    if (data.tests && data.tests.length) {
        html += `<div class="data-section"><div class="section-title">Tests</div>${renderArrayAsTable(data.tests)}</div>`;
    }

    return html || '<span style="color:var(--text-dim)">No data</span>';
}

function renderRankingCard(mode, info) {
    const tierLabel = info.tier != null ? `T${info.tier}` : '?';
    const peakLabel = info.peak_tier != null ? `T${info.peak_tier}` : '?';
    const retired = info.retired ? '🔴 Retired' : '🟢 Active';
    const attained = info.attained ? new Date(info.attained * 1000).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : '';

    return `
        <div class="ranking-card">
            <span class="ranking-mode">${esc(mode)}</span>
            <span class="ranking-tier">${tierLabel}</span>
            <div class="ranking-details">
                <span><span class="label">pos</span> #${info.pos ?? '?'}</span>
                <span><span class="label">peak</span> ${peakLabel} #${info.peak_pos ?? '?'}</span>
                <span>${retired}</span>
                ${attained ? `<span><span class="label">attained</span> ${attained}</span>` : ''}
            </div>
        </div>
    `;
}


function renderHypixel(data) {
    let html = '';
    if (data.player_info) html += renderKVSection('Player Info', data.player_info);
    if (data.status) html += renderKVSection('Status', typeof data.status === 'string' ? { Status: data.status } : data.status);
    if (data.socials) html += renderKVSection('Socials', data.socials);
    if (data.games) {
        html += `<div class="data-section"><div class="section-title">Games</div>`;
        for (const [name, gd] of Object.entries(data.games)) html += renderGameBlock(name, gd);
        html += `</div>`;
    }
    return html || '<span style="color:var(--text-dim)">No data</span>';
}

function renderGameBlock(name, gameData) {
    let inner = '';
    if (gameData.stats) inner += renderKVGrid(gameData.stats);
    if (gameData.tables) {
        for (const tbl of gameData.tables) inner += renderTable(tbl);
    }
    return `
        <div class="game-block">
            <div class="game-title" onclick="this.parentElement.classList.toggle('open')">
                <span>🎯 ${esc(name)}</span>
                <span class="game-chevron">▼</span>
            </div>
            <div class="game-inner"><div class="game-body">${inner}</div></div>
        </div>
    `;
}


function renderObject(obj) {
    let html = '';
    const flat = {}, nested = {}, arrays = {};

    for (const [k, v] of Object.entries(obj)) {
        if (v && typeof v === 'object' && !Array.isArray(v)) nested[k] = v;
        else if (Array.isArray(v)) arrays[k] = v;
        else flat[k] = v;
    }

    if (Object.keys(flat).length) html += renderKVGrid(flat);
    for (const [k, v] of Object.entries(nested)) html += renderKVSection(k, v);
    for (const [k, arr] of Object.entries(arrays)) {
        if (arr.length && typeof arr[0] === 'object') {
            html += `<div class="data-section"><div class="section-title">${esc(k)}</div>${renderArrayAsTable(arr)}</div>`;
        } else {
            html += renderKVSection(k, Object.fromEntries(arr.map((v, i) => [i, v])));
        }
    }
    return html || '<span style="color:var(--text-dim)">No data</span>';
}


function renderKVSection(title, obj) {
    if (typeof obj !== 'object' || obj === null) {
        return `<div class="data-section"><div class="section-title">${esc(title)}</div><div class="kv-grid"><div class="kv-row"><span class="kv-val">${esc(String(obj))}</span></div></div></div>`;
    }
    const flat = {}, nested = {};
    for (const [k, v] of Object.entries(obj)) {
        if (v && typeof v === 'object') nested[k] = v; else flat[k] = v;
    }
    let html = `<div class="data-section"><div class="section-title">${esc(title)}</div>`;
    if (Object.keys(flat).length) html += renderKVGrid(flat);
    for (const [k, v] of Object.entries(nested)) {
        if (Array.isArray(v) && v.length && typeof v[0] === 'object') {
            html += `<div style="margin-top:8px"><div class="section-title" style="font-size:0.75rem">${esc(k)}</div>${renderArrayAsTable(v)}</div>`;
        } else if (!Array.isArray(v)) {
            html += renderKVGrid(v);
        }
    }
    html += `</div>`;
    return html;
}

function renderKVGrid(obj) {
    let html = '<div class="kv-grid">';
    for (const [k, v] of Object.entries(obj)) {
        html += `<div class="kv-row"><span class="kv-key">${esc(String(k))}</span><span class="kv-val">${esc(String(v))}</span></div>`;
    }
    return html + '</div>';
}

function renderTable(tbl) {
    if (!tbl.rows || !tbl.rows.length) return '';
    let html = '<div class="data-table-wrap"><table class="data-table">';
    if (tbl.headers) {
        html += '<thead><tr>';
        for (const h of tbl.headers) html += `<th>${esc(h)}</th>`;
        html += '</tr></thead>';
    }
    html += '<tbody>';
    for (const row of tbl.rows) {
        html += '<tr>';
        if (Array.isArray(row)) {
            for (const c of row) html += `<td>${esc(c)}</td>`;
        } else {
            for (const h of (tbl.headers || Object.keys(row))) html += `<td>${esc(String(row[h] ?? ''))}</td>`;
        }
        html += '</tr>';
    }
    return html + '</tbody></table></div>';
}

function renderArrayAsTable(arr) {
    if (!arr.length) return '';
    const keys = [...new Set(arr.flatMap(o => Object.keys(o)))];
    let html = '<div class="data-table-wrap"><table class="data-table"><thead><tr>';
    for (const k of keys) html += `<th>${esc(k)}</th>`;
    html += '</tr></thead><tbody>';
    for (const row of arr) {
        html += '<tr>';
        for (const k of keys) html += `<td>${esc(String(row[k] ?? ''))}</td>`;
        html += '</tr>';
    }
    return html + '</tbody></table></div>';
}


function esc(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
