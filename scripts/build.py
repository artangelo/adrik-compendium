#!/usr/bin/env python3
"""
build.py — Genera el sitio multi-jugador del compendium

Outputs:
  dist/index.html           Party Hub
  dist/adrik/index.html     Página de Adrik (completa, pre-renderizada)
  dist/{slug}/index.html    Páginas stub para los otros 5 personajes
"""

import json
import os
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(path, default=None):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default

def fmt(n):
    return f"+{n}" if n >= 0 else str(n)

# ── Load data ──────────────────────────────────────────────────────────────────
char_path     = os.path.join(BASE, "data", "character.json")
world_path    = os.path.join(BASE, "data", "world.json")
sessions_path = os.path.join(BASE, "data", "sessions.json")
char_tmpl     = os.path.join(BASE, "templates", "character.html")

if not os.path.exists(char_path):
    print("❌ data/character.json not found. Run:")
    print("   python3 scripts/parse-foundry.py <foundry-export.json>")
    sys.exit(1)

char         = load(char_path)
world        = load(world_path, {})
sessions_data = load(sessions_path)

with open(char_tmpl, encoding="utf-8") as f:
    CHAR_TMPL = f.read()

# ── Party definitions ──────────────────────────────────────────────────────────
PARTY = [
    {
        "slug": "adrik", "name": "Adrik Frostbeard",
        "class_str": "Clérigo · Dominio Crepúsculo", "race_str": "Enano de Colina",
        "color": "#C9963A", "border": "rgba(201,150,58,0.55)", "bg": "rgba(201,150,58,0.12)",
        "initial": "A", "player": "Luis", "is_player": True,
    },
    {
        "slug": "draxus", "name": "Draxus",
        "class_str": "Fighter", "race_str": "Dragonborn Plateado",
        "color": "#94A3B8", "border": "rgba(148,163,184,0.5)", "bg": "rgba(148,163,184,0.1)",
        "initial": "D", "player": None, "is_player": False,
    },
    {
        "slug": "sven", "name": "Sven",
        "class_str": "Rogue", "race_str": "Elfo",
        "color": "#38BDF8", "border": "rgba(56,189,248,0.5)", "bg": "rgba(56,189,248,0.1)",
        "initial": "S", "player": None, "is_player": False,
    },
    {
        "slug": "teska", "name": "Teska",
        "class_str": "Bardo", "race_str": "Tiefling",
        "color": "#A78BFA", "border": "rgba(167,139,250,0.5)", "bg": "rgba(167,139,250,0.1)",
        "initial": "T", "player": None, "is_player": False,
    },
    {
        "slug": "elian", "name": "Elian",
        "class_str": "Mago", "race_str": "Humano",
        "color": "#60A5FA", "border": "rgba(96,165,250,0.5)", "bg": "rgba(96,165,250,0.1)",
        "initial": "E", "player": None, "is_player": False,
    },
    {
        "slug": "yankavic", "name": "Yankavic",
        "class_str": "Paladín", "race_str": "Semielfo",
        "color": "#34D399", "border": "rgba(52,211,153,0.5)", "bg": "rgba(52,211,153,0.1)",
        "initial": "Y", "player": None, "is_player": False,
    },
]

PARTY_BY_SLUG = {m["slug"]: m for m in PARTY}

# ── Credentials ────────────────────────────────────────────────────────────────
CREDENTIALS = {
    "adrik":    {"password": "selune",   "admin": True},
    "draxus":   {"password": "yunque",   "admin": False},
    "sven":     {"password": "escarcha", "admin": False},
    "teska":    {"password": "arpistas", "admin": False},
    "elian":    {"password": "elfico",   "admin": False},
    "yankavic": {"password": "tormenta", "admin": False},
}

# ── Auth script (injected in every character page) ────────────────────────────
def auth_script(slug):
    creds = json.dumps({k: {"p": v["password"], "a": v["admin"]} for k, v in CREDENTIALS.items()})
    m = PARTY_BY_SLUG.get(slug, {})
    char_color = m.get("color", "var(--gold)")
    return f"""<script>
// ── Session & Analytics ────────────────────────────────────────────────────
const _SK = 'icewind_session';
const _AK = 'icewind_analytics';
const _CREDS = {creds};

function _getSession() {{
  try {{ return JSON.parse(localStorage.getItem(_SK)); }} catch {{ return null; }}
}}
function logout() {{
  localStorage.removeItem(_SK);
  location.href = '../index.html';
}}
function _track(type, data) {{
  try {{
    const ev = JSON.parse(localStorage.getItem(_AK) || '[]');
    ev.push({{ t: type, d: data, ts: Date.now() }});
    if (ev.length > 1000) ev.splice(0, 200);
    localStorage.setItem(_AK, JSON.stringify(ev));
  }} catch(e) {{}}
}}
function _trackUpload(slug) {{
  _track('upload', {{ slug }});
  localStorage.setItem('last_upload_' + slug, Date.now());
  localStorage.setItem('upload_char_' + slug, '1');
}}

// ── Auth check ──────────────────────────────────────────────────────────────
(function() {{
  const sess = _getSession();
  if (!sess) {{ location.replace('../index.html'); return; }}

  // Track visit
  _track('visit', {{ slug: '{slug}', ts: Date.now() }});
  localStorage.setItem('last_visit_{slug}', Date.now());

  // User indicator in header
  const hubLink = document.querySelector('.hub-link');
  if (hubLink) {{
    hubLink.insertAdjacentHTML('afterend',
      '<span id="session-indicator" style="font-size:11px;color:var(--text3);margin-left:14px">' +
      '<span style="color:{char_color}">' + sess.slug + '</span>' +
      (sess.admin ? ' <span style="color:var(--gold);opacity:0.7;font-size:10px">★ admin</span>' : '') +
      ' &nbsp;·&nbsp; <a href="#" onclick="logout();return false" ' +
      'style="color:var(--text3);text-decoration:none;border-bottom:1px solid var(--surface3)">salir</a>' +
      '</span>'
    );
  }}

  // Apply tab restrictions immediately
  applyAuthRestrictions();
}})();
</script>"""

# ── Helpers ────────────────────────────────────────────────────────────────────
CLASS_ES = {
    "Cleric": "Clérigo", "Fighter": "Guerrero", "Rogue": "Pícaro",
    "Wizard": "Mago", "Paladin": "Paladín", "Bard": "Bardo",
    "Ranger": "Explorador", "Sorcerer": "Hechicero", "Warlock": "Brujo",
    "Barbarian": "Bárbaro", "Druid": "Druida", "Monk": "Monje",
}
SUBCLASS_ES = {
    "Twilight Domain": "Dominio Crepúsculo", "Life Domain": "Dominio de la Vida",
    "Light Domain": "Dominio de la Luz", "War Domain": "Dominio de la Guerra",
}
RACE_ES = {
    "Dwarf (Hill)": "Enano de Colina", "Dwarf (Mountain)": "Enano de Montaña",
    "Elf (High)": "Elfo de la Alta Magia", "Elf (Wood)": "Elfo del Bosque",
    "Tiefling": "Tiefling", "Human": "Humano", "Halfling": "Mediano",
    "Half-Elf": "Semielfo", "Half-Orc": "Semiorco",
}

def char_subtitle(c):
    cls  = CLASS_ES.get(c.get("class", ""), c.get("class", ""))
    sub  = SUBCLASS_ES.get(c.get("subclass", ""), c.get("subclass", ""))
    race = RACE_ES.get(c.get("race", ""), c.get("race", ""))
    lvl  = c.get("level", 1)
    bg   = c.get("background", "")
    deity = c.get("deity", "")
    return f'{cls} · <span>{sub}</span> · Nivel {lvl} · {race} · {bg} · <span>{deity}</span>'

def last_updated(c):
    ts = c.get("lastUpdated", "")
    if not ts:
        return datetime.now().strftime("%-d %b %Y")
    try:
        return datetime.fromisoformat(ts).strftime("%-d %b %Y")
    except Exception:
        return ts[:10]

# ── Adrik header: warnings + stat boxes + slot tracker ────────────────────────
def warnings_html(warnings):
    if not warnings:
        return ""
    icons  = {"error": "🔴", "warn": "🟡", "info": "🔵"}
    items = "\n".join(
        f'<div style="display:flex;gap:8px;align-items:flex-start;padding:5px 0;font-size:13px;color:var(--text2)">'
        f'<span>{icons.get(w["type"],"🔵")}</span><span>{w["msg"]}</span></div>'
        for w in warnings
    )
    return (
        f'<div style="margin:14px 0 0;padding:12px 16px;background:rgba(201,80,30,0.1);'
        f'border:1px solid rgba(201,80,30,0.3);border-radius:8px;line-height:1.7">'
        f'<strong style="color:var(--amber);font-size:13px">⚠ Alertas de configuración Foundry:</strong>'
        f'{items}</div>'
    )

def stat_boxes_html(c):
    abs_data = c.get("abilities", {})
    order = [("str","FUE"),("dex","DES"),("con","CON"),("int","INT"),("wis","SAB"),("cha","CAR")]
    boxes = []
    for key, label in order:
        ab = abs_data.get(key, {})
        val = ab.get("value", 10)
        mod_str = ab.get("modStr", "+0")
        boxes.append(
            f'<div class="stat-box"><span class="stat-val">{mod_str}</span>'
            f'<span class="stat-label">{label} {val}</span></div>'
        )
    hp = c.get("hp", {})
    hp_max = hp.get("max") or hp.get("override") or "?"
    hp_val = hp.get("value", "?")
    hp_color = "#4A9A5A" if hp_max != "?" else "var(--amber)"
    hp_warn  = " ⚠" if hp_max == "?" else ""
    equip = c.get("equipment", [])
    has_scale = any("scale mail" in e.get("name","").lower() for e in equip)
    ac_val   = "15 ⚠" if has_scale else "18"
    ac_color = "color:var(--amber)" if has_scale else ""
    ac_title = ' title="Scale Mail+Escudo=15. Cambia a Chain Mail para CA 18."' if has_scale else ""
    boxes.append(
        f'<div class="stat-box wide"{ac_title}>'
        f'<span class="stat-val" style="{ac_color}">{ac_val}</span>'
        f'<span class="stat-label">Clase Armadura</span></div>'
    )
    boxes.append(
        f'<div class="stat-box wide">'
        f'<span class="stat-val" style="color:{hp_color}">{hp_val}/{hp_max}{hp_warn}</span>'
        f'<span class="stat-label">HP</span></div>'
    )
    boxes.append('<div class="stat-box wide"><span class="stat-val">25 ft</span><span class="stat-label">Velocidad</span></div>')
    prof = c.get("proficiencyBonus", 2)
    boxes.append(
        f'<div class="stat-box wide"><span class="stat-val">{fmt(prof)}</span>'
        f'<span class="stat-label">Proficiencia</span></div>'
    )
    dc  = c.get("spellSaveDC", 15)
    atk = c.get("spellAttackBonus", 5)
    boxes.append(
        f'<div class="stat-box wide"><span class="stat-val">{dc}</span>'
        f'<span class="stat-label">Spell Save DC</span></div>'
    )
    boxes.append(
        f'<div class="stat-box wide"><span class="stat-val">{fmt(atk)}</span>'
        f'<span class="stat-label">Ataque Hechizo</span></div>'
    )
    if c.get("inspiration"):
        boxes.append(
            '<div class="stat-box wide" style="border-color:var(--gold-border2);background:rgba(201,150,58,0.08)">'
            '<span class="stat-val" style="color:var(--gold2)">✦</span>'
            '<span class="stat-label">Inspiración</span></div>'
        )
    return "\n    ".join(boxes)

def adrik_header_content(c):
    abs_html = stat_boxes_html(c)
    slots = c.get("spellSlots", {})
    total = slots.get("1", {}).get("max", 3) if slots else 3
    pips = "\n      ".join(
        f'<button class="slot-pip" onclick="toggleSlot({i})">●</button>'
        for i in range(total)
    )
    return f'''
  <div class="stat-grid">
    {abs_html}
  </div>
  <div class="slots-area">
    <span class="slots-label">Spell Slots Niv. 1</span>
    <div class="slots-pips" id="slotPips">{pips}</div>
    <button class="slots-reset" onclick="resetSlots()">↺ Resetear</button>
    <span id="slotsCount" style="font-size:13px;color:var(--text2)">{total} / {total} disponibles</span>
    <span style="font-size:13px;color:var(--text2)">·</span>
    <span style="font-size:13px;color:var(--text2)">Channel Divinity: <button onclick="toggleCD()" id="cdBtn" style="background:var(--teal-bg);color:var(--teal);border:1px solid rgba(42,157,127,0.3);border-radius:20px;padding:3px 10px;cursor:pointer;font-size:12px;font-family:\'Source Sans 3\',sans-serif">1 uso disponible</button></span>
  </div>'''

# ── Adrik personal tab panels ──────────────────────────────────────────────────
ADRIK_PERSONAL_BUTTONS = """\
<button class="tab-btn tab-personal active" onclick="switchTab('combate',this)">⚔ Combate</button>
<button class="tab-btn tab-personal" onclick="switchTab('hechizos',this)">✦ Hechizos</button>
<button class="tab-btn tab-personal" onclick="switchTab('habilidades',this)">◈ Habilidades</button>"""

ADRIK_PERSONAL_PANELS = """\
<!-- TAB: COMBATE -->
<div id="tab-combate" class="tab-panel active">
  <div class="section-label">Prioridades de combate</div>
  <ul class="priority-list">
    <li class="priority-item">
      <div class="priority-num amber">1</div>
      <div class="priority-body">
        <div class="priority-title">Bless — siempre el primer turno</div>
        <div class="priority-dw">"Baraz azamar" · Slot nivel 1 · Concentración</div>
        <div class="priority-note">Cubre a los 3 aliados que más atacan (Draxus, Sven, Yankavic). +1d4 a ataques y saving throws. Dura 1 minuto. Prioridad absoluta antes de cualquier otra acción.</div>
      </div>
    </li>
    <li class="priority-item">
      <div class="priority-num purple">2</div>
      <div class="priority-body">
        <div class="priority-title">Twilight Sanctuary — combate prolongado o daño en área</div>
        <div class="priority-dw">"Sel kharak dur" · Channel Divinity · Sin spell slot</div>
        <div class="priority-note">Esfera de 30 pies centrada en ti, se mueve contigo. Al final de cada turno dentro: 1d6+2 HP temporales O elimina miedo/encantamiento. No gasta slot.</div>
      </div>
    </li>
    <li class="priority-item">
      <div class="priority-num teal">3</div>
      <div class="priority-body">
        <div class="priority-title">Healing Word — si alguien cae a 0 HP</div>
        <div class="priority-dw">"Kharak azamar" · Slot nivel 1 · Acción bonus</div>
        <div class="priority-note">Acción bonus. Rango 60 pies. Levantas a un aliado inconsciente sin sacrificar tu acción principal. Siempre superior a Cure Wounds en economía de acción.</div>
      </div>
    </li>
    <li class="priority-item">
      <div class="priority-num gray">4</div>
      <div class="priority-body">
        <div class="priority-title">Command — control sin concentración</div>
        <div class="priority-dw">"Karak dûm" · Slot nivel 1 · Sin concentración</div>
        <div class="priority-note">Fuerza a un enemigo a perder su acción (huye, cae, detente). No compite con Bless en concentración. Úsalo cuando el combate lo requiera.</div>
      </div>
    </li>
    <li class="priority-item">
      <div class="priority-num coral">5</div>
      <div class="priority-body">
        <div class="priority-title">Guiding Bolt — daño ofensivo fuerte</div>
        <div class="priority-dw">"Nar khalad sel" · Slot nivel 1</div>
        <div class="priority-note">4d6 radiante + ventaja al siguiente ataque contra ese objetivo. Úsalo cuando Bless ya está activo y todos están en pie.</div>
      </div>
    </li>
    <li class="priority-item">
      <div class="priority-num gray">6</div>
      <div class="priority-body">
        <div class="priority-title">Warhammer / Toll the Dead — ataque básico</div>
        <div class="priority-dw">"Kharak dûm" para Toll the Dead · Cantrip, sin slot</div>
        <div class="priority-note">Toll the Dead NO usa spell slot — es cantrip. D8 normal, d12 si el objetivo ya está herido (SAB save). Warhammer en melee si hay flanqueo activo.</div>
      </div>
    </li>
  </ul>
  <div class="section-label">Antes del combate</div>
  <div class="grid-2">
    <div class="card purple">
      <div class="card-title">Vigilant Blessing</div>
      <div class="card-sub">Como acción, da ventaja en la próxima iniciativa a un aliado. Úsalo en el Fighter o el Rogue antes de combates que anticipas. Se consume al tirar iniciativa.</div>
    </div>
    <div class="card teal">
      <div class="card-title">Eyes of Night (compartido)</div>
      <div class="card-sub">Como acción, comparte darkvision 300 pies con 3 aliados por 1 hora. Actívalo antes de entrar a zonas oscuras. 1 uso por descanso largo.</div>
    </div>
  </div>
  <div class="section-label">Skills de exploración</div>
  <div class="skill-grid">
    <div class="skill-item"><span class="skill-name">Survival</span><span class="skill-val">+5</span></div>
    <div class="skill-item"><span class="skill-name">Insight</span><span class="skill-val">+5</span></div>
    <div class="skill-item"><span class="skill-name">Athletics</span><span class="skill-val">+3</span></div>
    <div class="skill-item"><span class="skill-name">Religion</span><span class="skill-val">+2</span></div>
  </div>
  <div class="card" style="margin-top:10px">
    <div class="card-sub"><strong style="color:var(--text)">Saving throws con proficiencia:</strong> Sabiduría +5, Carisma +3. Concentración: CON save DC 10 o mitad del daño. Sin proficiencia en CON — posicionate detrás del frontline para no romper Bless.</div>
  </div>
</div>

<!-- TAB: HECHIZOS -->
<div id="tab-hechizos" class="tab-panel">
  <div class="section-label">Cantrips — nunca usan spell slot</div>
  <div class="spell-grid">
    <div class="spell-card cantrip">
      <div class="spell-name">Toll the Dead</div>
      <div class="spell-dw">"Kharak dûm"</div>
      <span class="badge teal spell-tag">Daño · Cantrip</span>
      <div class="spell-desc">SAB save. 1d8 (1d12 si el objetivo ya está herido). Tu daño a distancia principal. Sin costo.</div>
    </div>
    <div class="spell-card cantrip">
      <div class="spell-name">Guidance</div>
      <div class="spell-dw">"Sel'ur"</div>
      <span class="badge teal spell-tag">Utilidad · Cantrip</span>
      <div class="spell-desc">Acción bonus. +1d4 al próximo check de un aliado. Úsalo siempre que puedas antes de checks importantes.</div>
    </div>
    <div class="spell-card cantrip">
      <div class="spell-name">Sacred Flame</div>
      <div class="spell-dw">"Nar sel"</div>
      <span class="badge teal spell-tag">Daño · Cantrip</span>
      <div class="spell-desc">DEX save. Radiante. Ignora cobertura. Backup cuando Toll the Dead no aplica.</div>
    </div>
  </div>
  <div class="section-label">Dominio Crepúsculo — siempre preparados, no cuentan contra el límite</div>
  <div class="spell-grid">
    <div class="spell-card domain">
      <div class="spell-name">Sleep</div>
      <div class="spell-dw">"Khadûm"</div>
      <span class="badge purple spell-tag">Control · 1 slot</span>
      <div class="spell-desc">Afecta criaturas empezando por las de menos HP. Muy útil vs múltiples enemigos débiles.</div>
    </div>
    <div class="spell-card domain">
      <div class="spell-name">Faerie Fire</div>
      <div class="spell-dw">"Sel nar"</div>
      <span class="badge purple spell-tag">Control · 1 slot · Concentración</span>
      <div class="spell-desc">Ventaja en todos los ataques vs criaturas afectadas. No puedes tenerlo activo junto a Bless — elige uno.</div>
    </div>
  </div>
  <div class="section-label">Hechizos preparados — usan spell slot de nivel 1</div>
  <div class="spell-grid">
    <div class="spell-card prepared">
      <div class="spell-name">Bless ⭐</div>
      <div class="spell-dw">"Baraz azamar"</div>
      <span class="badge amber spell-tag">Soporte · 1 slot · Concentración</span>
      <div class="spell-desc">PRIORIDAD 1. +1d4 ataques y saves a 3 aliados. 1 minuto. Cambia el combate completo.</div>
    </div>
    <div class="spell-card prepared">
      <div class="spell-name">Healing Word</div>
      <div class="spell-dw">"Kharak azamar"</div>
      <span class="badge amber spell-tag">Curación · 1 slot · Acción bonus</span>
      <div class="spell-desc">Rango 60 pies. Levanta inconscientes a distancia. Económicamente superior a Cure Wounds.</div>
    </div>
    <div class="spell-card prepared">
      <div class="spell-name">Guiding Bolt</div>
      <div class="spell-dw">"Nar khalad sel"</div>
      <span class="badge amber spell-tag">Daño · 1 slot</span>
      <div class="spell-desc">4d6 radiante + ventaja al siguiente ataque vs ese objetivo. Tu opción ofensiva fuerte.</div>
    </div>
    <div class="spell-card prepared">
      <div class="spell-name">Shield of Faith</div>
      <div class="spell-dw">"Sel'dur"</div>
      <span class="badge amber spell-tag">Defensa · 1 slot · Concentración</span>
      <div class="spell-desc">+2 AC a un aliado. Útil en Fighter o Rogue en combates difíciles.</div>
    </div>
    <div class="spell-card prepared">
      <div class="spell-name">Command</div>
      <div class="spell-dw">"Karak dûm"</div>
      <span class="badge amber spell-tag">Control · 1 slot</span>
      <div class="spell-desc">Sin concentración. Un enemigo pierde su acción. No compite con Bless.</div>
    </div>
  </div>
  <div class="card gold" style="margin-top:16px">
    <div class="card-title" style="color:var(--gold2);margin-bottom:6px">Gestión de slots</div>
    <div class="card-sub">Tienes 3 slots de nivel 1. Bless ocupa 1. Guarda al menos 1 para Healing Word de emergencia. En nivel 3 obtendrás slots de nivel 2.</div>
  </div>
</div>

<!-- TAB: HABILIDADES -->
<div id="tab-habilidades" class="tab-panel">
  <div class="section-label">Features de clase — Twilight Domain</div>
  <div class="feature-card">
    <div class="feature-top"><div class="feature-name">Eyes of Night</div><span class="badge purple">Nivel 1 · 1 uso/descanso largo</span></div>
    <div class="feature-desc">Darkvision permanente de 300 pies para ti. Como acción: comparte esta visión con hasta 3 criaturas visibles durante 1 hora. En Icewind Dale, con 2 horas de luz al día, esta feature es crítica cada sesión.</div>
  </div>
  <div class="feature-card">
    <div class="feature-top"><div class="feature-name">Vigilant Blessing</div><span class="badge purple">Nivel 1 · Gasto de acción</span></div>
    <div class="feature-desc">Como acción, tocas a una criatura (o a ti) y le das ventaja en su próxima tirada de iniciativa. Se consume al tirar. Ideal para el Fighter o el Rogue antes de combates anticipados.</div>
  </div>
  <div class="feature-card">
    <div class="feature-top"><div class="feature-name">Twilight Sanctuary</div><span class="badge purple">Nivel 2 · Channel Divinity</span></div>
    <div class="feature-desc">Como acción, emana una esfera de penumbra de 30 pies centrada en ti. Se mueve contigo. Dura 1 minuto. Al final de cada turno dentro: 1d6+2 HP temporales, o elimina un efecto de miedo o encantamiento.</div>
  </div>
  <div class="feature-card">
    <div class="feature-top"><div class="feature-name">Turn Undead</div><span class="badge gray">Nivel 2 · Channel Divinity</span></div>
    <div class="feature-desc">Presenta tu símbolo sagrado. Cada no-muerto que te vea a 30 pies y falle SAB save es ahuyentado durante 1 minuto. Relevante en este módulo — ya hemos encontrado no-muertos.</div>
  </div>
  <div class="feature-card">
    <div class="feature-top"><div class="feature-name">Dwarven Toughness</div><span class="badge gray">Pasivo · Enano de Colina</span></div>
    <div class="feature-desc">+1 HP máximo por nivel. Ya incluido en tus HP. A nivel 2: +2 HP sobre la base normal. Aumenta cada nivel.</div>
  </div>
  <div class="feature-card">
    <div class="feature-top"><div class="feature-name">Stonecunning</div><span class="badge gray">Pasivo · Enano</span></div>
    <div class="feature-desc">Ventaja en Intelligence (History) relacionados con estructuras de piedra. Ya lo usaste en la cueva.</div>
  </div>
  <div class="section-label">Equipo importante</div>
  <div class="grid-2">
    <div class="card"><div class="card-title">Warhammer</div><div class="card-sub">Arma principal. 1d8 contundente. Proficiencia racial de enano.</div></div>
    <div class="card amber"><div class="card-title">Scale Mail + Escudo ⚠</div><div class="card-sub">CA actual: 15. Con Chain Mail sería 18. Tienes proficiencia en armadura pesada.</div></div>
    <div class="card"><div class="card-title">Quarterstaff</div><div class="card-sub">1d6/1d8 contundente. Versátil.</div></div>
    <div class="card"><div class="card-title">Handaxe</div><div class="card-sub">Arrojadiza. Le prestaste una a Dorbulgruf en el combate con Auril.</div></div>
    <div class="card"><div class="card-title">Cuerda 50 pies</div><div class="card-sub">La usaste para salvar a Teska del lago helado.</div></div>
    <div class="card"><div class="card-title">Rations x11</div><div class="card-sub">Necesarias para descanso largo. Bien abastecido.</div></div>
    <div class="card"><div class="card-title">Hunting Trap</div><div class="card-sub">Útil para comida en campo abierto.</div></div>
    <div class="card"><div class="card-title">Collar de colmillo</div><div class="card-sub">Loot de troglodita. Origen desconocido.</div></div>
  </div>
</div>"""

# ── Stub personal panels (para personajes no-Adrik) ────────────────────────────
def stub_personal_panels(member):
    name = member["name"]
    initial = member["initial"]
    color = member["color"]
    return f'''\
<!-- TAB: PERSONAJE -->
<div id="tab-personaje" class="tab-panel active">
  <div class="upload-zone" id="upload-zone">
    <div class="upload-icon">⬆</div>
    <div class="upload-title">Sube tu personaje</div>
    <div class="upload-desc">
      Exporta tu actor desde Foundry VTT<br>
      <strong style="color:var(--text)">Actor → botón derecho → Export Data</strong><br><br>
      Sube el archivo JSON aquí. Tus datos se guardan en este navegador.
    </div>
    <label class="upload-btn" for="json-file-input">Seleccionar archivo JSON</label>
    <input type="file" id="json-file-input" accept=".json" style="display:none" onchange="loadCharJSON(this)">
    <div class="upload-note">Los datos se guardan localmente (localStorage) y no se comparten.</div>
  </div>
  <div id="dynamic-stats"></div>
</div>'''

# ── Party content generators ───────────────────────────────────────────────────
def map_html():
    """SVG de relaciones + soporte para imagen de mapa."""
    map_img = os.path.join(BASE, "dist", "assets", "maps", "icewind-dale.jpg")
    map_img_section = ""
    if os.path.exists(map_img):
        map_img_section = '''<div class="section-label teal">Mapa de Icewind Dale</div>
  <div class="map-img-container">
    <img src="../assets/maps/icewind-dale.jpg" alt="Mapa de Icewind Dale">
  </div>'''

    return f'''{map_img_section}
  <div class="section-label teal">Mapa de relaciones</div>
  <div class="map-container">
    <svg viewBox="0 0 900 520" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arr" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
          <path d="M0,0 L0,6 L6,3 z" fill="rgba(201,150,58,0.4)"/>
        </marker>
      </defs>
      <line x1="450" y1="250" x2="180" y2="100" stroke="rgba(201,150,58,0.25)" stroke-width="1.5" marker-end="url(#arr)"/>
      <line x1="450" y1="250" x2="165" y2="200" stroke="rgba(201,150,58,0.25)" stroke-width="1.5" marker-end="url(#arr)"/>
      <line x1="450" y1="250" x2="160" y2="390" stroke="rgba(123,99,204,0.35)" stroke-width="1.5" stroke-dasharray="5,4" marker-end="url(#arr)"/>
      <line x1="450" y1="250" x2="310" y2="430" stroke="rgba(42,157,127,0.35)" stroke-width="1.5" marker-end="url(#arr)"/>
      <line x1="450" y1="250" x2="650" y2="430" stroke="rgba(74,138,222,0.35)" stroke-width="1.5" marker-end="url(#arr)"/>
      <line x1="450" y1="250" x2="710" y2="130" stroke="rgba(201,150,58,0.3)" stroke-width="1.5" marker-end="url(#arr)"/>
      <line x1="450" y1="250" x2="750" y2="250" stroke="rgba(204,51,51,0.5)" stroke-width="2" marker-end="url(#arr)"/>
      <line x1="450" y1="250" x2="450" y2="430" stroke="rgba(204,51,51,0.3)" stroke-width="1.5" stroke-dasharray="5,4" marker-end="url(#arr)"/>
      <line x1="750" y1="250" x2="450" y2="100" stroke="rgba(204,80,48,0.3)" stroke-width="1.5" marker-end="url(#arr)"/>
      <line x1="750" y1="250" x2="830" y2="390" stroke="rgba(204,80,48,0.25)" stroke-width="1.5" marker-end="url(#arr)"/>
      <line x1="710" y1="130" x2="830" y2="390" stroke="rgba(201,150,58,0.3)" stroke-width="1.5" marker-end="url(#arr)"/>
      <line x1="180" y1="100" x2="310" y2="430" stroke="rgba(201,150,58,0.2)" stroke-width="1" stroke-dasharray="4,4"/>
      <line x1="165" y1="200" x2="180" y2="100" stroke="rgba(201,150,58,0.2)" stroke-width="1"/>
      <text x="295" y="158" font-size="10" fill="rgba(201,150,58,0.6)" font-family="Source Sans 3, sans-serif" text-anchor="middle">enviado por</text>
      <text x="285" y="225" font-size="10" fill="rgba(201,150,58,0.6)" font-family="Source Sans 3, sans-serif" text-anchor="middle">origen</text>
      <text x="270" y="340" font-size="10" fill="rgba(123,99,204,0.7)" font-family="Source Sans 3, sans-serif" text-anchor="middle">fe cuestionada</text>
      <text x="368" y="365" font-size="10" fill="rgba(42,157,127,0.7)" font-family="Source Sans 3, sans-serif" text-anchor="middle">familiar / rescató</text>
      <text x="560" y="370" font-size="10" fill="rgba(74,138,222,0.7)" font-family="Source Sans 3, sans-serif" text-anchor="middle">compañeros</text>
      <text x="600" y="175" font-size="10" fill="rgba(201,150,58,0.6)" font-family="Source Sans 3, sans-serif" text-anchor="middle">contratado por</text>
      <text x="610" y="242" font-size="10" fill="rgba(204,51,51,0.8)" font-family="Source Sans 3, sans-serif" text-anchor="middle">enfrentamiento</text>
      <text x="465" y="355" font-size="10" fill="rgba(204,51,51,0.6)" font-family="Source Sans 3, sans-serif" text-anchor="middle">acusación</text>
      <rect x="390" y="218" width="120" height="64" rx="8" fill="rgba(201,150,58,0.15)" stroke="#C9963A" stroke-width="2"/>
      <text x="450" y="244" font-size="15" font-weight="600" fill="#E8B84B" font-family="Cinzel, serif" text-anchor="middle">Adrik</text>
      <text x="450" y="260" font-size="11" fill="rgba(201,150,58,0.8)" font-family="Source Sans 3, sans-serif" text-anchor="middle">Frostbeard</text>
      <text x="450" y="275" font-size="10" fill="rgba(201,150,58,0.6)" font-family="Source Sans 3, sans-serif" text-anchor="middle">Clérigo · Niv. 2</text>
      <rect x="108" y="74" width="144" height="48" rx="7" fill="rgba(22,29,52,0.9)" stroke="rgba(201,150,58,0.3)" stroke-width="1"/>
      <text x="180" y="97" font-size="13" font-weight="500" fill="#EDE6D6" font-family="Cinzel, serif" text-anchor="middle">Padre</text>
      <text x="180" y="113" font-size="10" fill="#9A9080" font-family="Source Sans 3, sans-serif" text-anchor="middle">Clan Frostbeard · Sur</text>
      <rect x="90" y="170" width="150" height="50" rx="7" fill="rgba(22,29,52,0.9)" stroke="rgba(201,150,58,0.3)" stroke-width="1"/>
      <text x="165" y="193" font-size="13" font-weight="500" fill="#EDE6D6" font-family="Cinzel, serif" text-anchor="middle">Clan Frostbeard</text>
      <text x="165" y="210" font-size="10" fill="#9A9080" font-family="Source Sans 3, sans-serif" text-anchor="middle">3 generaciones · Sur</text>
      <rect x="82" y="363" width="156" height="54" rx="7" fill="rgba(123,99,204,0.1)" stroke="rgba(123,99,204,0.4)" stroke-width="1" stroke-dasharray="4,3"/>
      <text x="160" y="386" font-size="13" font-weight="500" fill="#9B80EE" font-family="Cinzel, serif" text-anchor="middle">Selûne</text>
      <text x="160" y="402" font-size="10" fill="rgba(123,99,204,0.7)" font-family="Source Sans 3, sans-serif" text-anchor="middle">Diosa · fe cuestionada</text>
      <text x="160" y="415" font-size="10" fill="rgba(123,99,204,0.6)" font-family="Source Sans 3, sans-serif" text-anchor="middle">¿por qué yo?</text>
      <rect x="224" y="406" width="172" height="50" rx="7" fill="rgba(42,157,127,0.1)" stroke="rgba(42,157,127,0.35)" stroke-width="1"/>
      <text x="310" y="429" font-size="13" font-weight="500" fill="#2A9D7F" font-family="Cinzel, serif" text-anchor="middle">Dorbulgruf Shalescar</text>
      <text x="310" y="446" font-size="10" fill="rgba(42,157,127,0.7)" font-family="Source Sans 3, sans-serif" text-anchor="middle">Alcalde Bremen · Primo lejano · Rescatado</text>
      <rect x="350" y="72" width="200" height="48" rx="7" fill="rgba(123,99,204,0.1)" stroke="rgba(123,99,204,0.3)" stroke-width="1"/>
      <text x="450" y="95" font-size="13" font-weight="500" fill="#9B80EE" font-family="Cinzel, serif" text-anchor="middle">Invierno Eterno</text>
      <text x="450" y="111" font-size="10" fill="rgba(123,99,204,0.7)" font-family="Source Sans 3, sans-serif" text-anchor="middle">2 años sin sol · Causado por Auril</text>
      <rect x="680" y="216" width="140" height="68" rx="7" fill="rgba(204,51,51,0.1)" stroke="rgba(204,51,51,0.5)" stroke-width="1.5"/>
      <text x="750" y="241" font-size="14" font-weight="600" fill="#EE6060" font-family="Cinzel, serif" text-anchor="middle">Auril</text>
      <text x="750" y="257" font-size="10" fill="rgba(204,51,51,0.8)" font-family="Source Sans 3, sans-serif" text-anchor="middle">La Doncella del Hielo</text>
      <text x="750" y="272" font-size="10" fill="rgba(204,51,51,0.7)" font-family="Source Sans 3, sans-serif" text-anchor="middle">Antagonista principal</text>
      <rect x="344" y="402" width="212" height="54" rx="7" fill="rgba(204,51,51,0.08)" stroke="rgba(204,51,51,0.3)" stroke-width="1" stroke-dasharray="4,3"/>
      <text x="450" y="424" font-size="12" font-weight="500" fill="#EE8888" font-family="Cinzel, serif" text-anchor="middle">¿A quiénes dejé morir?</text>
      <text x="450" y="440" font-size="10" fill="rgba(204,51,51,0.7)" font-family="Source Sans 3, sans-serif" text-anchor="middle">Auril lo sabe · Hace 10 años</text>
      <text x="450" y="452" font-size="10" fill="rgba(204,51,51,0.6)" font-family="Source Sans 3, sans-serif" text-anchor="middle">Núcleo del arco personal</text>
      <rect x="622" y="100" width="176" height="52" rx="7" fill="rgba(201,150,58,0.1)" stroke="rgba(201,150,58,0.35)" stroke-width="1"/>
      <text x="710" y="123" font-size="13" font-weight="500" fill="#C9963A" font-family="Cinzel, serif" text-anchor="middle">Gillin Trollbane</text>
      <text x="710" y="140" font-size="10" fill="rgba(201,150,58,0.7)" font-family="Source Sans 3, sans-serif" text-anchor="middle">Salvadora · Empleadora · 100gp</text>
      <rect x="762" y="363" width="136" height="52" rx="7" fill="rgba(204,80,48,0.1)" stroke="rgba(204,80,48,0.35)" stroke-width="1"/>
      <text x="830" y="386" font-size="13" font-weight="500" fill="#CC5030" font-family="Cinzel, serif" text-anchor="middle">Sefek Caltro</text>
      <text x="830" y="402" font-size="10" fill="rgba(204,80,48,0.7)" font-family="Source Sans 3, sans-serif" text-anchor="middle">Objetivo · Piel azul</text>
      <text x="830" y="414" font-size="10" fill="rgba(204,80,48,0.6)" font-family="Source Sans 3, sans-serif" text-anchor="middle">No siente el frío</text>
      <rect x="564" y="400" width="180" height="62" rx="7" fill="rgba(74,138,222,0.1)" stroke="rgba(74,138,222,0.35)" stroke-width="1"/>
      <text x="654" y="422" font-size="13" font-weight="500" fill="#4A8ADE" font-family="Cinzel, serif" text-anchor="middle">La Party</text>
      <text x="654" y="438" font-size="10" fill="rgba(74,138,222,0.7)" font-family="Source Sans 3, sans-serif" text-anchor="middle">Sven · Draxus · Teska</text>
      <text x="654" y="452" font-size="10" fill="rgba(74,138,222,0.6)" font-family="Source Sans 3, sans-serif" text-anchor="middle">Elian · Yankavic</text>
    </svg>
  </div>
  <div class="grid-2">
    <div class="mystery-card">
      <div class="mystery-title">⚠ El misterio de Adrik</div>
      <div class="mystery-text">Auril le dijo directamente: "asesino, los dejaste morir, y lo sabes." Hace 10 años, Adrik sobrevivió una tormenta que mató a dos compañeros. ¿Fue solo eso? ¿O hay algo más? Este misterio es el núcleo del arco personal del personaje.</div>
    </div>
    <div class="feature-card">
      <div class="feature-name" style="margin-bottom:8px">Arco de fe con Selûne</div>
      <div class="feature-desc">Adrik tiene poderes que vienen de una diosa que no eligió activamente. Cada uso de sus poderes en momentos críticos es una oportunidad para que algo cambie. No hay que forzarlo: basta con ese segundo de silencio después de que algo funciona.</div>
    </div>
  </div>'''

def sessions_html(sd):
    if not sd or not sd.get("sessions"):
        return (
            '<div class="card" style="margin-top:0">'
            '<div class="card-title" style="color:var(--text2)">Sin sesiones sincronizadas</div>'
            '<div class="card-sub" style="margin-top:6px">Para sincronizar tu Google Doc ejecuta:<br>'
            '<code style="background:var(--surface2);padding:3px 8px;border-radius:4px;font-size:13px">'
            'python3 scripts/sync-gdocs.py</code>'
            '<br><br>O pega el contenido manualmente en <code>data/sessions.json</code>.</div></div>'
        )
    synced = sd.get("lastSynced", "")
    try:
        synced_str = datetime.fromisoformat(synced).strftime("%-d de %B, %H:%M")
    except Exception:
        synced_str = synced[:16] if synced else "desconocido"
    sessions = sd.get("sessions", [])
    parts = [f'<div style="margin-bottom:16px;font-size:12px;color:var(--text3)">Último sync: {synced_str} · {len(sessions)} sesión(es)</div>']
    for s in reversed(sessions):
        title   = s.get("title", "Sesión")
        date    = s.get("date", "")
        content = s.get("content", [])
        date_str = f' <span style="color:var(--text3);font-size:12px">· {date}</span>' if date else ""
        paras = "".join(f"<p style='margin-bottom:6px'>{p}</p>" for p in content)
        parts.append(
            f'<div class="card" style="margin-bottom:12px">'
            f'<div class="card-title">{title}{date_str}</div>'
            f'<div class="card-sub" style="margin-top:8px;line-height:1.7">{paras}</div>'
            f'</div>'
        )
    return "\n".join(parts)

def personajes_html(w):
    """Character backgrounds and development arcs tab."""
    party_data = w.get("party", [])
    arcs = {
        "adrik":    ("Outlander. Sobrevivió una tormenta hace 10 años que mató a dos compañeros. Tiene poderes que vienen de Selûne sin haberla elegido activamente.",
                     "Redención y fe cuestionada. Auril conoce su culpa — ¿cobardía o destino? Cada spell que funciona es un segundo de silencio ante una pregunta sin respuesta.",
                     ["Detectó con Insight que Aliana mentía", "Levantó a Elian dos veces en sesión 2", "Le prestó el hacha a Dorbulgruf contra Auril"]),
        "sven":     ("Marinero del norte originario de Thermaline. Piel azulada, escarcha en la barba, cicatriz en un ojo. Muy conectado con el norte y el mar helado.",
                     "¿Por qué alguien del norte está tan cómodo con este frío? Hay algo en su conexión con Icewind Dale que aún no ha revelado.",
                     ["Sneak Attack con flecha de fuego en la primera batalla"]),
        "draxus":   ("Dragonborn plateado del sur. Tabardo con yunque. Resistencia innata al frío — inusual incluso para su raza.",
                     "Busca a alguien. Auril le dijo que lo preservaría solo a él. El nombre de quien busca podría estar ligado a la historia de la región.",
                     ["Fue el último en caer ante Auril", "Auril lo llamó por su nombre antes de que él la nombrara"]),
        "teska":    ("Tiefling bardo, agente de los Arpistas enviado a investigar Bremen.",
                     "La lealtad de los Arpistas puesta en duda: Auril le dijo que sus propios empleadores lo enviaron para deshacerse de él. ¿Misión o trampa?",
                     ["Diplomático en negociaciones tensas", "Heroísmo activo en el combate con Auril"]),
        "elian":    ("Mago humano joven, lleva un diario. Promesa incumplida a su abuelo. Habla en élfico al castear hechizos.",
                     "El más frágil del grupo pero con el mayor potencial. Cayó dos veces en la misma sesión — algo en él sigue eligiendo levantarse.",
                     ["Cayó inconsciente 2 veces en sesión 2", "Adrik lo levantó ambas veces", "Habla en élfico — origen o formación inusuales"]),
        "yankavic": ("Paladín semielfo de Dungask Hold. Busca a su maestro desaparecido. Subclase de tormenta.",
                     "Auril lo amenazó directamente — dijo que su juramento se rompería y que él atraería a los no-muertos. El peso de esa amenaza aún no ha materializado.",
                     ["Auril lo nombró directamente entre los presentes", "Su maestro desaparecido podría estar relacionado con los eventos del módulo"]),
    }

    parts = [
        '<div class="section-label teal">La Party · Arcos y Trasfondos</div>',
        '<div class="card" style="margin-bottom:20px;border-color:rgba(42,157,127,0.2);background:rgba(42,157,127,0.05)">'
        '<div class="card-sub" style="font-size:13px">Los arcos de cada personaje se van entrelazando con la historia de Icewind Dale. '
        'Las amenazas de Auril tocaron algo personal en cada miembro de la party — no fue al azar.</div></div>'
    ]

    # Adrik first (the player character)
    adrik_info = PARTY_BY_SLUG["adrik"]
    bg, arc, moments = arcs["adrik"]
    portrait_html = (
        f'<img src="../assets/portraits/adrik.jpg" style="width:100%;height:100%;object-fit:cover" '
        f'onerror="this.style.display=\'none\';this.parentElement.innerHTML=\'A\'">'
    )
    moment_tags = "".join(f'<span class="moment-tag">{m}</span>' for m in moments)
    parts.append(f'''
<div class="party-char-card" style="border-left:3px solid {adrik_info["color"]}">
  <div class="party-char-portrait" style="background:{adrik_info["bg"]};color:{adrik_info["color"]};border-color:{adrik_info["border"]}">{portrait_html}</div>
  <div class="party-char-body">
    <div class="party-char-name">Adrik Frostbeard <span style="font-size:11px;color:var(--gold);font-family:\'Source Sans 3\',sans-serif;font-weight:normal">· tú</span></div>
    <div class="party-char-class">Clérigo · Dominio Crepúsculo · Enano de Colina</div>
    <div class="party-char-bg">{bg}</div>
    <div class="party-char-arc">Arco: {arc}</div>
    <div class="party-char-moments">{moment_tags}</div>
  </div>
</div>''')

    # Other party members
    for m in PARTY[1:]:
        slug = m["slug"]
        bg_text, arc_text, moment_list = arcs.get(slug, ("Sin información aún.", "", []))
        # Get info from world.json party array
        world_info = next((p for p in party_data if p.get("name","").lower().startswith(slug)), {})
        class_info = world_info.get("class", m["class_str"] + " · " + m["race_str"])
        portrait_html = (
            f'<img src="../assets/portraits/{slug}.jpg" style="width:100%;height:100%;object-fit:cover" '
            f'onerror="this.style.display=\'none\';this.parentElement.innerHTML=\'{m["initial"]}\'">'
        )
        moment_tags = "".join(f'<span class="moment-tag">{mo}</span>' for mo in moment_list)
        note = world_info.get("note", "")
        if note and note != bg_text:
            bg_display = bg_text
        else:
            bg_display = bg_text
        parts.append(f'''
<div class="party-char-card">
  <div class="party-char-portrait" style="background:{m["bg"]};color:{m["color"]};border-color:{m["border"]}">{portrait_html}</div>
  <div class="party-char-body">
    <div class="party-char-name">{m["name"]}</div>
    <div class="party-char-class">{class_info}</div>
    <div class="party-char-bg">{bg_display}</div>
    <div class="party-char-arc">Arco: {arc_text}</div>
    <div class="party-char-moments">{moment_tags}</div>
    <a href="../{slug}/index.html" class="party-char-link">Ver página de {m["name"]} →</a>
  </div>
</div>''')
    return "\n".join(parts)

def misiones_html(w):
    """Active quests + mysteries + open threads."""
    quests    = w.get("quests", [])
    mysteries = w.get("mysteries", [])
    parts     = []

    if quests:
        parts.append('<div class="section-label teal">Misiones Activas</div>')
        for q in quests:
            status_color = "var(--gold2)" if q.get("status") == "active" else "var(--text3)"
            status_label = "Activa" if q.get("status") == "active" else q.get("status", "")
            reward = q.get("reward", "")
            reward_html = f'<div class="quest-reward"><strong>Recompensa:</strong> {reward}</div>' if reward else ""
            notes_lines = []
            if q.get("client"):   notes_lines.append(f'<strong>Contratante:</strong> {q["client"]}')
            if q.get("target"):   notes_lines.append(f'<strong>Objetivo:</strong> {q["target"]}')
            if q.get("description"): notes_lines.append(q["description"])
            if q.get("notes"):    notes_lines.append(f'<em>{q["notes"]}</em>')
            notes_html = "<br>".join(notes_lines) if notes_lines else ""
            parts.append(f'''<div class="quest-card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">
    <div class="quest-title">{q.get("title","")}</div>
    <span class="badge amber">{status_label}</span>
  </div>
  {reward_html}
  <div class="quest-note">{notes_html}</div>
</div>''')

    if mysteries:
        parts.append('<div class="section-label teal" style="margin-top:24px">Misterios y Hilos Abiertos</div>')
        for mystery in mysteries:
            parts.append(f'''<div class="mystery-card">
  <div class="mystery-title">🔴 {mystery.get("title","")}</div>
  <div class="mystery-text">{mystery.get("description","")}</div>
</div>''')

    # Static open threads
    parts.append('''<div class="section-label teal" style="margin-top:24px">Preguntas Sin Respuesta</div>
<div class="card" style="border-left:3px solid rgba(204,51,51,0.4);background:rgba(204,51,51,0.04)">
  <div class="card-title" style="color:#EE8888;font-size:14px">¿Qué le pasó al maestro de Yankavic?</div>
  <div class="card-sub">Yankavic busca a su maestro desaparecido. Auril lo amenazó directamente, lo que sugiere una conexión con los eventos del módulo.</div>
</div>
<div class="card" style="border-left:3px solid rgba(204,51,51,0.4);background:rgba(204,51,51,0.04)">
  <div class="card-title" style="color:#EE8888;font-size:14px">¿A quién busca Draxus?</div>
  <div class="card-sub">El dragonborn plateado viajó desde el sur buscando a alguien. Auril dijo que lo preservaría "solo a él" — como si conociera su historia.</div>
</div>
<div class="card" style="border-left:3px solid rgba(204,51,51,0.4);background:rgba(204,51,51,0.04)">
  <div class="card-title" style="color:#EE8888;font-size:14px">¿Los Arpistas traicionaron a Teska?</div>
  <div class="card-sub">Auril le dijo que sus propios empleadores lo enviaron para deshacerse de él. ¿Misión encubierta o trampa?</div>
</div>''')
    return "\n".join(parts)

def mundo_html(w):
    """NPCs (antagonists + allies) + places."""
    npcs   = w.get("npcs", [])
    places = w.get("places", [])
    parts  = []

    antagonists = [n for n in npcs if n.get("category") == "antagonist"]
    allies      = [n for n in npcs if n.get("category") == "ally"]

    if antagonists:
        parts.append('<div class="section-label teal">Antagonistas</div>')
        for npc in antagonists:
            role = npc.get("role", "")
            rel  = npc.get("relation", "")
            note = npc.get("note", "")
            is_main = "principal" in role.lower() or "Auril" in npc.get("name","")
            color   = "var(--red)" if is_main else "var(--coral)"
            bg_cls  = "red" if is_main else "coral"
            parts.append(f'''<div class="persona-card" style="border-left:3px solid {color};background:linear-gradient(90deg,rgba({("204,51,51" if is_main else "204,80,48")},0.08),var(--surface))">
  <div class="persona-header">
    <div class="persona-name" style="color:{color}">{npc.get("name","")}</div>
    <span class="badge {bg_cls}">{role}</span>
  </div>
  <div class="persona-rel">{rel}</div>
  <div class="persona-note">{note}</div>
</div>''')

    if allies:
        parts.append('<div class="section-label teal" style="margin-top:24px">Aliados</div>')
        for npc in allies:
            role = npc.get("role", "")
            rel  = npc.get("relation", "")
            note = npc.get("note", "")
            color = "var(--amber)" if "emplea" in role.lower() else "var(--teal)"
            badge = "amber" if "emplea" in role.lower() else "teal"
            parts.append(f'''<div class="persona-card" style="border-left:3px solid {color}">
  <div class="persona-header">
    <div class="persona-name">{npc.get("name","")}</div>
    <span class="badge {badge}">{role}</span>
  </div>
  <div class="persona-rel">{rel}</div>
  <div class="persona-note">{note}</div>
</div>''')

    if places:
        parts.append('<hr class="divider"><div class="section-label teal">Lugares</div>')
        for place in places:
            name = place.get("name", "")
            desc = place.get("desc", "")
            is_dangerous = any(w in name.lower() for w in ["cueva","cave","haven","targos","bryn"])
            cls = "coral" if is_dangerous else ""
            parts.append(f'<div class="card {cls}"><div class="card-title">{name}</div><div class="card-sub">{desc}</div></div>')

    return "\n".join(parts)

# ── Hub HTML generation ────────────────────────────────────────────────────────
def hub_party_card(member, char_data, sessions_data):
    slug      = member["slug"]
    name      = member["name"]
    color     = member["color"]
    border    = member["border"]
    bg        = member["bg"]
    initial   = member["initial"]
    player    = member.get("player")
    is_player = member.get("is_player", False)

    # Level and class display
    if slug == "adrik" and char_data:
        lvl      = char_data.get("level", "?")
        class_en = char_data.get("class", "")
        CLASS_ES2 = {"Cleric": "Clérigo", "Fighter": "Guerrero", "Rogue": "Pícaro",
                     "Wizard": "Mago", "Paladin": "Paladín", "Bard": "Bardo"}
        class_str = CLASS_ES2.get(class_en, class_en) or member["class_str"]
        race_str  = RACE_ES.get(char_data.get("race",""), char_data.get("race","")) or member["race_str"]
    else:
        lvl       = "?"
        class_str = member["class_str"]
        race_str  = member["race_str"]

    # Portrait — always use <img> with onerror fallback (handles images added after build)
    portrait_html = (
        f'<img class="portrait-img" src="assets/portraits/{slug}.jpg" '
        f'alt="{name}" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'">'
        f'<div class="portrait-fallback" style="display:none;background:{bg};color:{color};border-color:{border}">{initial}</div>'
    )

    player_tag = f' <span class="player-you">tú</span>' if is_player else (f'<span class="player-name">{player}</span>' if player else "")
    card_cls   = "char-card is-player" if is_player else "char-card"
    level_html = f'<span style="color:{color};font-family:Cinzel,serif;font-size:12px">Nivel {lvl}</span> · ' if lvl != "?" else ""

    return f'''\
<a href="{slug}/index.html" class="{card_cls}" style="border-color:{border if is_player else 'var(--surface3)'}">
  <div class="portrait-wrap">{portrait_html}</div>
  <div class="char-info">
    <div class="char-card-name">{name}{player_tag}</div>
    <div class="char-card-class">{class_str}</div>
    <div class="char-card-race">{level_html}{race_str}</div>
  </div>
  <div class="char-card-arrow" style="color:{color}">→</div>
</a>'''

def build_hub():
    sessions_count = len(sessions_data.get("sessions", [])) if sessions_data else 0
    quests = world.get("quests", [])
    active_quest = next((q["title"] for q in quests if q.get("status") == "active"), "Sin quest activa")

    cards_html = "\n".join(hub_party_card(m, char, sessions_data) for m in PARTY)

    quest_html = ""
    for q in quests:
        if q.get("status") == "active":
            quest_html += f'''<div class="quest-banner">
  <div class="quest-icon">⚔</div>
  <div class="quest-body">
    <div class="quest-label">Quest Activa</div>
    <div class="quest-title">{q.get("title","")}</div>
    <div class="quest-detail">{q.get("description","")}</div>
  </div>
</div>'''

    build_date = datetime.now().strftime("%-d %b %Y")
    last_upd   = last_updated(char) if char else build_date

    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Icewind Dale · Party Hub</title>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600&family=Source+Sans+3:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
<style>
:root {{
  --bg:#080b16;--surface:#0f1425;--surface2:#161e34;--surface3:#1d2640;
  --gold:#C9963A;--gold2:#E8B84B;--gold-border:rgba(201,150,58,0.3);--gold-border2:rgba(201,150,58,0.55);
  --text:#F8F3E8;--text2:#C8BEA8;--text3:#8A8070;
  --teal:#2A9D7F;--teal2:#4ABFA0;--teal-bg:rgba(42,157,127,0.12);
  --radius:10px;--radius-sm:6px;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:'Source Sans 3',sans-serif;font-size:16px;line-height:1.65;min-height:100vh}}
h1,h2,h3{{font-family:'Cinzel',serif}}
.header{{background:linear-gradient(180deg,#040710 0%,#080c1a 50%,#0b1020 100%);border-bottom:1px solid var(--gold-border);padding:48px 36px 36px;text-align:center;position:relative;overflow:hidden}}
.header::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--gold),transparent)}}
.campaign-label{{font-family:'Cinzel',serif;font-size:12px;color:var(--gold);text-transform:uppercase;letter-spacing:3px;margin-bottom:10px}}
.hub-title{{font-family:'Cinzel',serif;font-size:40px;font-weight:600;color:var(--gold2);letter-spacing:1px;line-height:1.1;margin-bottom:8px}}
.hub-sub{{font-size:14px;color:var(--text3);font-style:italic;margin-bottom:28px}}
.hub-stats{{display:flex;justify-content:center;gap:32px;flex-wrap:wrap;font-size:13px;color:var(--text2)}}
.hub-stat strong{{color:var(--gold);font-family:'Cinzel',serif}}
.content{{max-width:1200px;margin:0 auto;padding:40px 28px}}
.section-label{{font-family:'Cinzel',serif;font-size:11px;font-weight:500;color:var(--gold);text-transform:uppercase;letter-spacing:1.2px;margin:0 0 20px;display:flex;align-items:center;gap:10px}}
.section-label::before,.section-label::after{{content:'';flex:1;height:1px;background:var(--gold-border)}}
.party-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px;margin-bottom:40px}}
.char-card{{display:flex;gap:16px;align-items:center;background:var(--surface);border:1px solid var(--surface3);border-radius:var(--radius);padding:18px;text-decoration:none;color:inherit;transition:all 0.25s;position:relative;overflow:hidden}}
.char-card:hover{{border-color:var(--gold-border);background:var(--surface2);transform:translateY(-2px)}}
.char-card.is-player{{border-color:var(--gold-border);background:linear-gradient(135deg,rgba(201,150,58,0.06),var(--surface))}}
.char-card.is-player:hover{{border-color:var(--gold-border2)}}
.portrait-wrap{{position:relative;flex-shrink:0}}
.portrait-img{{width:68px;height:68px;border-radius:50%;object-fit:cover;border:2px solid var(--gold-border);display:block}}
.portrait-fallback{{width:68px;height:68px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:'Cinzel',serif;font-size:24px;font-weight:600;border:2px solid}}
.char-info{{flex:1;min-width:0}}
.char-card-name{{font-family:'Cinzel',serif;font-size:16px;font-weight:500;color:var(--text);margin-bottom:3px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}}
.char-card-class{{font-size:13px;color:var(--text2);margin-bottom:2px}}
.char-card-race{{font-size:12px;color:var(--text3)}}
.char-card-arrow{{font-size:16px;flex-shrink:0;transition:all 0.2s}}
.char-card:hover .char-card-arrow{{transform:translateX(3px)}}
.player-you{{font-size:10px;color:var(--gold);font-family:'Cinzel',serif;text-transform:uppercase;letter-spacing:0.8px;background:rgba(201,150,58,0.1);border:1px solid rgba(201,150,58,0.3);border-radius:20px;padding:1px 7px;font-style:normal}}
.player-name{{font-size:11px;color:var(--text3);font-family:'Source Sans 3',sans-serif}}
.quest-banner{{background:linear-gradient(135deg,rgba(201,150,58,0.1),var(--surface));border:1px solid var(--gold-border);border-radius:var(--radius);padding:18px 20px;display:flex;gap:16px;align-items:flex-start;margin-bottom:14px}}
.quest-icon{{font-size:20px;flex-shrink:0}}
.quest-body{{flex:1}}
.quest-label{{font-size:10px;color:var(--gold);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;font-family:'Cinzel',serif}}
.quest-title{{font-family:'Cinzel',serif;font-size:15px;color:var(--text);margin-bottom:4px}}
.quest-detail{{font-size:13px;color:var(--text2)}}
.footer{{text-align:center;padding:24px;font-size:12px;color:var(--text3);border-top:1px solid var(--surface3)}}
::-webkit-scrollbar{{width:6px}}::-webkit-scrollbar-track{{background:var(--bg)}}::-webkit-scrollbar-thumb{{background:var(--surface3);border-radius:3px}}
</style>
</head>
<body>
<div class="header">
  <div class="campaign-label">Icewind Dale</div>
  <div class="hub-title">Rime of the Frostmaiden</div>
  <div class="hub-sub">El invierno eterno de Auril · Los Diez Pueblos</div>
  <div class="hub-stats">
    <div class="hub-stat"><strong>{sessions_count}</strong> sesiones</div>
    <div class="hub-stat"><strong>6</strong> aventureros</div>
    <div class="hub-stat">actualizado <strong>{last_upd}</strong></div>
  </div>
</div>
<div class="content">
  <div class="section-label">La Party</div>
  <div class="party-grid">
{cards_html}
  </div>
  <div class="section-label">Quest Activa</div>
{quest_html}
</div>
<div class="footer">Adrik Compendium · Generado {build_date} · <a href="#" onclick="logout();return false" style="color:var(--text3);text-decoration:none">Cerrar sesión</a></div>
</body>
<script>
const _SK2='icewind_session';
function _getSess(){{try{{return JSON.parse(localStorage.getItem(_SK2));}}catch{{return null;}}}}
function logout(){{localStorage.removeItem(_SK2);location.href='../index.html';}}
(function(){{
  const s=_getSess();
  if(!s){{location.replace('../index.html');return;}}
  // Show admin link for admin users
  if(s.admin){{
    const footer=document.querySelector('.footer');
    if(footer)footer.insertAdjacentHTML('afterbegin',
      '<a href="../admin/index.html" style="color:var(--gold);text-decoration:none;font-family:Cinzel,serif;font-size:11px;text-transform:uppercase;letter-spacing:0.8px;margin-right:16px">★ Admin</a>');
  }}
  // Show session user
  const header=document.querySelector('.hub-stats');
  if(header)header.insertAdjacentHTML('beforeend',
    '<div class="hub-stat" style="margin-left:8px;padding-left:16px;border-left:1px solid var(--surface3)">'+
    'Sesión: <strong style="color:var(--gold)">'+s.slug+'</strong></div>');
}})();
</script>
</html>'''

    hub_dir = os.path.join(BASE, "dist", "hub")
    os.makedirs(hub_dir, exist_ok=True)
    out = os.path.join(hub_dir, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ dist/hub/index.html (hub)")

# ── Character page builder ─────────────────────────────────────────────────────
def build_character_page(member):
    slug        = member["slug"]
    is_adrik    = (slug == "adrik")
    name        = member["name"]
    color       = member["color"]
    border      = member["border"]
    bg          = member["bg"]
    initial     = member["initial"]
    class_str   = member["class_str"]
    race_str    = member["race_str"]

    portrait_rel = f"../assets/portraits/{slug}.jpg"
    portrait_abs = os.path.join(BASE, "dist", "assets", "portraits", f"{slug}.jpg")

    # Adrik data from character.json; others use world.json party data
    if is_adrik and char:
        subtitle  = char_subtitle(char)
        upd       = last_updated(char)
        warnings  = warnings_html(char.get("warnings", []))
        hdr       = adrik_header_content(char)
        pers_btns = ADRIK_PERSONAL_BUTTONS
        pers_pnls = ADRIK_PERSONAL_PANELS
        slots_total = char.get("spellSlots", {}).get("1", {}).get("max", 3)
    else:
        world_member = next((p for p in world.get("party", []) if p.get("name","").lower().startswith(slug)), {})
        subtitle  = f'{class_str} · {race_str}'
        upd       = datetime.now().strftime("%-d %b %Y")
        warnings  = ""
        hdr       = ""
        pers_btns = '<button class="tab-btn tab-personal active" onclick="switchTab(\'personaje\',this)">📋 Personaje</button>'
        pers_pnls = stub_personal_panels(member)
        slots_total = 0

    # Party content (same for all)
    _map    = map_html()
    _sess   = sessions_html(sessions_data)
    _pers   = personajes_html(world)
    _mis    = misiones_html(world)
    _mundo  = mundo_html(world)

    html = CHAR_TMPL
    replacements = {
        "{{CHAR_NAME}}":           name,
        "{{CHAR_SUBTITLE}}":       subtitle,
        "{{LAST_UPDATED}}":        upd,
        "{{PORTRAIT_SRC}}":        portrait_rel,
        "{{PORTRAIT_INITIAL}}":    initial,
        "{{CHAR_COLOR}}":          color,
        "{{CHAR_BORDER}}":         border,
        "{{CHAR_BG}}":             bg,
        "{{WARNINGS}}":            warnings,
        "{{HEADER_CONTENT}}":      hdr,
        "{{PERSONAL_TAB_BUTTONS}}": pers_btns,
        "{{PERSONAL_TAB_PANELS}}": pers_pnls,
        "{{CHAR_SLUG}}":           slug,
        "{{SLOTS_TOTAL}}":         str(slots_total),
        "{{MAP_HTML}}":            _map,
        "{{SESSIONS_HTML}}":       _sess,
        "{{PERSONAJES_HTML}}":     _pers,
        "{{MISIONES_HTML}}":       _mis,
        "{{MUNDO_HTML}}":          _mundo,
        "{{AUTH_SCRIPT}}":         auth_script(slug),
    }
    for k, v in replacements.items():
        html = html.replace(k, v)

    out_dir = os.path.join(BASE, "dist", slug)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    tag = "(pre-renderizado)" if is_adrik else "(stub + upload)"
    print(f"   dist/{slug}/index.html {tag}")

# ── Login page ─────────────────────────────────────────────────────────────────
def build_login():
    creds_js = json.dumps({k: {"p": v["password"], "a": v["admin"]} for k, v in CREDENTIALS.items()})
    cards = ""
    for m in PARTY:
        slug    = m["slug"]
        name    = m["name"]
        color   = m["color"]
        border  = m["border"]
        bg      = m["bg"]
        initial = m["initial"]
        cs      = m["class_str"]
        rs      = m["race_str"]
        cards += f'''
    <div class="char-card" data-slug="{slug}" onclick="selectChar(this)"
         style="--c:{color};--b:{border};--bg:{bg}">
      <div class="card-portrait">
        <img src="assets/portraits/{slug}.jpg" alt="{name}"
             onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
        <div class="portrait-init" style="display:none;background:{bg};color:{color};border-color:{border}">{initial}</div>
      </div>
      <div class="card-info">
        <div class="card-name">{name}</div>
        <div class="card-class">{cs}</div>
        <div class="card-race">{rs}</div>
      </div>
    </div>'''

    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Icewind Dale · Compendium</title>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600&family=Source+Sans+3:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
<style>
:root{{--bg:#080b16;--surface:#0f1425;--surface2:#161e34;--surface3:#1d2640;
  --gold:#C9963A;--gold2:#E8B84B;--gold-border:rgba(201,150,58,0.3);
  --text:#F8F3E8;--text2:#C8BEA8;--text3:#8A8070;--radius:10px}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:'Source Sans 3',sans-serif;min-height:100vh;
  display:flex;align-items:center;justify-content:center;padding:24px}}
h1,h2{{font-family:'Cinzel',serif}}
.container{{width:100%;max-width:680px}}
.header{{text-align:center;margin-bottom:40px}}
.campaign{{font-family:'Cinzel',serif;font-size:11px;color:var(--gold);text-transform:uppercase;
  letter-spacing:3px;margin-bottom:8px}}
.title{{font-family:'Cinzel',serif;font-size:34px;font-weight:600;color:var(--gold2);
  line-height:1.1;margin-bottom:6px}}
.sub{{font-size:14px;color:var(--text3);font-style:italic}}
.chars-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:28px}}
@media(max-width:520px){{.chars-grid{{grid-template-columns:repeat(2,1fr)}}}}
.char-card{{background:var(--surface);border:2px solid var(--surface3);border-radius:var(--radius);
  padding:14px;cursor:pointer;transition:all 0.2s;display:flex;align-items:center;gap:10px}}
.char-card:hover{{border-color:var(--b,var(--gold-border));background:var(--surface2)}}
.char-card.selected{{border-color:var(--b);background:rgba(from var(--c) r g b / 0.08);
  box-shadow:0 0 0 1px var(--b)}}
.card-portrait{{position:relative;flex-shrink:0}}
.card-portrait img{{width:44px;height:44px;border-radius:50%;object-fit:cover;display:block;
  border:1.5px solid var(--gold-border)}}
.portrait-init{{width:44px;height:44px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;font-family:'Cinzel',serif;font-size:18px;font-weight:600;border:1.5px solid}}
.card-info{{flex:1;min-width:0}}
.card-name{{font-family:'Cinzel',serif;font-size:13px;font-weight:500;color:var(--text);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.card-class{{font-size:11px;color:var(--text2)}}
.card-race{{font-size:11px;color:var(--text3)}}
.login-form{{background:var(--surface);border:1px solid var(--gold-border);border-radius:var(--radius);
  padding:24px;display:none}}
.login-form.visible{{display:block}}
.form-label{{font-family:'Cinzel',serif;font-size:11px;color:var(--gold);text-transform:uppercase;
  letter-spacing:0.8px;margin-bottom:8px;display:block}}
.form-row{{display:flex;gap:10px;align-items:stretch}}
.pw-input{{flex:1;background:var(--surface2);border:1px solid var(--surface3);border-radius:6px;
  padding:12px 14px;color:var(--text);font-size:15px;font-family:'Source Sans 3',sans-serif;
  outline:none;transition:border-color 0.2s}}
.pw-input:focus{{border-color:var(--gold-border)}}
.login-btn{{background:var(--gold);color:#080b16;border:none;border-radius:6px;padding:12px 20px;
  font-family:'Cinzel',serif;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap;
  transition:all 0.2s}}
.login-btn:hover{{background:var(--gold2)}}
.error-msg{{color:#EE6060;font-size:13px;margin-top:10px;display:none}}
.who-label{{font-size:13px;color:var(--text2);margin-bottom:14px}}
.who-name{{color:var(--gold2);font-family:'Cinzel',serif}}
::-webkit-scrollbar{{width:6px}}::-webkit-scrollbar-track{{background:var(--bg)}}
::-webkit-scrollbar-thumb{{background:var(--surface3);border-radius:3px}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="campaign">Icewind Dale</div>
    <div class="title">Rime of the Frostmaiden</div>
    <div class="sub">El invierno eterno de Auril · Los Diez Pueblos</div>
  </div>

  <div class="chars-grid">{cards}
  </div>

  <div class="login-form" id="loginForm">
    <div class="who-label">Bienvenido, <span class="who-name" id="whoName">—</span></div>
    <label class="form-label" for="pwInput">Contraseña</label>
    <div class="form-row">
      <input type="password" class="pw-input" id="pwInput"
             placeholder="tu contraseña..." onkeydown="if(event.key==='Enter')doLogin()">
      <button class="login-btn" onclick="doLogin()">Entrar →</button>
    </div>
    <div class="error-msg" id="errMsg">Contraseña incorrecta. Intenta de nuevo.</div>
  </div>
</div>
<script>
const CREDS = {creds_js};
const _SK = 'icewind_session';
let _sel = null;

// Already logged in? Redirect
(function() {{
  try {{
    const s = JSON.parse(localStorage.getItem(_SK));
    if (s && s.slug) {{
      location.replace(s.admin ? 'hub/index.html' : s.slug + '/index.html');
    }}
  }} catch(e) {{}}
}})();

function selectChar(el) {{
  document.querySelectorAll('.char-card').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
  _sel = el.dataset.slug;
  document.getElementById('whoName').textContent = el.querySelector('.card-name').textContent;
  const form = document.getElementById('loginForm');
  form.classList.add('visible');
  document.getElementById('pwInput').value = '';
  document.getElementById('errMsg').style.display = 'none';
  document.getElementById('pwInput').focus();
}}

function doLogin() {{
  if (!_sel) return;
  const pw = document.getElementById('pwInput').value.trim().toLowerCase();
  const cred = CREDS[_sel];
  if (!cred || pw !== cred.p) {{
    const err = document.getElementById('errMsg');
    err.style.display = 'block';
    document.getElementById('pwInput').select();
    return;
  }}
  const session = {{ slug: _sel, admin: cred.a, loginTime: Date.now() }};
  localStorage.setItem(_SK, JSON.stringify(session));
  // Track login
  try {{
    const ev = JSON.parse(localStorage.getItem('icewind_analytics') || '[]');
    ev.push({{ t: 'login', d: {{ slug: _sel }}, ts: Date.now() }});
    localStorage.setItem('icewind_analytics', JSON.stringify(ev));
    localStorage.setItem('last_login_' + _sel, Date.now());
  }} catch(e) {{}}
  location.href = cred.a ? 'hub/index.html' : _sel + '/index.html';
}}
</script>
</body>
</html>'''

    out = os.path.join(BASE, "dist", "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ dist/index.html (login)")


# ── Admin dashboard ─────────────────────────────────────────────────────────────
def build_admin():
    party_rows = ""
    for m in PARTY:
        slug = m["slug"]
        name = m["name"]
        color = m["color"]
        cs   = m["class_str"]
        rs   = m["race_str"]
        party_rows += f'''
      {{ slug: "{slug}", name: "{name}", color: "{color}", class_str: "{cs}", race: "{rs}" }},'''

    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin · Adrik Compendium</title>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600&family=Source+Sans+3:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
<style>
:root{{--bg:#080b16;--surface:#0f1425;--surface2:#161e34;--surface3:#1d2640;
  --gold:#C9963A;--gold2:#E8B84B;--gold-border:rgba(201,150,58,0.3);--gold-border2:rgba(201,150,58,0.55);
  --text:#F8F3E8;--text2:#C8BEA8;--text3:#8A8070;--teal:#2A9D7F;--teal-bg:rgba(42,157,127,0.12);
  --green:#4ADE80;--red:#EE6060;--amber:#C9963A;--radius:10px}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:'Source Sans 3',sans-serif;font-size:15px;line-height:1.65;min-height:100vh}}
h1,h2,h3{{font-family:'Cinzel',serif}}
.header{{background:linear-gradient(180deg,#040710,#080c1a);border-bottom:1px solid var(--gold-border);
  padding:28px 32px 24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}}
.header::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,var(--gold),transparent)}}
.header{{position:relative}}
.header-left h1{{font-size:24px;color:var(--gold2)}}
.header-left p{{font-size:12px;color:var(--text3);margin-top:4px}}
.header-links a{{font-size:12px;color:var(--text2);text-decoration:none;margin-left:16px}}
.header-links a:hover{{color:var(--gold)}}
.content{{max-width:1100px;margin:0 auto;padding:32px 28px}}
.section-label{{font-family:'Cinzel',serif;font-size:11px;font-weight:500;color:var(--gold);
  text-transform:uppercase;letter-spacing:1.2px;margin:28px 0 16px;display:flex;align-items:center;gap:10px}}
.section-label::before,.section-label::after{{content:'';flex:1;height:1px;background:var(--gold-border)}}
.section-label:first-child{{margin-top:0}}
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin-bottom:8px}}
.stat-card{{background:var(--surface);border:1px solid var(--surface3);border-radius:var(--radius);
  padding:18px 20px;text-align:center}}
.stat-val{{font-family:'Cinzel',serif;font-size:30px;font-weight:600;color:var(--gold2);display:block}}
.stat-lbl{{font-size:12px;color:var(--text3);text-transform:uppercase;letter-spacing:0.6px;margin-top:4px;display:block}}
.char-table{{width:100%;border-collapse:collapse;margin-bottom:8px}}
.char-table th{{text-align:left;font-family:'Cinzel',serif;font-size:11px;color:var(--text3);
  text-transform:uppercase;letter-spacing:0.8px;padding:8px 12px;border-bottom:1px solid var(--surface3)}}
.char-table td{{padding:12px;border-bottom:1px solid var(--surface2);vertical-align:middle}}
.char-table tr:hover td{{background:var(--surface2)}}
.char-name{{font-family:'Cinzel',serif;font-size:14px;font-weight:500}}
.badge-yes{{background:rgba(74,222,128,0.1);color:var(--green);border:1px solid rgba(74,222,128,0.3);
  border-radius:20px;padding:2px 10px;font-size:11px;font-family:'Cinzel',serif}}
.badge-no{{background:rgba(238,96,96,0.1);color:var(--red);border:1px solid rgba(238,96,96,0.3);
  border-radius:20px;padding:2px 10px;font-size:11px;font-family:'Cinzel',serif}}
.badge-never{{background:var(--surface2);color:var(--text3);border:1px solid var(--surface3);
  border-radius:20px;padding:2px 10px;font-size:11px;font-family:'Cinzel',serif}}
.tab-bar-chart{{display:flex;flex-direction:column;gap:8px}}
.bar-row{{display:flex;align-items:center;gap:12px}}
.bar-label{{font-size:13px;color:var(--text2);width:100px;flex-shrink:0;text-align:right}}
.bar-track{{flex:1;height:8px;background:var(--surface2);border-radius:4px;overflow:hidden}}
.bar-fill{{height:100%;background:var(--teal);border-radius:4px;transition:width 0.4s}}
.bar-count{{font-size:12px;color:var(--text3);width:36px;text-align:right}}
.activity-list{{list-style:none}}
.activity-item{{display:flex;gap:12px;align-items:flex-start;padding:10px 0;border-bottom:1px solid var(--surface2)}}
.activity-dot{{width:8px;height:8px;border-radius:50%;background:var(--teal);flex-shrink:0;margin-top:5px}}
.activity-text{{font-size:13px;color:var(--text2)}}
.activity-ts{{font-size:11px;color:var(--text3);margin-top:2px}}
.empty{{font-size:13px;color:var(--text3);font-style:italic;padding:16px 0}}
.info-box{{background:var(--surface);border:1px solid var(--surface3);border-radius:var(--radius);
  padding:14px 16px;font-size:13px;color:var(--text3);margin-top:16px;line-height:1.6}}
</style>
</head>
<body>
<div class="header">
  <div class="header-left">
    <h1>★ Admin Dashboard</h1>
    <p>Icewind Dale · Rime of the Frostmaiden · Solo visible para Adrik</p>
  </div>
  <div class="header-links">
    <a href="../hub/index.html">← Party Hub</a>
    <a href="#" onclick="logout();return false">Cerrar sesión</a>
  </div>
</div>

<div class="content">
  <div class="section-label">Resumen</div>
  <div class="stats-grid" id="statsGrid"><!-- JS --></div>

  <div class="section-label">Estado de la Party</div>
  <table class="char-table">
    <thead>
      <tr>
        <th>Personaje</th>
        <th>Clase</th>
        <th>JSON subido</th>
        <th>Último login</th>
        <th>Visitas</th>
      </tr>
    </thead>
    <tbody id="charTableBody"><!-- JS --></tbody>
  </table>

  <div class="section-label">Tabs más visitadas</div>
  <div class="tab-bar-chart" id="tabChart"><!-- JS --></div>

  <div class="section-label">Actividad reciente</div>
  <ul class="activity-list" id="activityList"><!-- JS --></ul>

  <div class="info-box">
    ⓘ Los datos de analytics se almacenan en el navegador de cada jugador (localStorage).
    Esta pantalla muestra la actividad registrada en <strong>este dispositivo</strong>.
    Para ver las estadísticas de todos los jugadores, cada uno debe visitar su página desde este dispositivo, o compartirte su actividad.
  </div>
</div>

<script>
const _SK = 'icewind_session';
const _AK = 'icewind_analytics';
const PARTY = [{party_rows}
];

function _getSess(){{try{{return JSON.parse(localStorage.getItem(_SK));}}catch{{return null;}}}}
function logout(){{localStorage.removeItem(_SK);location.href='../index.html';}}

// Auth check
(function(){{
  const s=_getSess();
  if(!s||!s.admin){{location.replace('../index.html');}}
}})();

function relTime(ts){{
  if(!ts) return '—';
  const diff=Date.now()-ts;
  const m=Math.floor(diff/60000);
  if(m<1) return 'hace un momento';
  if(m<60) return 'hace '+m+' min';
  const h=Math.floor(m/60);
  if(h<24) return 'hace '+h+'h';
  const d=Math.floor(h/24);
  return 'hace '+d+' día'+(d>1?'s':'');
}}

function fmtDate(ts){{
  if(!ts) return '—';
  return new Date(ts).toLocaleDateString('es-CL',{{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'}});
}}

window.addEventListener('DOMContentLoaded', function(){{
  const events = JSON.parse(localStorage.getItem(_AK)||'[]');

  // ── Stats summary ──
  const loginsToday = events.filter(e=>e.t==='login'&&Date.now()-e.ts<86400000).length;
  const uploads     = PARTY.filter(p=>localStorage.getItem('upload_char_'+p.slug)==='1').length;
  const totalVisits = events.filter(e=>e.t==='visit').length;
  const grid = document.getElementById('statsGrid');
  grid.innerHTML =
    `<div class="stat-card"><span class="stat-val">${{loginsToday}}</span><span class="stat-lbl">Logins hoy</span></div>`+
    `<div class="stat-card"><span class="stat-val">${{uploads}}/6</span><span class="stat-lbl">JSON subidos</span></div>`+
    `<div class="stat-card"><span class="stat-val">${{totalVisits}}</span><span class="stat-lbl">Visitas totales</span></div>`+
    `<div class="stat-card"><span class="stat-val">${{events.length}}</span><span class="stat-lbl">Eventos registrados</span></div>`;

  // ── Character table ──
  const visitsBySlug = {{}};
  events.filter(e=>e.t==='visit').forEach(e=>{{
    const s=e.d?.slug||'';
    visitsBySlug[s]=(visitsBySlug[s]||0)+1;
  }});
  const tbody = document.getElementById('charTableBody');
  tbody.innerHTML = PARTY.map(p=>{{
    const hasUpload = localStorage.getItem('upload_char_'+p.slug)==='1';
    const lastUp    = localStorage.getItem('last_upload_'+p.slug);
    const lastLog   = localStorage.getItem('last_login_'+p.slug);
    const visits    = visitsBySlug[p.slug]||0;
    const upBadge   = hasUpload
      ? `<span class="badge-yes">✓ Sí</span> <span style="font-size:11px;color:var(--text3)">${{fmtDate(parseInt(lastUp))}}</span>`
      : '<span class="badge-no">✗ No</span>';
    return `<tr>
      <td><span class="char-name" style="color:${{p.color}}">${{p.name}}</span></td>
      <td style="font-size:13px;color:var(--text2)">${{p.class_str}}</td>
      <td>${{upBadge}}</td>
      <td style="font-size:13px;color:var(--text2)">${{relTime(parseInt(lastLog))}}</td>
      <td style="font-family:'Cinzel',serif;color:var(--gold2)">${{visits}}</td>
    </tr>`;
  }}).join('');

  // ── Tab chart ──
  const tabCounts = {{}};
  const tabLabels = {{
    'combate':'⚔ Combate','hechizos':'✦ Hechizos','habilidades':'◈ Habilidades',
    'personaje':'📋 Personaje','mapa':'🗺 Mapa','sesion':'📖 Sesión',
    'personajes':'👥 Personajes','misiones':'🔍 Misiones','mundo':'🌍 Mundo'
  }};
  events.filter(e=>e.t==='tab').forEach(e=>{{
    const t=e.d?.tab||'';
    tabCounts[t]=(tabCounts[t]||0)+1;
  }});
  const sortedTabs = Object.entries(tabCounts).sort((a,b)=>b[1]-a[1]).slice(0,8);
  const maxTab = sortedTabs[0]?.[1]||1;
  const chartEl = document.getElementById('tabChart');
  if(sortedTabs.length===0){{
    chartEl.innerHTML='<div class="empty">Sin datos de tabs aún.</div>';
  }} else {{
    chartEl.innerHTML = sortedTabs.map(([tab,cnt])=>
      `<div class="bar-row">
        <span class="bar-label">${{tabLabels[tab]||tab}}</span>
        <div class="bar-track"><div class="bar-fill" style="width:${{Math.round(cnt/maxTab*100)}}%"></div></div>
        <span class="bar-count">${{cnt}}</span>
      </div>`
    ).join('');
  }}

  // ── Activity log ──
  const recent = [...events].reverse().slice(0,20);
  const listEl = document.getElementById('activityList');
  const typeLabel = {{login:'Inició sesión',visit:'Visitó página',tab:'Cambió tab',upload:'Subió JSON'}};
  if(recent.length===0){{
    listEl.innerHTML='<li class="empty">Sin actividad registrada aún.</li>';
  }} else {{
    listEl.innerHTML = recent.map(e=>{{
      const action=typeLabel[e.t]||e.t;
      const who=e.d?.slug||'';
      const tab=e.d?.tab?' ('+e.d.tab+')':'';
      return `<li class="activity-item">
        <div class="activity-dot"></div>
        <div>
          <div class="activity-text"><strong>${{who}}</strong> ${{action}}${{tab}}</div>
          <div class="activity-ts">${{fmtDate(e.ts)}}</div>
        </div>
      </li>`;
    }}).join('');
  }}
}});
</script>
</body>
</html>'''

    admin_dir = os.path.join(BASE, "dist", "admin")
    os.makedirs(admin_dir, exist_ok=True)
    out = os.path.join(admin_dir, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ dist/admin/index.html (dashboard admin)")


# ── Main ───────────────────────────────────────────────────────────────────────
print("⟳ Generando compendium multi-jugador...")
build_login()
build_hub()
build_admin()
for member in PARTY:
    build_character_page(member)

sessions_count = len(sessions_data.get("sessions", [])) if sessions_data else 0
warns = char.get("warnings", []) if char else []
print()
print(f"✅ Sitio generado · {len(PARTY)} personajes · {sessions_count} sesiones")
if char:
    print(f"   {char.get('name')} — Nivel {char.get('level')} {char.get('class')}")
if warns:
    print(f"   ⚠  {len(warns)} advertencia(s) de Foundry en Adrik")
print(f"   🔐 Login: dist/index.html")
print(f"   ★  Admin: dist/admin/index.html (solo Adrik · contraseña: selune)")
