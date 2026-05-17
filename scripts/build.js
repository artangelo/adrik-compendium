#!/usr/bin/env node
/**
 * build.js
 * Reads data/*.json and generates dist/index.html
 * Usage: node scripts/build.js
 */

const fs = require('fs');
const path = require('path');

// Load data
const charPath = path.join(__dirname, '../data/character.json');
const worldPath = path.join(__dirname, '../data/world.json');
const sessionsPath = path.join(__dirname, '../data/sessions.json');
const templatePath = path.join(__dirname, '../templates/main.html');

if (!fs.existsSync(charPath)) {
  console.error('❌ data/character.json not found. Run: node scripts/parse-foundry.js <foundry-export.json>');
  process.exit(1);
}

const char = JSON.parse(fs.readFileSync(charPath, 'utf8'));
const world = fs.existsSync(worldPath) ? JSON.parse(fs.readFileSync(worldPath, 'utf8')) : {};
const sessions = fs.existsSync(sessionsPath) ? JSON.parse(fs.readFileSync(sessionsPath, 'utf8')) : null;

// Helper: format modifier
const fmt = (n) => n >= 0 ? `+${n}` : `${n}`;

// Generate warnings HTML
function warningsHtml(warnings) {
  if (!warnings || warnings.length === 0) return '';
  const icons = { error: '🔴', warn: '🟡', info: '🔵' };
  const colors = { error: 'var(--red)', warn: 'var(--amber)', info: 'var(--blue)' };
  return `
    <div class="warnings-bar">
      ${warnings.map(w => `<div class="warning-item" style="border-left-color:${colors[w.type]}">
        <span>${icons[w.type]}</span> <span>${w.msg}</span>
      </div>`).join('')}
    </div>`;
}

// Generate stat boxes HTML
function statsHtml(char) {
  const abs = char.abilities;
  const acNote = char.equipment?.some(e => e.name?.toLowerCase().includes('scale mail'))
    ? '⚠ 15' : '18';
  const hpMax = char.hp?.max ?? '?';
  const hpVal = char.hp?.value ?? '?';
  const inspiration = char.inspiration ? `<div class="stat-box wide" style="border-color:var(--gold-border2)"><span class="stat-val" style="color:var(--gold2)">✦</span><span class="stat-label">Inspiración</span></div>` : '';

  return `
    ${Object.entries(abs).map(([k, ab]) => `
      <div class="stat-box">
        <span class="stat-val">${ab.modStr}</span>
        <span class="stat-label">${ab.label} ${ab.value}</span>
      </div>`).join('')}
    <div class="stat-box wide"><span class="stat-val" style="${acNote.includes('⚠') ? 'color:var(--amber)' : ''}">${acNote}</span><span class="stat-label">Clase Armadura</span></div>
    <div class="stat-box wide"><span class="stat-val" style="color:#4A9A5A">${hpVal}/${hpMax}</span><span class="stat-label">HP</span></div>
    <div class="stat-box wide"><span class="stat-val">25 ft</span><span class="stat-label">Velocidad</span></div>
    <div class="stat-box wide"><span class="stat-val">${fmt(char.proficiencyBonus)}</span><span class="stat-label">Proficiencia</span></div>
    <div class="stat-box wide"><span class="stat-val">${char.spellSaveDC}</span><span class="stat-label">Spell Save DC</span></div>
    <div class="stat-box wide"><span class="stat-val">${fmt(char.spellAttackBonus)}</span><span class="stat-label">Ataque Hechizo</span></div>
    ${inspiration}
  `;
}

// Generate equipment HTML
function equipmentHtml(equipment) {
  if (!equipment || equipment.length === 0) return '<p style="color:var(--text2)">Sin equipo registrado</p>';
  return equipment.map(e => `
    <div class="card">
      <div class="card-title">${e.name}${e.quantity > 1 ? ` <span style="color:var(--text2);font-size:13px">x${e.quantity}</span>` : ''}</div>
    </div>`).join('');
}

// Generate sessions HTML
function sessionsHtml(sessions) {
  if (!sessions || !sessions.sessions?.length) return '<div class="card"><div class="card-sub">Sin sesiones sincronizadas. Ejecuta: <code>node scripts/sync-gdocs.js</code></div></div>';
  return sessions.sessions.slice(-3).reverse().map(s => `
    <div class="card">
      <div class="card-title">${s.title}${s.date ? ` <span style="color:var(--text2);font-size:12px">· ${s.date}</span>` : ''}</div>
      <div class="card-sub">${s.content.slice(0, 3).join(' ').substring(0, 300)}…</div>
    </div>`).join('');
}

// Read template
if (!fs.existsSync(templatePath)) {
  console.error('❌ templates/main.html not found');
  process.exit(1);
}

let html = fs.readFileSync(templatePath, 'utf8');

// Replace placeholders
const replacements = {
  '{{char.name}}': char.name,
  '{{char.class}}': char.class,
  '{{char.subclass}}': char.subclass,
  '{{char.level}}': char.level,
  '{{char.background}}': char.background,
  '{{char.race}}': char.race,
  '{{char.deity}}': char.deity,
  '{{char.lastUpdated}}': new Date(char.lastUpdated).toLocaleDateString('es-CL'),
  '{{warnings}}': warningsHtml(char.warnings),
  '{{stats}}': statsHtml(char),
  '{{equipment}}': equipmentHtml(char.equipment),
  '{{sessions}}': sessionsHtml(sessions),
  '{{spellSlots.total}}': Object.values(char.spellSlots)[0]?.max ?? 3,
};

for (const [placeholder, value] of Object.entries(replacements)) {
  html = html.replaceAll(placeholder, value ?? '');
}

// Write output
const outPath = path.join(__dirname, '../dist/index.html');
fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, html);

const stats = fs.statSync(outPath);
console.log(`✅ Built dist/index.html (${Math.round(stats.size / 1024)}KB)`);
console.log(`   Character: ${char.name} — Level ${char.level} ${char.class}`);
if (sessions?.sessions) console.log(`   Sessions: ${sessions.sessions.length} loaded`);
if (char.warnings?.length) console.log(`   ⚠️  ${char.warnings.length} warning(s) in character data`);
