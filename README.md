# LoL Chat Off

A lightweight Windows system tray application that lets you go offline in League of Legends chat without disconnecting from the game.

It works by adding Windows Firewall rules to block outbound connections to Riot's chat servers (IPv4 and IPv6), making you appear offline to friends while staying connected to the game.

## Features

- **System tray icon** — sits quietly in your taskbar, click to toggle
- **One-click toggle** — enable/disable chat blocking instantly
- **Multi-region support** — BR, NA, EUW, EUNE, LAN, LAS, JP, OCE, RU, TR, and more
- **Visual status** — hextech-styled icon: cyan = chat active, gray + red X = chat blocked
- **Auto-detect region** — defaults to your region based on your OS language
- **Portable** — single `.exe`, no installation required
- **Runs as admin** — automatically requests elevation (required for firewall rules)

## Usage

1. Run `LoLChatOff.exe` (it will ask for admin permissions)
2. A tray icon appears near the clock
3. Right-click the icon to:
   - **Disable/Enable Chat** — toggle the firewall rules
   - **Region** — select your server region
   - **Quit** — exit the app (rules remain until you re-enable chat)

## Building from Source

### Requirements

- Python 3.11+
- Windows 10/11

### Steps

```bash
pip install -r requirements.txt
python build.py
```

The portable `.exe` will be at `dist/LoLChatOff.exe`.

## Background

Sometimes you just want to play without being bothered, but Riot never added an invisible/offline mode to the client. The workaround? Manually adding and removing Windows Firewall rules to block the chat servers. After doing it by hand too many times, it made sense to wrap it into a simple one-click app.

## How It Works

Riot's chat system connects to region-specific servers (e.g. `br.chat.si.riotgames.com`). This app resolves the server's IP addresses and creates Windows Firewall outbound block rules, preventing the chat client from connecting — which makes you appear offline without affecting gameplay.

## License

MIT
