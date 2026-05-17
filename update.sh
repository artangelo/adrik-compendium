#!/bin/bash
# ─────────────────────────────────────────────────────────────
# update.sh — Flujo semanal para actualizar el compendium
# ─────────────────────────────────────────────────────────────
# Uso:
#   ./update.sh                         → solo rebuild
#   ./update.sh ~/Downloads/fvtt-*.json → actualiza personaje + rebuild
#   ./update.sh ~/Downloads/fvtt-*.json ABC123DOCID → personaje + Google Doc + rebuild
# ─────────────────────────────────────────────────────────────

set -e
cd "$(dirname "$0")"

FOUNDRY_JSON="$1"
GDOC_ID="$2"

echo "═══════════════════════════════════════════════"
echo " Adrik Compendium — Update"
echo "═══════════════════════════════════════════════"

# 1. Parse Foundry JSON (si se provee)
if [ -n "$FOUNDRY_JSON" ]; then
  echo ""
  echo "⟳ Parseando Foundry JSON..."
  python3 scripts/parse-foundry.py "$FOUNDRY_JSON"
elif [ ! -f data/character.json ]; then
  echo "❌ No hay data/character.json."
  echo "   Exporta tu actor desde Foundry y ejecuta:"
  echo "   ./update.sh ruta/al/fvtt-Actor-adrik-*.json"
  exit 1
fi

# 2. Sincronizar Google Docs (si se provee ID o está en .env)
if [ -n "$GDOC_ID" ]; then
  echo ""
  echo "⟳ Sincronizando Google Doc..."
  python3 scripts/sync-gdocs.py "$GDOC_ID"
elif [ -f .env ] && grep -q "GOOGLE_DOC_ID=" .env && [ "$(grep GOOGLE_DOC_ID= .env | cut -d= -f2)" != "" ]; then
  echo ""
  echo "⟳ Sincronizando Google Doc desde .env..."
  python3 scripts/sync-gdocs.py
fi

# 3. Build
echo ""
echo "⟳ Generando dist/index.html..."
python3 scripts/build.py

echo ""
echo "═══════════════════════════════════════════════"
echo "✅ Listo. Abriendo en el browser..."
echo "═══════════════════════════════════════════════"
open dist/index.html   # Party Hub
