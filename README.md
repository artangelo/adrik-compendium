# Adrik Compendium

Hoja de referencia D&D para la campaña **Icewind Dale: Rime of the Frostmaiden**.

Party Hub con páginas individuales por personaje. Generado automáticamente desde Foundry VTT + Google Docs + notas de sesión.

## Personajes

| Personaje | Clase | Raza |
|-----------|-------|------|
| Adrik Frostbeard | Clérigo · Dominio Crepúsculo | Enano de Colina |
| Draxus | Fighter | Dragonborn Plateado |
| Sven | Rogue | Elfo |
| Teska | Bardo | Tiefling |
| Elian | Mago | Humano |
| Yankavic | Paladín | Semielfo |

## Flujo semanal

```bash
# Actualizar personaje desde Foundry VTT + rebuild + publicar
./update.sh ~/Downloads/fvtt-Actor-adrik-*.json
git add -A && git commit -m "Sesión N" && git push
```

## Estructura

```
scripts/
  parse-foundry.py   # Foundry VTT JSON → data/character.json
  sync-gdocs.py      # Google Doc → data/sessions.json
  build.py           # Genera dist/ completo (hub + 6 personajes)
data/
  character.json     # Stats de Adrik (generado)
  world.json         # NPCs, lugares, quests — editar manualmente o via Claude
  sessions.json      # Historial de sesiones (generado)
dist/                # Sitio estático publicado en GitHub Pages
  index.html         # Party Hub
  adrik/index.html   # Página de Adrik (completa)
  {slug}/index.html  # Páginas de otros personajes (upload JSON)
  assets/portraits/  # Retratos: adrik.jpg, draxus.jpg, sven.jpg,
                     #           teska.jpg, elian.jpg, yankavic.jpg
```

## Actualizar NPCs, lugares o quests

Pégale la transcripción de Granola a Claude Code y pídele:
> "actualiza data/world.json con lo que pasó esta sesión"

Luego: `python3 scripts/build.py && git add -A && git commit -m "..." && git push`

## Requisitos

Python 3.9+. Sin dependencias externas.
