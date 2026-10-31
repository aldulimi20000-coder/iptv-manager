import os
import json
import logging
from flask import Flask, request, jsonify, render_template_string, redirect

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

SOURCES_FILE = "sources.json"
SUBS_FILE = "subscribers.json"

def init_storage():
    if not os.path.exists(SOURCES_FILE):
        with open(SOURCES_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    if not os.path.exists(SUBS_FILE):
        with open(SUBS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "12345": {
                    "password": "12345",
                    "expiry_date": "2026-12-31",
                    "status": "Active"
                }
            }, f, ensure_ascii=False, indent=4)

init_storage()

def load_json(filename):
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return [] if filename == SOURCES_FILE else {}

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

@app.route('/', methods=['GET', 'POST'])
def web_control_panel():
    message = ""
    subs = load_json(SUBS_FILE)
    sources = load_json(SOURCES_FILE)

    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'add_subscriber':
            u = request.form.get('username', '').strip()
            p = request.form.get('password', '').strip()
            if u and p:
                subs[u] = {"password": p, "expiry_date": "2026-12-31", "status": "Active"}
                save_json(SUBS_FILE, subs)
                message = f"تم إضافة المشترك ({u}) بنجاح!"
        elif form_type == 'add_source':
            dns = request.form.get('dns', '').strip().rstrip('/')
            su = request.form.get('s_username', '').strip()
            sp = request.form.get('s_password', '').strip()
            if dns and su and sp:
                sources.append({"dns": dns, "username": su, "password": sp})
                save_json(SOURCES_FILE, sources)
                message = "تم إضافة المصدر بنجاح!"

    current_url = request.host_url.rstrip('/')
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>لوحة تحكم السيرفر النهائي</title>
        <style>
            body {{ background: #030712; color: #f8fafc; font-family: Tahoma; padding: 20px; }}
            .card {{ background: #0f172a; padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #1e293b; }}
            input, button {{ width: 100%; padding: 10px; margin: 8px 0; background: #020617; border: 1px solid #334155; color: white; border-radius: 6px; box-sizing: border-box; }}
            button {{ background: #0ea5e9; font-weight: bold; cursor: pointer; }}
            code {{ color: #38bdf8; font-size: 15px; word-break: break-all; }}
        </style>
    </head>
    <body>
        <div style="max-width: 800px; margin: auto;">
            <div class="card" style="text-align: center;">
                <h2>⚡ لوحة التحكم النهائية</h2>
                <p>رابط السيرفر (URL) الخاص بك:</p>
                <code>{current_url}</code>
            </div>
            {f'<div style="background:#065f46; padding:10px; border-radius:6px; margin-bottom:15px; text-align:center;">{message}</div>' if message else ''}
            <div class="card">
                <h3>➕ إضافة مشترك جديد</h3>
                <form method="POST">
                    <input type="hidden" name="form_type" value="add_subscriber">
                    <input type="text" name="username" placeholder="اسم المستخدم (مثل: 12345)" required>
                    <input type="text" name="password" placeholder="كلمة المرور (مثل: 12345)" required>
                    <button type="submit">إضافة المشترك</button>
                </form>
            </div>
            <div class="card">
                <h3>🌐 إعادة توجيه مباشر للمصدر الأصلي</h3>
                <form method="POST">
                    <input type="hidden" name="form_type" value="add_source">
                    <input type="text" name="dns" placeholder="رابط المصدر الكامل (مثل: http://marveltv.info:80/get.php?...)" required>
                    <input type="text" name="s_username" placeholder="ملاحظة أو اسم" value="MainSource" required>
                    <input type="text" name="s_password" placeholder="كلمة المرور" value="123" required>
                    <button type="submit">حفظ التوجيه</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/player_api.php')
def xtream_gateway():
    usr = request.args.get('username')
    pwd = request.args.get('password')
    subs = load_json(SUBS_FILE)
    
    if usr not in subs or subs[usr].get('password') != pwd:
        return jsonify({"user_info": {"auth": 0}}), 401

    sources = load_json(SOURCES_FILE)
    if sources:
        target = sources[0]['dns']
        if "://" in target:
            return redirect(target, code=302)

    return jsonify({
        "user_info": {"username": usr, "status": "Active", "max_connections": "5"},
        "server_info": {"url": request.host_url.rstrip('/'), "port": "80"}
    })

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 1500))
    app.run(host='0.0.0.0', port=port)
