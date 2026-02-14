import json
import queue
import threading

from flask import Flask, render_template, request, jsonify, Response

from functions import (
    MojangClient,
    McTiersClient,
    PvpTiersClient,
    CentralTierListClient,
    HypixelClient,
    MinecraftEarthClient,
    JartexClient,
    HiveClient,
    SixB6tClient,
    PikaClient,
    ReafyClient,
    McsrRankedClient,
    MccIslandClient,
    ManaCubeClient,
    MCBrawlClient,
    ExtremeCraftClient,
    CavePvPClient,
    WynncraftClient,
    LeoneMCClient,
    DonutStatsClient,
    LabyNetClient,
    NameMCClient,
    CraftyGGClient,
    PaleTiersClient,
    SubTiersClient,
)

app = Flask(__name__)

_mojang = MojangClient()
_clients = {
    "mctiers.com":         (McTiersClient(),         "uuid"),
    "pvptiers.com":        (PvpTiersClient(),        "both"),
    "centraltierlist.com": (CentralTierListClient(), "both"),
    "hypixel (plancke)":   (HypixelClient(),         "username"),
    "minecraftearth.org":  (MinecraftEarthClient(),  "username"),
    "jartexnetwork.com":   (JartexClient(),          "username"),
    "playhive.com":        (HiveClient(),            "username"),
    "6b6t.org":            (SixB6tClient(),          "username"),
    "pika-network.net":    (PikaClient(),            "username"),
    "reafystats.com":      (ReafyClient(),           "username"),
    "mcsrranked.com":      (McsrRankedClient(),      "both"),
    "mccisland":           (MccIslandClient(),       "username"),
    "manacube.com":        (ManaCubeClient(),        "uuid"),
    "mcbrawl.com":         (MCBrawlClient(),         "username"),
    "extremecraft.net":    (ExtremeCraftClient(),    "username"),
    "cavepvp.com":         (CavePvPClient(),        "username"),
    "wynncraft.com":       (WynncraftClient(),       "uuid"),
    "leonemc.net":         (LeoneMCClient(),         "username"),
    "donutstats.net":      (DonutStatsClient(),      "username"),
    "laby.net":            (LabyNetClient(),          "username"),
    "namemc.com":          (NameMCClient(),           "username"),
    "crafty.gg":           (CraftyGGClient(),         "username"),
    "paletiers.xyz":       (PaleTiersClient(),        "username"),
    "subtiers.net":        (SubTiersClient(),         "uuid"),
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search")
def api_search():
    """SSE endpoint — streams progress + final results."""
    identifier = request.args.get("q", "").strip()
    if not identifier:
        return jsonify({"error": "No input provided"}), 400

    def generate():
        uuid = None
        xuid = None
        username = identifier
        platform = "java"

        try:
            uuid, username = _mojang.resolve_both(identifier)
        except Exception:
            xuid = _mojang.resolve_bedrock(identifier)
            if xuid:
                platform = "bedrock"
                username = identifier
            else:
                yield _sse({
                    "type": "error",
                    "message": f"Player '{identifier}' not found (Java or Bedrock)",
                })
                yield _sse({"type": "done"})
                return

        skin_url = (
            f"https://mc-heads.net/body/{uuid}/right"
            if uuid
            else f"https://mc-heads.net/body/{username}/right"
        )

        yield _sse({
            "type": "player",
            "uuid": uuid,
            "xuid": xuid,
            "username": username,
            "platform": platform,
            "skin_url": skin_url,
        })

        sources = []
        for label, (client, use) in _clients.items():
            if platform == "bedrock" and use == "uuid":
                continue
            sources.append((label, client, use))

        total = len(sources)
        results_queue = queue.Queue()

        def worker(label, client, use):
            try:
                fn = client.get_profile
                if use == "uuid":
                    data = fn(uuid)
                elif use == "username":
                    data = fn(username)
                else:
                    if uuid:
                        try:
                            data = fn(uuid)
                        except Exception:
                            data = fn(username)
                    else:
                        data = fn(username)
                results_queue.put((label, data, None))
            except Exception as exc:
                results_queue.put((label, None, str(exc)))

        threads = []
        for label, client, use in sources:
            t = threading.Thread(target=worker, args=(label, client, use))
            t.start()
            threads.append(t)

        fetched = 0
        while fetched < total:
            label, data, error = results_queue.get()
            fetched += 1
            yield _sse({
                "type": "source",
                "label": label,
                "data": data,
                "error": error,
                "fetched": fetched,
                "total": total,
            })

        for t in threads:
            t.join()

        yield _sse({"type": "done"})

    return Response(generate(), mimetype="text/event-stream")


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


if __name__ == "__main__":
    app.run(debug=True, port=5000)
