## 1. Registrar el bridge MCP

- [x] 1.1 **RESUELTO 2026-09-11.** Creado `antigravity-app/.mcp.json` (project-scoped):
      `command: wsl.exe`, `args: [-d, Ubuntu, /home/contexia/.hermes/hermes-agent/venv/bin/hermes,
      --profile, contexia, mcp, serve]`. Usa la ruta absoluta del venv (no `hermes` a secas) para
      no depender de que el PATH de WSL esté configurado igual en cada invocación desde Windows.
- [x] 1.2 **RESUELTO 2026-09-11.** JSON no soporta comentarios inline, así que el alcance
      (desarrollo, nunca datos de negocio) quedó documentado en `ARCHITECTURE.md` (nueva fila
      "Bridge MCP Hermes→Claude Code" en la tabla de contenedores) en vez de en el propio archivo.

## 2. Verificar la conexión

- [x] 2.1 **RESUELTO 2026-09-11.** El fundador reinició la sesión de Claude Code — las 10 tools
      de Hermes (`mcp__hermes__*`: channels_list, conversations_list, conversation_get,
      messages_read, messages_send, events_poll, events_wait, attachments_fetch,
      permissions_list_open, permissions_respond) aparecen listadas.
- [x] 2.2 **RESUELTO 2026-09-11.** `channels_list()` respondió con datos reales, no un error
      vacío: `{"count": 1, "channels": [{"target": "telegram:993414747", "platform": "telegram",
      "name": "JD PC", "chat_type": "dm"}]}` — coincide exactamente con el canal real confirmado
      en `channel_directory.json` durante el change anterior. Bridge funcional end-to-end.
- [x] 2.3 **RESUELTO 2026-09-11.** `hermes --version` tras la conexión: "Hermes Agent v0.21.1 ·
      upstream 1021a032 · local 2ddeba9e" — sin ningún warning de "mixed sys.modules" ni de
      sesión. (Nota aparte, no bloqueante: reporta "267 commits behind" — actualización
      disponible normal, no un error; no se ejecuta `hermes update` ahora para no interrumpir la
      conexión del bridge recién verificada.)

## 3. Documentar el cierre del gap

- [x] 3.1 **RESUELTO 2026-09-11.** `docs/integrations/HERMES-SELF-CONFIG.md` §6 corregido: ya no
      afirma que el gap está abierto, documenta el bridge real y mantiene la coordinación vía
      GBrain/`COORDINATION-LOG.md` como mecanismo paralelo (no reemplazado).
- [x] 3.2 **RESUELTO 2026-09-11.** Nueva fila en `ARCHITECTURE.md` con referencia a este change.

## 4. Cierre del change (sin Stage 11 — no hay deploy a Railway/Vercel)

- [ ] 4.1 `git diff` de los archivos tocados — confirmar que `.mcp.json` no contiene tokens ni
      credenciales inline
- [ ] 4.2 Confirmar con el fundador que el bridge funciona end-to-end antes de archivar
- [ ] 4.3 Commit de los cambios a `main`

## 5. Fuera de alcance — registrar como pendiente, no ejecutar aquí

- Loop piloto de auto-fix sobre un Scheduled Job real — decisión y change futuros, una vez el
  bridge esté validado end-to-end (ver Open Question de `design.md`: candidato preliminar Radar
  Predictivo, a confirmar con el fundador).
