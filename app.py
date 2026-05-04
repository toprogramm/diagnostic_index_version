from flask import Flask, render_template, request, jsonify, send_from_directory
import requests, re, urllib3, os, json
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --- LOAD ENV ---
load_dotenv()

LOGIN = os.getenv("LOGIN")
PASSWORD = os.getenv("PASSWORD")
TIMEOUT = int(os.getenv("TIMEOUT", 300))
SIGNIN_TAIL = os.getenv("SIGNIN_TAIL")
VERSION_TAIL = os.getenv("VERSION_TAIL")
INDEX_TAIL = os.getenv("INDEX_TAIL")

PAGE_AUTH_TOKEN = os.getenv("PAGE_AUTH_TOKEN")
PAGE_INPUT_LOGIN = os.getenv("PAGE_INPUT_LOGIN")
PAGE_INPUT_PASSWORD = os.getenv("PAGE_INPUT_PASSWORD")
PAGE_PARSER_BODY = os.getenv("PAGE_PARSER_BODY")

# --- LOAD SERVERS ---
def load_servers():
    with open("config.json", encoding="utf-8") as f:
        return json.load(f)["servers"]

SERVERS = load_servers()

# --- SSL WARNINGS OFF ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# --- HELPERS ---
def parse(soup):
    res = []
    mp = soup.find(id=PAGE_PARSER_BODY)
    if not mp:
        return res

    for div in mp.find_all("div", class_="exception-panel"):
        al = div.find("div", class_="alert")
        if not al:
            continue

        name = al.find("strong").get_text(strip=True) if al.find("strong") else "???"

        res.append({
            "name": name,
            "detail": al.get_text(separator=" ", strip=True).replace(name, "").strip(" -–"),
            "status": "alert-success" if "alert-success" in al.get("class", []) else "alert-danger"
        })

    return res


def get_session(url):
    s = requests.Session()
    s.verify = False

    r = s.get(f"{url}{SIGNIN_TAIL}", timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    token = soup.find("input", {"name": PAGE_AUTH_TOKEN})["value"]

    s.post(
        f"{url}{SIGNIN_TAIL}",
        data={
            PAGE_AUTH_TOKEN : token,
            PAGE_INPUT_LOGIN : LOGIN,
            PAGE_INPUT_PASSWORD: PASSWORD
        },
        timeout=10
    )

    return s


# --- ROUTES ---
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(app.root_path, "favicon.ico", mimetype="image/vnd.microsoft.icon")


@app.route("/api/servers")
def api_servers():
    return jsonify(SERVERS)


@app.route("/api/check", methods=["POST"])
def api_check():
    data = request.json
    srv = next(s for s in SERVERS if s["id"] == data["server_id"])

    try:
        session = get_session(srv["url"])
        result = {}

        # INDEX
        if data["mode"] in ("index", "both"):
            html = session.get(f"{srv['url']}{INDEX_TAIL}", timeout=TIMEOUT).text
            result["index"] = {
                "services": parse(BeautifulSoup(html, "html.parser"))
            }

        # VERSION
        if data["mode"] in ("version", "both"):
            html = session.get(f"{srv['url']}{VERSION_TAIL}", timeout=TIMEOUT).text
            soup = BeautifulSoup(html, "html.parser")

            footer = soup.find(id="footer")
            footer_version = (
                footer.find("a").text if footer and footer.find("a") else "?"
            )

            result["version"] = {
                "footer_version": footer_version,
                "services": [
                    {
                        "name": i["name"],
                        "version": (
                            re.search(r"([\d.]+)", i["detail"]).group(1)
                            if re.search(r"([\d.]+)", i["detail"])
                            else "?"
                        )
                    }
                    for i in parse(soup)
                ]
            }

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True, port=5000)