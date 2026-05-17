#!/usr/bin/env node
/**
 * parse-foundry.js
 * Usage: node scripts/parse-foundry.js path/to/fvtt-Actor-*.json
 * Reads a Foundry VTT actor export and writes data/character.json
 */

const fs = require('fs');
const path = require('path');

const inputFile = process.argv[2];
if (!inputFile) {
  console.error('Usage: node scripts/parse-foundry.js <foundry-export.json>');
  process.exit(1);
}

const raw = JSON.parse(fs.readFileSync(inputFile, 'utf8'));
const sys = raw.system;

// --- Abilities ---
const abilityKeys = { str: 'FUE', dex: 'DES', con: 'CON', int: 'INT', wis: 'SAB', cha: 'CAR' };
const abilities = {};
for (const [key, label] of Object.entries(abilityKeys)) {
  const val = sys.abilities[key]?.value ?? 10;
  const mod = Math.floor((val - 10) / 2);
  abilities[key] = { value: val, mod, modStr: mod >= 0 ? `+${mod}` : `${mod}`, label, proficient: sys.abilities[key]?.proficient ?? 0 };
}

// --- Skills with proficiency ---
const skillMap = {
  acr: { name: 'Acrobatics', ability: 'dex' },
  ani: { name: 'Animal Handling', ability: 'wis' },
  arc: { name: 'Arcana', ability: 'int' },
  ath: { name: 'Athletics', ability: 'str' },
  dec: { name: 'Deception', ability: 'cha' },
  his: { name: 'History', ability: 'int' },
  ins: { name: 'Insight', ability: 'wis' },
  itm: { name: 'Intimidation', ability: 'cha' },
  inv: { name: 'Investigation', ability: 'int' },
  med: { name: 'Medicine', ability: 'wis' },
  nat: { name: 'Nature', ability: 'int' },
  prc: { name: 'Perception', ability: 'wis' },
  prf: { name: 'Performance', ability: 'cha' },
  per: { name: 'Persuasion', ability: 'cha' },
  rel: { name: 'Religion', ability: 'int' },
  slt: { name: 'Sleight of Hand', ability: 'dex' },
  ste: { name: 'Stealth', ability: 'dex' },
  sur: { name: 'Survival', ability: 'wis' },
};

// Get proficiency bonus from level
const classItem = raw.items.find(i => i.type === 'class');
const level = classItem?.system?.levels ?? 1;
const profBonus = Math.ceil(1 + level / 4);

const skills = {};
for (const [key, info] of Object.entries(skillMap)) {
  const sk = sys.skills[key];
  const abilMod = abilities[info.ability].mod;
  const profValue = sk?.value ?? 0; // 0=none, 1=prof, 2=expertise
  const bonus = abilMod + (profValue === 2 ? profBonus * 2 : profValue === 1 ? profBonus : 0);
  skills[key] = {
    name: info.name,
    ability: info.ability,
    proficient: profValue > 0,
    expertise: profValue === 2,
    bonus,
    bonusStr: bonus >= 0 ? `+${bonus}` : `${bonus}`,
  };
}

// --- HP ---
const hp = sys.attributes?.hp ?? {};

// --- Class & Subclass ---
const subclassItem = raw.items.find(i => i.type === 'subclass');
const className = classItem?.name ?? 'Unknown';
const subclassName = subclassItem?.name ?? '';

// --- Currency ---
const currency = sys.currency ?? {};

// --- Inspiration ---
const inspiration = sys.attributes?.inspiration ?? false;

// --- Exhaustion ---
const exhaustion = sys.attributes?.exhaustion ?? 0;

// --- Spells ---
const spells = raw.items
  .filter(i => i.type === 'spell')
  .map(i => ({
    name: i.name,
    level: i.system?.level ?? 0,
    prepMode: i.system?.preparation?.mode ?? 'prepared',
    school: i.system?.school ?? '',
  }))
  .sort((a, b) => a.level - b.level);

// --- Spell slots ---
const spellSlots = {};
for (let lvl = 1; lvl <= 9; lvl++) {
  const slot = sys.spells?.[`spell${lvl}`] ?? {};
  if (slot.max || slot.override || slot.value) {
    spellSlots[lvl] = { value: slot.value ?? 0, max: slot.override ?? slot.max ?? 0 };
  }
}

// --- Equipment ---
const equipmentTypes = ['weapon', 'equipment', 'consumable', 'tool', 'backpack', 'loot'];
const equipment = raw.items
  .filter(i => equipmentTypes.includes(i.type))
  .map(i => ({
    name: i.name,
    type: i.type,
    quantity: i.system?.quantity ?? 1,
    equipped: i.system?.equipped ?? false,
  }));

// --- Active effects ---
const effects = raw.items
  .filter(i => i.type === 'feat' || i.type === 'class' || i.type === 'subclass')
  .map(i => i.name);

const activeConditions = (raw.effects ?? [])
  .filter(e => !e.disabled)
  .map(e => e.name);

// --- Saving throws ---
const savingThrows = {};
for (const [key, ab] of Object.entries(abilities)) {
  const proficient = ab.proficient;
  const bonus = ab.mod + (proficient ? profBonus : 0);
  savingThrows[key] = { bonus, bonusStr: bonus >= 0 ? `+${bonus}` : `${bonus}`, proficient: proficient > 0 };
}

// --- Warnings ---
const warnings = [];
if (!hp.max) warnings.push({ type: 'error', msg: 'HP máximo no configurado en Foundry — ve a la hoja de personaje y configura manualmente.' });
if (Object.keys(spellSlots).length === 0) warnings.push({ type: 'error', msg: 'Spell slots no configurados en Foundry — revisa la pestaña de hechizos.' });
const hasDomainSpells = spells.some(s => ['Sleep', 'Faerie Fire'].includes(s.name));
if (!hasDomainSpells) warnings.push({ type: 'warn', msg: 'Los hechizos de dominio (Sleep, Faerie Fire) no están agregados en Foundry.' });
if (activeConditions.includes('Concentrating: Bless')) warnings.push({ type: 'info', msg: 'Concentrating: Bless está activo como efecto — desactívalo si hiciste descanso largo.' });

const armor = equipment.find(e => e.name.toLowerCase().includes('scale mail') || e.name.toLowerCase().includes('chain mail') || e.name.toLowerCase().includes('plate'));
if (armor?.name?.toLowerCase().includes('scale mail')) {
  warnings.push({ type: 'warn', msg: 'Tienes Scale Mail (CA 15 con escudo). Considera cambiar a Chain Mail (CA 18) — tienes proficiencia en armadura pesada por Twilight Domain.' });
}

// --- Output ---
const character = {
  name: raw.name,
  class: className,
  subclass: subclassName,
  level,
  background: raw.items.find(i => i.type === 'background')?.name ?? 'Outlander',
  race: raw.items.find(i => i.type === 'race')?.name ?? 'Dwarf (Hill)',
  deity: 'Selûne',
  proficiencyBonus: profBonus,
  abilities,
  savingThrows,
  skills,
  hp,
  spellSaveDC: 8 + profBonus + abilities.wis.mod,
  spellAttackBonus: profBonus + abilities.wis.mod,
  inspiration,
  exhaustion,
  currency,
  spells,
  spellSlots,
  equipment,
  activeConditions,
  warnings,
  lastUpdated: new Date().toISOString(),
};

const outputPath = path.join(__dirname, '../data/character.json');
fs.writeFileSync(outputPath, JSON.stringify(character, null, 2));
console.log(`✅ Character data written to ${outputPath}`);
console.log(`   Level ${level} ${className} (${subclassName})`);
console.log(`   HP: ${hp.value ?? '?'}/${hp.max ?? 'NOT SET'} | Inspiration: ${inspiration}`);
if (warnings.length > 0) {
  console.log(`\n⚠️  ${warnings.length} warning(s):`);
  warnings.forEach(w => console.log(`   [${w.type.toUpperCase()}] ${w.msg}`));
}
