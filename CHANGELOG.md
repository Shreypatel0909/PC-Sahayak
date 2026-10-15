# Changelog

## 1.3.1 (2026-10-15)

- **Power button** to close PC-Sahayak from the app: stops the server, frees
  the port, closes the launcher window and shows a "closed" page. Only the
  computer running PC-Sahayak has it.
- **Network mode fixes:** if PC-Sahayak is already running for this computer
  only, the network launcher offers to restart it in network mode. If Windows
  has the Wi-Fi set to Public (which blocks other devices), it offers to set it
  to Private and allow PC-Sahayak through the firewall in one administrator
  prompt. The uninstaller can undo both.
- **Fixed:** Settings crashed when an older PC-Sahayak was still running after
  an update. The interface now tolerates it, a crash shows a Reload screen
  instead of a blank page, and the launcher offers to restart an outdated copy.
- **Fixed:** the launcher and uninstaller could not always stop the server
  (Windows starts it through a small `.venv` helper process).
- README rewritten for the current version; `main` now carries the full app.

## 1.3.0 (2026-10-15)

- **Renamed to PC-Sahayak** across the app, the assistant's replies and the docs.
- **Double-click launcher** (`Start PC-Sahayak.bat`): checks for Python, the
  Python packages, Node.js (only to build the interface) and the Groq API key,
  asks before installing anything that is missing, then opens the app in the
  browser. Offers a desktop shortcut on first run.
- **Local network mode** (`Start PC-Sahayak (network).bat`): phones and other
  PCs on the same network can use PC-Sahayak through a share link. The link
  carries an access code, so devices without it are blocked; this computer
  never needs it. The link is also shown in Settings, with a copy button.
- **Uninstaller** (`Uninstall PC-Sahayak.bat`): removes what the launcher set
  up, and asks separately about saved chats, the API key, the firewall rule,
  any Python or Node.js it installed, and the program folder.
- Version number shown in Settings.

## 1.1.0

- New **React + TypeScript interface** (Vite) over a thin **FastAPI** layer; the
  Python core and the Streamlit app are unchanged and share the same chats.
- "Fix route" panel: each step becomes a stop, coloured by the problem type the
  assistant assigns; the route advances automatically.
- Detailed, step-by-step replies; off-topic questions get a polite refusal;
  confirming the fix gives a full summary and locks the chat (unlockable).
- Delete one or all chats, settings (theme, reply animation, rebuild index),
  screenshots by upload, drag-and-drop or paste.

## 1.0.0

- Streamlit app built on the original PC Sahayak prototype: Groq LLM, RAG over
  a Markdown knowledge base with citations, intake form for system specs,
  saved and resumable chats, screenshot (vision) support, tests.
