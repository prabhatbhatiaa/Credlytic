# backend/app.py

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os, json
from datetime import datetime, timezone
import base64

from admin_mint import mint_certificate_with_email, generate_certificate_png
from email_utils import send_certificate_email

# ==========================================================
#                   FILE SYSTEM SETUP
# ==========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_DIR = os.path.join(BASE_DIR, "generated")
DB_FILE = os.path.join(BASE_DIR, "db.json")
ADMINS_FILE = os.path.join(BASE_DIR, "admin.json")

os.makedirs(GENERATED_DIR, exist_ok=True)

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({}, f)

if not os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, "w") as f:
        json.dump({}, f)

app = Flask(
    __name__,
    static_folder="../frontend",
    static_url_path="",
)

CORS(app)

# Keep Google sign-in unhindered
@app.after_request
def coop_fix(res):
    res.headers["Cross-Origin-Opener-Policy"] = "unsafe-none"
    res.headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"
    return res

app.url_map.strict_slashes = False


# ==========================================================
#              LOAD & SAVE HELPERS
# ==========================================================
def load_admins():
    with open(ADMINS_FILE, "r") as f:
        return json.load(f)

def save_admins(admins):
    with open(ADMINS_FILE, "w") as f:
        json.dump(admins, f, indent=2)

def load_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)


# ==========================================================
#                FRONTEND ROUTES
# ==========================================================
@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/student")
@app.route("/student/")
def student_page():
    return app.send_static_file("student.html")

@app.route("/admin")
@app.route("/admin/")
def admin_page():
    return app.send_static_file("admin.html")

# 🔥 NEW: CLEAN DASHBOARD ROUTE
@app.route("/admin/dashboard")
@app.route("/admin/dashboard/")
def admin_dashboard_page():
    return app.send_static_file("dashboard.html")

@app.route("/employer")
@app.route("/employer/")
def employer_page():
    return app.send_static_file("employer.html")


# Protect accidental catch-all under /api
@app.route("/api/<path:dummy>")
def api_guard(dummy):
    return "Invalid API route", 404


# ==========================================================
#                 ADMIN GOOGLE AUTH
# ==========================================================
ALLOWED_ADMIN_EMAILS = ["credlytic@gmail.com"]

@app.route("/api/admin/login_check", methods=["POST"])
def login_check():
    data = request.get_json() or {}
    email = data.get("email")

    if not email:
        return jsonify({"ok": False, "error": "Missing email"}), 400

    if email not in ALLOWED_ADMIN_EMAILS:
        return jsonify({"ok": False, "error": "Unauthorized Google Admin"}), 403

    admins = load_admins()

    if email in admins:
        return jsonify({
            "ok": True,
            "is_registered": True,
            "wallet": admins[email]["wallet"]
        })

    return jsonify({"ok": True, "is_registered": False})


# ==========================================================
#         WALLET BINDING (ONE-TIME)
# ==========================================================
@app.route("/api/admin/bind_start", methods=["POST"])
def bind_start():
    data = request.get_json() or {}
    email = data.get("email")

    if email not in ALLOWED_ADMIN_EMAILS:
        return jsonify({"ok": False, "error": "Unauthorized"}), 403

    return jsonify({"ok": True})


@app.route("/api/admin/bind_finish", methods=["POST"])
def bind_finish():
    data = request.get_json() or {}

    email = data.get("email")
    wallet = data.get("wallet")
    message = data.get("message")
    signature = data.get("signature")

    if email not in ALLOWED_ADMIN_EMAILS:
        return jsonify({"ok": False, "error": "Unauthorized"}), 403

    if not wallet:
        return jsonify({"ok": False, "error": "Missing wallet"}), 400

    try:
        message.encode("utf-8")
        base64.b64decode(signature)
    except Exception:
        return jsonify({"ok": False, "error": "Invalid signature"}), 400

    admins = load_admins()
    admins[email] = {
        "wallet": wallet,
        "verified": True,
        "bound_at": datetime.now(timezone.utc).isoformat()
    }
    save_admins(admins)

    return jsonify({"ok": True, "wallet": wallet})


# ==========================================================
#                 ISSUE CERTIFICATE
# ==========================================================
@app.route("/api/admin/issue", methods=["POST"])
def issue():
    p = request.get_json() or {}

    admin_email = p.get("admin_email")
    admin_wallet = p.get("admin_wallet")

    admins = load_admins()

    if admin_email not in admins:
        return jsonify({"ok": False, "error": "Admin not registered"}), 403

    if admins[admin_email]["wallet"].lower() != admin_wallet.lower():
        return jsonify({"ok": False, "error": "Wallet mismatch"}), 403

    required = ["student_name", "student_email", "course_name"]
    for f in required:
        if not p.get(f):
            return jsonify({"ok": False, "error": f"Missing field: {f}"}), 400

    try:
        tx, token_name = mint_certificate_with_email(
            p["student_name"], p["course_name"], p["student_email"]
        )
    except Exception as e:
        return jsonify({"ok": False, "error": f"Minting failed: {e}"}), 500

    explorer = f"https://explorer.aptoslabs.com/txn/{tx}?network=devnet"

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe = p["student_email"].replace("@", "_").replace(".", "_")
    pdf_name = f"{safe}_{ts}.pdf"
    pdf_path = os.path.join(GENERATED_DIR, pdf_name)

    returned_pdf_path = generate_certificate_png(
        p["student_name"], p["course_name"], tx, token_name, pdf_path
    )

    if not returned_pdf_path:
        return jsonify({"ok": False, "error": "Failed to generate certificate"}), 500

    entry = {
        "file": os.path.basename(returned_pdf_path),
        "student": p["student_name"],
        "email": p["student_email"],
        "course": p["course_name"],
        "token_name": token_name,
        "tx_hash": tx,
        "explorer_url": explorer,
        "issued_at": datetime.now(timezone.utc).isoformat()
    }

    db = load_db()
    db.setdefault(p["student_email"], []).append(entry)
    save_db(db)

    try:
        send_certificate_email(
            p["student_email"],
            p["student_name"],
            p["course_name"],
            explorer,
            returned_pdf_path,
            tx_hash=tx
        )
    except Exception as e:
        return jsonify({"ok": True, "entry": entry, "warning": f"Email failed: {e}"}), 200

    return jsonify({"ok": True, "entry": entry})


# ==========================================================
#             STUDENT CERTIFICATE LOOKUP
# ==========================================================
@app.route("/api/student/certificates", methods=["GET"])
def get_certificates():
    email = request.args.get("email")
    if not email:
        return jsonify({"ok": False, "error": "Missing email"}), 400

    db = load_db()
    return jsonify({"ok": True, "certificates": db.get(email, [])})


# ==========================================================
#             EMPLOYER VERIFICATION
# ==========================================================
@app.route("/api/employer/verify", methods=["POST"])
def employer_verify():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip()
    tx_hash = (data.get("tx_hash") or "").strip()

    if not email or not tx_hash:
        return jsonify({"ok": False, "error": "Missing email or transaction hash"}), 400

    db = load_db()
    entries = db.get(email, [])

    def normalize(h):
        h = h.lower()
        return h if h.startswith("0x") else "0x" + h

    needle = normalize(tx_hash)

    for e in entries:
        if e.get("tx_hash") and e["tx_hash"].lower() == needle:
            return jsonify({"ok": True, "certificate": e})

    return jsonify({"ok": False, "error": "No matching certificate found"}), 404


# ==========================================================
#             SERVE GENERATED FILES
# ==========================================================
@app.route("/generated/<filename>")
def serve_file(filename):
    return send_from_directory(GENERATED_DIR, filename)


# ==========================================================
#                  RUN SERVER
# ==========================================================
if __name__ == "__main__":
    app.run(port=5000, debug=True)
