#!/usr/bin/env python3
"""
parse-foundry.py
Reads a Foundry VTT actor export and writes data/character.json

Usage: python3 scripts/parse-foundry.py path/to/fvtt-Actor-adrik-*.json
"""

import json
import sys
import os
import math
from datetime import datetime

def fmt(n):
    return f"+{n}" if n >= 0 else str(n)

def mod(value):
    return math.floor((value - 10) / 2)

if len(sys.argv) < 2:
    print("Usage: python3 scripts/parse-foundry.py <foundry-export.json>")
    sys.exit(1)

input_file = sys.argv[1]
if not os.path.exists(input_file):
    print(f"❌ File not found: {input_file}")
    sys.exit(1)

with open(input_file, encoding="utf-8") as f:
    raw = json.load(f)

sys_data = raw.get("system", {})

# --- Abilities ---
ability_keys = {"str": "FUE", "dex": "DES", "con": "CON", "int": "INT", "wis": "SAB", "cha": "CAR"}
abilities = {}
for key, label in ability_keys.items():
    val = sys_data.get("abilities", {}).get(key, {}).get("value", 10)
    m = mod(val)
    prof = sys_data.get("abilities", {}).get(key, {}).get("proficient", 0)
    abilities[key] = {"value": val, "mod": m, "modStr": fmt(m), "label": label, "proficient": prof}

# --- Level & Proficiency ---
class_item = next((i for i in raw.get("items", []) if i.get("type") == "class"), None)
level = class_item.get("system", {}).get("levels", 1) if class_item else 1
prof_bonus = math.ceil(1 + level / 4)

# --- Skills ---
skill_map = {
    "acr": ("Acrobatics", "dex"), "ani": ("Animal Handling", "wis"),
    "arc": ("Arcana", "int"), "ath": ("Athletics", "str"),
    "dec": ("Deception", "cha"), "his": ("History", "int"),
    "ins": ("Insight", "wis"), "itm": ("Intimidation", "cha"),
    "inv": ("Investigation", "int"), "med": ("Medicine", "wis"),
    "nat": ("Nature", "int"), "prc": ("Perception", "wis"),
    "prf": ("Performance", "cha"), "per": ("Persuasion", "cha"),
    "rel": ("Religion", "int"), "slt": ("Sleight of Hand", "dex"),
    "ste": ("Stealth", "dex"), "sur": ("Survival", "wis"),
}
skills = {}
for key, (name, ability) in skill_map.items():
    sk = sys_data.get("skills", {}).get(key, {})
    a_mod = abilities[ability]["mod"]
    prof_val = sk.get("value", 0)
    bonus = a_mod + (prof_bonus * 2 if prof_val == 2 else prof_bonus if prof_val == 1 else 0)
    skills[key] = {
        "name": name, "ability": ability,
        "proficient": prof_val > 0, "expertise": prof_val == 2,
        "bonus": bonus, "bonusStr": fmt(bonus),
    }

# --- HP ---
hp = sys_data.get("attributes", {}).get("hp", {})

# --- Class & Subclass ---
subclass_item = next((i for i in raw.get("items", []) if i.get("type") == "subclass"), None)
class_name = class_item.get("name", "Unknown") if class_item else "Unknown"
subclass_name = subclass_item.get("name", "") if subclass_item else ""

# --- Background & Race ---
bg_item = next((i for i in raw.get("items", []) if i.get("type") == "background"), None)
race_item = next((i for i in raw.get("items", []) if i.get("type") == "race"), None)
background = bg_item.get("name", "Outlander") if bg_item else "Outlander"
race = race_item.get("name", "Dwarf (Hill)") if race_item else "Dwarf (Hill)"

# --- Currency, Inspiration, Exhaustion ---
currency = sys_data.get("currency", {})
inspiration = sys_data.get("attributes", {}).get("inspiration", False)
exhaustion = sys_data.get("attributes", {}).get("exhaustion", 0)

# --- Spells ---
spells = []
for i in raw.get("items", []):
    if i.get("type") != "spell":
        continue
    spells.append({
        "name": i.get("name", ""),
        "level": i.get("system", {}).get("level", 0),
        "prepMode": i.get("system", {}).get("preparation", {}).get("mode", "prepared"),
        "school": i.get("system", {}).get("school", ""),
    })
spells.sort(key=lambda x: x["level"])

# --- Spell Slots ---
spell_slots = {}
raw_spells = sys_data.get("spells", {})
for lvl in range(1, 10):
    slot = raw_spells.get(f"spell{lvl}", {})
    max_val = slot.get("override") or slot.get("max") or 0
    cur_val = slot.get("value") or 0
    if max_val or cur_val:
        spell_slots[lvl] = {"value": cur_val, "max": max_val}

# --- Equipment ---
equipment_types = {"weapon", "equipment", "consumable", "tool", "backpack", "loot"}
equipment = []
for i in raw.get("items", []):
    if i.get("type") not in equipment_types:
        continue
    equipment.append({
        "name": i.get("name", ""),
        "type": i.get("type", ""),
        "quantity": i.get("system", {}).get("quantity", 1),
        "equipped": i.get("system", {}).get("equipped", False),
    })

# --- Saving Throws ---
saving_throws = {}
for key, ab in abilities.items():
    prof = ab["proficient"]
    bonus = ab["mod"] + (prof_bonus if prof else 0)
    saving_throws[key] = {"bonus": bonus, "bonusStr": fmt(bonus), "proficient": prof > 0}

# --- Active Conditions ---
active_conditions = [e.get("name", "") for e in raw.get("effects", []) if not e.get("disabled", True)]

# --- Derived Stats ---
spell_save_dc = 8 + prof_bonus + abilities["wis"]["mod"]
spell_attack_bonus = prof_bonus + abilities["wis"]["mod"]

# --- Warnings ---
warnings = []
if not hp.get("max"):
    warnings.append({"type": "error", "msg": "HP máximo no configurado en Foundry — configúralo manualmente en la hoja de personaje."})
if not spell_slots:
    warnings.append({"type": "error", "msg": "Spell slots no configurados en Foundry — revisa la pestaña de hechizos."})
domain_spells = {"Sleep", "Faerie Fire"}
has_domain = any(s["name"] in domain_spells for s in spells)
if not has_domain:
    warnings.append({"type": "warn", "msg": "Los hechizos de dominio (Sleep, Faerie Fire) no están agregados en Foundry."})
if any("scale mail" in e["name"].lower() for e in equipment):
    warnings.append({"type": "warn", "msg": "Tienes Scale Mail (CA 15). Considera cambiar a Chain Mail (CA 18) — tienes proficiencia en armadura pesada por Twilight Domain."})

# --- Build output ---
character = {
    "name": raw.get("name", ""),
    "class": class_name,
    "subclass": subclass_name,
    "level": level,
    "background": background,
    "race": race,
    "deity": "Selûne",
    "proficiencyBonus": prof_bonus,
    "abilities": abilities,
    "savingThrows": saving_throws,
    "skills": skills,
    "hp": hp,
    "spellSaveDC": spell_save_dc,
    "spellAttackBonus": spell_attack_bonus,
    "inspiration": inspiration,
    "exhaustion": exhaustion,
    "currency": currency,
    "spells": spells,
    "spellSlots": {str(k): v for k, v in spell_slots.items()},
    "equipment": equipment,
    "activeConditions": active_conditions,
    "warnings": warnings,
    "lastUpdated": datetime.now().isoformat(),
}

output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "character.json")
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(character, f, indent=2, ensure_ascii=False)

print(f"✅ Character data written to {output_path}")
print(f"   Level {level} {class_name} ({subclass_name})")
print(f"   HP: {hp.get('value','?')}/{hp.get('max','NOT SET')} | Inspiration: {inspiration}")
if warnings:
    print(f"\n⚠️  {len(warnings)} warning(s):")
    for w in warnings:
        print(f"   [{w['type'].upper()}] {w['msg']}")
