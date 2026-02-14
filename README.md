# 🧊 Cubelytics

![](https://i.postimg.cc/Nfq5rY5b/Screenshot-2026-02-13-at-19-32-44-Cubelytics.png)


**Cubelytics** - Minecraft player OSINT tool. Search a username or UUID and get profile data from **24 sources** in real time.

![Python](https://img.shields.io/badge/python-3.10+-blue)
![Flask](https://img.shields.io/badge/flask-server-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

## Features

- **Instant lookup** - enter a username or UUID, results stream in via SSE as each source responds
- **Java & Bedrock** - resolves both platforms via Mojang API + Geyser XUID
- **24 sources** scraped in parallel:

| Source |
|---|
| **6b6t.org** |
| **CavePvP** |
| **centraltierlist.com** |
| **Crafty.gg** |
| **DonutStats** |
| **ExtremeCraft** |
| **Hive** |
| **Hypixel** |
| **JartexNetwork** |
| **Laby.net** |
| **LeoneMC** |
| **ManaCube** |
| **MCC Island** |
| **MCBrawl** |
| **MCSR Ranked** |
| **MinecraftEarth** |
| **mctiers.com** |
| **Mojang** |
| **NameMC** |
| **PaleTiers** |
| **Pika Network** |
| **pvptiers.com** |
| **Reafy** |
| **subtiers.net** |
| **Wynncraft** |




## Quick Start

```bash
# Clone
git clone https://github.com/faranoia/cubelytics.git
cd cubelytics

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

## Project Structure

```
├── main.py                  # Flask app + SSE endpoint
├── requirements.txt         # pip dependencies
├── functions/               # One module per source
│   ├── __init__.py          
│   ├── mojang.py            # UUID/username resolution
│   ├── namemc.py            # NameMC 
│   ├── hypixel.py           # Hypixel
│   ├── ...                  # 21 more scrapers
├── templates/
│   └── index.html           # Single-page frontend
└── static/
    ├── style.css            # UI styles
    └── app.js               # SSE client + rendering
```

## How It Works

1. User enters a username or UUID
2. Backend resolves the player via Mojang API (Java) or Geyser (Bedrock)
3. All 21 scrapers run **in parallel** using threads
4. Results stream to the frontend via **Server-Sent Events** (SSE)
5. Frontend renders each source card as data arrives

## Dependencies

| Package | Why |
|---|---|
| `flask` | Web server |
| `requests` | HTTP client for most scrapers |
| `beautifulsoup4` | HTML parsing |
| `tls_client` | TLS fingerprint spoofing (NameMC Cloudflare bypass) |

## Have New Websites or Endpoints?

Found a new Minecraft-related website or API for players look-up?
You can help expand Cubelytics 
* Submit at Discord: faranoia
* Or open an Issue 

## License

MIT
