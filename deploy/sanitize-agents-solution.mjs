#!/usr/bin/env node
// sanitize-agents-solution.mjs — turn an exported Copilot Studio solution zip into
// an AGENTS-ONLY solution: strip every custom connector, every connection
// reference, and every connection-bound tool component, leaving only the bots
// and their non-connector botcomponents (skills, files, connected-agent tools).
//
// WHY (the two-solution split):
//   We ship the BlastBox demo as two solutions the user imports in order:
//     1. a connectors solution (the custom-code MCP connectors), then
//     2. this agents-only solution (the bots + skills).
//   Keeping connectors out of the agents solution avoids the connector compile /
//   capacity problems bleeding into the agent import, and lets the connectors be
//   versioned and re-imported independently. The agents solution must therefore
//   carry NO connectors and NO connection references, or import fails on missing
//   dependencies (a clean target has no such connection references, and an MCP tool
//   left pointing at a non-existent connref resolves to null -> NRE).
//
// WHAT IT REMOVES (generically, not by hard-coded name/id):
//   - every `<RootComponent type="372" .../>` (custom connector) in solution.xml
//   - the whole `Connector/` (or `Connectors/`) folder
//   - every connection-bound tool botcomponent (`kind: McpTool`,
//     `kind: ConnectorTool`, or the older `InvokeExternalAgentTaskAction`
//     TaskDialog form)
//   - connection-reference artifacts: `Assets/botcomponent_connectionreferenceset.xml`
//     and any `connectionreferences/` folder
//   - the removed parts' `<Override>` entries in `[Content_Types].xml`
//   It then resets `<MissingDependencies>` to an EMPTY (but present) element.
//
// WHAT IT KEEPS: bots, skills (InlineAgentSkill), bundled files, connected-agent
//   tools (ConnectedAgentTool) and everything else.
//
// After importing the agents solution, the connections already exist (from the
// connectors solution + one no-auth connection each), so the only manual step is
// re-adding each agent's connector-bound tools in the Copilot Studio portal.
//
// Usage:
//   node deploy/sanitize-agents-solution.mjs <input.zip> [output.zip]
// If output is omitted, writes alongside input with an `-agentsonly` suffix.

import { spawnSync } from 'node:child_process';
import { mkdtempSync, existsSync, readFileSync, writeFileSync, rmSync, readdirSync, statSync } from 'node:fs';
import { join, basename, resolve } from 'node:path';
import { tmpdir } from 'node:os';

const C = { g: '\x1b[32m', y: '\x1b[33m', r: '\x1b[31m', d: '\x1b[2m', x: '\x1b[0m' };
const ok = (m) => console.log(`${C.g}[ok]${C.x} ${m}`);
const warn = (m) => console.log(`${C.y}[warn]${C.x} ${m}`);
const log = (m) => console.log(`${C.d}==>${C.x} ${m}`);
const die = (m) => { console.error(`${C.r}[error]${C.x} ${m}`); process.exit(1); };

function sh(cmd, args, opts = {}) {
  const r = spawnSync(cmd, args, { encoding: 'utf8', maxBuffer: 256 * 1024 * 1024, ...opts });
  if (r.status !== 0) die(`${cmd} ${args.join(' ')} failed:\n${r.stderr || r.stdout}`);
  return r.stdout || '';
}

const inputArg = process.argv[2];
if (!inputArg) die('usage: node deploy/sanitize-agents-solution.mjs <input.zip> [output.zip]');
const input = resolve(inputArg);
if (!existsSync(input)) die(`input zip not found: ${input}`);
const output = resolve(process.argv[3] || input.replace(/\.zip$/i, '') + '-agentsonly.zip');

const work = mkdtempSync(join(tmpdir(), 'sanitize-agents-'));
try {
  log(`Unpacking ${basename(input)}`);
  sh('unzip', ['-o', '-q', input, '-d', work]);

  const bcRoot = join(work, 'botcomponents');
  if (!existsSync(bcRoot)) die('no botcomponents/ folder in solution — is this a Copilot Studio solution zip?');

  // 1. Remove connection-bound tool components. Their `data` declares
  //    `kind: McpTool`, `kind: ConnectorTool`, or an
  //    `InvokeExternalAgentTaskAction` (older TaskDialog form). They bind a
  //    connection reference and are re-added in the portal after import. Skills
  //    (InlineAgentSkill), bundled files and connected-agent tools
  //    (ConnectedAgentTool) are left untouched.
  const removedComponents = [];
  for (const name of readdirSync(bcRoot)) {
    const dir = join(bcRoot, name);
    if (!statSync(dir).isDirectory()) continue;
    const dataPath = join(dir, 'data');
    if (!existsSync(dataPath)) continue;
    const data = readFileSync(dataPath, 'utf8');
    const isConnectionBoundTool =
      /^\s*kind:\s*(?:McpTool|ConnectorTool)\s*$/m.test(data)
      || /InvokeExternalAgentTaskAction/.test(data);
    if (isConnectionBoundTool) {
      rmSync(dir, { recursive: true, force: true });
      removedComponents.push(name);
    }
  }
  if (!removedComponents.length) warn('no connection-bound tool components found (already connection-free?)');
  else { log(`Removed ${removedComponents.length} connection-bound tool component(s):`); removedComponents.forEach((n) => console.log(`     - ${n}`)); }

  // 2. Remove the connector folder(s) entirely (the custom connector definitions
  //    and inline code blobs). Match `Connector` or `Connectors`, case-insensitive.
  let connectorFolderRemoved = false;
  for (const name of readdirSync(work)) {
    if (/^connectors?$/i.test(name) && statSync(join(work, name)).isDirectory()) {
      rmSync(join(work, name), { recursive: true, force: true });
      ok(`removed ${name}/ (custom connector definitions)`);
      connectorFolderRemoved = true;
    }
  }
  if (!connectorFolderRemoved) warn('no Connector/ folder found — nothing to remove there');

  // 3. Remove connection-reference artifacts: the association manifest and any
  //    connectionreferences/ folder.
  const assets = join(work, 'Assets');
  const assocFile = join(assets, 'botcomponent_connectionreferenceset.xml');
  if (existsSync(assocFile)) {
    rmSync(assocFile, { force: true });
    ok('removed Assets/botcomponent_connectionreferenceset.xml');
    if (existsSync(assets) && readdirSync(assets).length === 0) rmSync(assets, { recursive: true, force: true });
  }
  for (const name of readdirSync(work)) {
    if (/^connectionreferences?$/i.test(name) && statSync(join(work, name)).isDirectory()) {
      rmSync(join(work, name), { recursive: true, force: true });
      ok(`removed ${name}/ (connection references)`);
    }
  }

  // 4. Edit solution.xml: drop every custom-connector RootComponent (type 372)
  //    and any connection-reference RootComponent, then reset MissingDependencies.
  const solXml = ['solution.xml', 'Solution.xml'].map((f) => join(work, f)).find(existsSync);
  if (solXml) {
    let s = readFileSync(solXml, 'utf8');
    const before = s;

    // 4a. Remove custom connector root components (component type 372).
    const connectorRoots = (s.match(/<RootComponent\b[^>]*\btype="372"[^>]*\/>\s*/g) || []);
    s = s.replace(/<RootComponent\b[^>]*\btype="372"[^>]*\/>\s*/g, '');
    // 4b. Remove connection-reference root components (component type 10122) if any.
    const connrefRoots = (s.match(/<RootComponent\b[^>]*\btype="10122"[^>]*\/>\s*/g) || []);
    s = s.replace(/<RootComponent\b[^>]*\btype="10122"[^>]*\/>\s*/g, '');
    if (connectorRoots.length) ok(`removed ${connectorRoots.length} custom-connector root component(s)`);
    if (connrefRoots.length) ok(`removed ${connrefRoots.length} connection-reference root component(s)`);

    // 4c. Reset <MissingDependencies>...</MissingDependencies> to an EMPTY element.
    //     The element MUST stay present (deleting it entirely makes import fail with
    //     a null-reference error). A known-good export keeps it empty.
    if (/<MissingDependencies>[\s\S]*?<\/MissingDependencies>/.test(s)) {
      s = s.replace(/<MissingDependencies>[\s\S]*?<\/MissingDependencies>/, '<MissingDependencies />');
      ok('reset <MissingDependencies /> to empty (element preserved)');
    } else if (!/<MissingDependencies\s*\/>/.test(s)) {
      s = s.replace(/(<\/RootComponents>\s*)/, `$1    <MissingDependencies />\n`);
      ok('inserted empty <MissingDependencies />');
    }

    if (s !== before) writeFileSync(solXml, s);
  } else warn('solution.xml not found at root — skipping RootComponents/MissingDependencies edits');

  // 5. Empty the <Connectors> block in customizations.xml. The connectors are
  //    declared a SECOND time here (each <Connector> points at the /Connector/*
  //    files we just deleted), so leaving it makes import fail with
  //    "Connector import: FAILURE: No file with that name found". Reset to an empty
  //    element, matching the other empty manifest sections.
  const custXml = ['customizations.xml', 'Customizations.xml'].map((f) => join(work, f)).find(existsSync);
  if (custXml) {
    let cx = readFileSync(custXml, 'utf8');
    const before = cx;
    const connectorBlocks = (cx.match(/<Connector>[\s\S]*?<\/Connector>/g) || []);
    if (/<Connectors>[\s\S]*?<\/Connectors>/.test(cx)) {
      cx = cx.replace(/<Connectors>[\s\S]*?<\/Connectors>/, '<Connectors></Connectors>');
    }
    if (cx !== before) {
      writeFileSync(custXml, cx);
      ok(`emptied <Connectors> in customizations.xml (${connectorBlocks.length} connector definition(s) removed)`);
    }
  } else warn('customizations.xml not found — skipping <Connectors> reset');

  // 6. Prune the removed tool components' <Override> entries from [Content_Types].xml
  //    so the package manifest stays consistent. Connector files ride on <Default>
  //    extension content types, so removing the Connector/ folder needs no edit here.
  const ctPath = join(work, '[Content_Types].xml');
  if (existsSync(ctPath) && removedComponents.length) {
    let ct = readFileSync(ctPath, 'utf8');
    const before = ct;
    for (const name of removedComponents) {
      const re = new RegExp(`<Override PartName="/botcomponents/${name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}/[^"]*"[^>]*/>`, 'g');
      ct = ct.replace(re, '');
    }
    if (ct !== before) { writeFileSync(ctPath, ct); ok('pruned removed parts from [Content_Types].xml'); }
  }

  // 7. Re-zip preserving the package layout. [Content_Types].xml must be first.
  if (existsSync(output)) rmSync(output, { force: true });
  const entries = readdirSync(work);
  const ordered = ['[Content_Types].xml', ...entries.filter((e) => e !== '[Content_Types].xml')];
  log(`Packing ${basename(output)}`);
  sh('zip', ['-r', '-q', '-X', output, ...ordered], { cwd: work });
  ok(`Wrote agents-only solution: ${output}`);
  console.log(`\nNext: import the connectors solution first, then this agents-only solution, create one no-auth connection per custom connector, and follow deploy/manifest.json or deploy/README.md to re-add all MCP servers and standard connector actions in Copilot Studio.`);
} finally {
  rmSync(work, { recursive: true, force: true });
}
