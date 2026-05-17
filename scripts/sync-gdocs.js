#!/usr/bin/env node
/**
 * sync-gdocs.js
 * Fetches the story/session Google Doc and writes to data/sessions.json
 * 
 * Setup:
 *   1. Create a Google Cloud project
 *   2. Enable Google Docs API
 *   3. Create a Service Account, download credentials JSON
 *   4. Share your Google Doc with the service account email
 *   5. Set GOOGLE_DOC_ID and GOOGLE_APPLICATION_CREDENTIALS in .env
 *
 * Usage: node scripts/sync-gdocs.js
 */

require('dotenv').config();
const fs = require('fs');
const path = require('path');
const { google } = require('googleapis');

const DOC_ID = process.env.GOOGLE_DOC_ID;
const CREDENTIALS = process.env.GOOGLE_APPLICATION_CREDENTIALS;

if (!DOC_ID || !CREDENTIALS) {
  console.error('❌ Missing GOOGLE_DOC_ID or GOOGLE_APPLICATION_CREDENTIALS in .env');
  console.error('   See .env.example for setup instructions.');
  process.exit(1);
}

async function fetchDoc() {
  const auth = new google.auth.GoogleAuth({
    keyFile: CREDENTIALS,
    scopes: ['https://www.googleapis.com/auth/documents.readonly'],
  });

  const docs = google.docs({ version: 'v1', auth });
  const res = await docs.documents.get({ documentId: DOC_ID });
  const doc = res.data;

  // Extract text from document body
  const content = doc.body.content;
  const sessions = [];
  let currentSession = null;

  for (const block of content) {
    if (!block.paragraph) continue;
    const text = block.paragraph.elements
      ?.map(e => e.textRun?.content ?? '')
      .join('')
      .trim();
    if (!text) continue;

    const style = block.paragraph.paragraphStyle?.namedStyleType ?? '';

    // Detect session headers (Heading 1 or "Sesión" in text)
    if (style === 'HEADING_1' || (style === 'HEADING_2' && text.toLowerCase().includes('sesión'))) {
      if (currentSession) sessions.push(currentSession);
      currentSession = { title: text, date: null, content: [] };
    } else if (currentSession) {
      // Look for date patterns
      const dateMatch = text.match(/\d{1,2}\s+de\s+\w+|\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4}/i);
      if (dateMatch && !currentSession.date) {
        currentSession.date = dateMatch[0];
      }
      currentSession.content.push(text);
    }
  }
  if (currentSession) sessions.push(currentSession);

  const output = {
    docTitle: doc.title,
    lastSynced: new Date().toISOString(),
    sessions,
  };

  const outputPath = path.join(__dirname, '../data/sessions.json');
  fs.writeFileSync(outputPath, JSON.stringify(output, null, 2));
  console.log(`✅ Synced "${doc.title}" → ${sessions.length} sessions found`);
  sessions.forEach((s, i) => console.log(`   ${i + 1}. ${s.title} (${s.content.length} paragraphs)`));
}

fetchDoc().catch(err => {
  console.error('❌ Error fetching Google Doc:', err.message);
  process.exit(1);
});
