# Adrik Compendium

Sitio de referencia para Adrik Frostbeard — Clérigo Dominio Crepúsculo — Icewind Dale: Rime of the Frostmaiden.

Auto-generado desde Foundry VTT y Google Docs.

## Requisitos

- Node.js 18+
- npm

```bash
npm install
```

## Flujo de trabajo

### Después de cada subida de nivel o cambio en Foundry

1. En Foundry: clic derecho sobre el actor → **Export Data** → guarda el JSON
2. Ejecuta:

```bash
npm run update-char ruta/al/fvtt-Actor-adrik-*.json
npm run build
```

Listo. El archivo `dist/index.html` está actualizado.

### Después de cada sesión (sincronizar Google Docs)

```bash
npm run full-sync
```

Esto hace:
1. Descarga el Google Doc con el historial de sesiones
2. Regenera el sitio con las sesiones actualizadas

### Solo regenerar el HTML (sin cambios en datos)

```bash
npm run build
```

## Setup Google Docs (una sola vez)

1. Ve a [Google Cloud Console](https://console.cloud.google.com)
2. Crea un proyecto nuevo
3. Activa la API **Google Docs API**
4. Ve a **IAM & Admin → Service Accounts**
5. Crea una service account, descarga el JSON de credenciales
6. Guárdalo en `credentials/google-service-account.json`
7. Abre tu Google Doc → Compartir → Añade el email de la service account con permiso de **lectura**
8. Copia `.env.example` a `.env` y completa los valores:

```bash
cp .env.example .env
# edita .env con tu GOOGLE_DOC_ID
```

## Estructura de archivos

```
adrik-compendium/
├── scripts/
│   ├── parse-foundry.js   # Foundry JSON → data/character.json
│   ├── sync-gdocs.js      # Google Docs → data/sessions.json
│   └── build.js           # data/*.json → dist/index.html
├── data/
│   ├── character.json     # Auto-generado por parse-foundry.js
│   ├── sessions.json      # Auto-generado por sync-gdocs.js
│   └── world.json         # NPCs, lugares, quests — editar manualmente o via Claude
├── templates/
│   └── main.html          # Template HTML con placeholders
├── dist/
│   └── index.html         # Sitio final — abrir en browser
├── .env                   # Credenciales (no subir a git)
└── .env.example           # Ejemplo de .env
```

## Actualizar NPCs, lugares, quests

Edita `data/world.json` directamente, o pégale la transcripción a Claude y pídele que lo actualice.

Luego: `npm run build`
