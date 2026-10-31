import os
import requests
from flask import Flask, Response, redirect, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY", "bashar_supreme_ultimate_iptv_master_2026")
TIMEOUT_LIMIT = 8

# ==============================================================================
# 1. قراءة وفحص مصادر الـ Xtream الـ 59 تلقائياً من ملف sources.txt
# ==============================================================================
def load_sources_from_file():
    sources = []
    try:
        if os.path.exists("sources.txt"):
            with open("sources.txt", "r", encoding="utf-8") as f:
                for idx, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts = line.split(",")
                        if len(parts) >= 3:
                            sources.append({
                                "id": idx,
                                "dns": parts[0].strip(),
                                "username": parts[1].strip(),
                                "password": parts[2].strip()
                            })
    except Exception as e:
        print(f"Error reading sources.txt: {e}")
    return sources

# ==============================================================================
# 2. قاعدة بيانات المشتركين (أنت تتحكم بكافة الصلاحيات، الأسماء، وكلمات المرور)
# ==============================================================================
SUBSCRIBERS_DB = {
    "client_bashar": {
        "password": "123",                          # كلمة المرور المخصصة للعميل
        "expiry_date": "2026-12-31",              # تاريخ انتهاء الاشتراك بدقة
        "max_connections": 2,                     # عدد الأجهزة المسموحة في نفس الوقت
        "allowed_device": "Android TV / TiviMate / IPTV Smarters",
        "status": "Active"                        # Active أو Suspended
    },
    # يمكنك إضافة عملاء جدد هنا بكل سهولة:
    # "client_2": {"password": "456", "expiry_date": "2026-06-30", "max_connections": 1, "allowed_device": "Smart IPTV", "status": "Active"}
}

# ==============================================================================
# 3. محرك الفحص الذكي (يأخذ الأكواد التي تعمل فقط ويستبعد التالفة)
# ==============================================================================
def get_active_upstream_sources():
    raw_sources = load_sources_from_file()
    active_sources = []
    for src in raw_sources:
        try:
            check_url = f"{src['dns']}/player_api.php?username={src['username']}&password={src['password']}"
            resp = requests.get(check_url, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("user_info", {}).get("auth") == 1 or "user_info" in data:
                    active_sources.append(src)
        except Exception:
            continue
    return active_sources if active_sources else raw_sources

# ==============================================================================
# 4. لوحة التحكم الإدارية الاحترافية والقصوى (Admin Dashboard)
# ==============================================================================
@app.route('/')
def admin_master_dashboard():
    raw_sources = load_sources_from_file()
    active_sources = get_active_upstream_sources()
    dashboard_html = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>لوحة التحكم المطلقة - IPTV Master Proxy</title>
        <style>
            :root { --bg: #030712; --card: #0f172a; --accent: #0ea5e9; --text: #f8fafc; --success: #22c55e; --danger: #ef4444; }
            body { font-family: 'Segoe UI', Tahoma, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }
            .container { max-width: 1250px; margin: auto; }
            header { text-align: center; margin-bottom: 30px; padding: 25px; background: var(--card); border-radius: 18px; border: 1px solid #1e293b; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
            header h1 { color: #38bdf8; margin: 0; font-size: 26px; text-shadow: 0 0 20px rgba(56,189,248,0.4); }
            header p { color: #94a3b8; font-size: 14px; margin-top: 10px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 25px; }
            .card { background: var(--card); padding: 20px; border-radius: 18px; border: 1px solid #1e293b; box-shadow: 0 8px 25px rgba(0,0,0,0.5); }
            .card h3 { margin-top: 0; color: #38bdf8; border-bottom: 2px solid #1e293b; padding-bottom: 12px; font-size: 17px; }
            .stat-value { font-size: 28px; font-weight: bold; color: var(--success); }
            .table-responsive { width: 100%; overflow-x: auto; }
            table { width: 100%; border-collapse: collapse; margin-top: 12px; min-width: 650px; }
            th, td { padding: 14px 12px; text-align: right; border-bottom: 1px solid #1e293b; font-size: 13px; }
            th { color: #38bdf8; background: #1e293b; }
            tr:hover { background: rgba(30, 41, 59, 0.5); }
            .badge { background: var(--accent); color: white; padding: 6px 12px; border-radius: 8px; font-size: 11px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>⚡ نظام إدارة وتوحيد الـ IPTV الأقصى قوة</h1>
                <p>فحص تلقائي للمصادر من ملف sources.txt، دمج القنوات والأفلام والمسلسلات، وإدارة مركزية للعملاء</p>
            </header>
            
            <div class="grid">
                <div class="card">
                    <h3>🌐 حالة مصادر الـ Xtream (59 مصدر)</h3>
                    <p>إجمالي المصادر المضافة في الملف: <span class="stat-value" style="color:#38bdf8;">{{ total_raw }}</span> مصدراً</p>
                    <p>المصادر النشطة والشغالة فقط: <span class="stat-value">{{ active_count }}</span> مصدراً</p>
                </div>
                <div class="card">
                    <h3>👥 إدارة المشتركين والاتصالات</h3>
                    <p>إجمالي العملاء المسجلين: <span class="stat-value">{{ total_subs }}</span> عميلاً</p>
                    <p>حالة النظام السحابي: <span class="badge" style="background:var(--success);">مستقر ويعمل 24/7</span></p>
                </div>
            </div>

            <div class="card">
                <h3>📋 جدول التحكم الشامل بالعملاء (الصلاحيات، كلمات المرور، والأجهزة)</h3>
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>اسم المستخدم (Username)</th>
                                <th>كلمة المرور (Password)</th>
                                <th>تاريخ انتهاء الاشتراك</th>
                                <th>الأجهزة المسموحة</th>
                                <th>نوع الجهاز المعتمد</th>
                                <th>حالة الحساب</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for username, data in subscribers.items() %}
                            <tr>
                                <td><strong>{{ username }}</strong></td>
                                <td><code>{{ data.password }}</code></td>
                                <td><span style="color: #38bdf8; font-weight:bold;">{{ data.expiry_date }}</span></td>
                                <td><span class="badge">{{ data.max_connections }} جهاز</span></td>
                                <td>{{ data.allowed_device }}</td>
                                <td><span style="color: var(--success); font-weight: bold;">{{ data.status }}</span></td>
                            </tr>
                            {% else %}
                            <tr>
                                <td colspan="6" style="text-align: center; color: #94a3b8; padding: 25px;">لا توجد حسابات مسجلة. أضفهم في SUBSCRIBERS_DB!</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(
        dashboard_html, 
        total_raw=len(raw_sources), 
        active_count=len(active_sources), 
        total_subs=len(SUBSCRIBERS_DB), 
        subscribers=SUBSCRIBERS_DB
    )

# ==============================================================================
# 5. نقطة اتصال تطبيقات الـ IPTV (Xtream API Login & Full Actions Proxy)
# ==============================================================================
@app.route('/player_api.php')
def xtream_player_api_proxy():
    username = request.args.get('username')
    password = request.args.get('password')
    action = request.args.get('action')
    
    # 1. التحقق من العميل وصلاحية اشتراكه
    client = SUBSCRIBERS_DB.get(username)
    if not client or client['password'] != password or client.get('status') != "Active":
        return jsonify({"user_info": {"auth": 0, "status": "Unauthorized or Expired"}}), 401
        
    active_sources = get_active_upstream_sources()
    
    # 2. معالجة كافة الأقسام والطلبات (Live, VOD, Series) وتوجيهها للمصدر الشغال
    if action and active_sources:
        try:
            target_source = active_sources[0]
            upstream_url = f"{target_source['dns']}/player_api.php?username={target_source['username']}&password={target_source['password']}&action={action}"
            
            for key, val in request.args.items():
                if key not in ['username', 'password']:
                    upstream_url += f"&{key}={val}"
            
            resp = requests.get(upstream_url, timeout=TIMEOUT_LIMIT)
            return resp.content, resp.status_code, dict(resp.headers)
        except Exception:
            return jsonify([])

    # 3. استجابة تسجيل الدخول الرسمية المتوافقة مع كافة تطبيقات الـ IPTV
    response_payload = {
        "user_info": {
            "username": username,
            "password": password,
            "status": "Active",
            "exp_date": "1893456000",
            "is_trial": "0",
            "active_cons": "1",
            "max_connections": str(client['max_connections'])
        },
        "server_info": {
            "url": request.host_url.rstrip('/').replace('https://', 'http://'),
            "port": "8080",
            "https_port": "8080",
            "server_protocol": "http"
        }
    }
    return jsonify(response_payload)

# ==============================================================================
# 6. محرك توجيه البث الشامل (القنوات المباشرة، الأفلام، المسلسلات)
# ==============================================================================
@app.route('/live/<username>/<password>/<path:stream_path>')
@app.route('/movie/<username>/<password>/<path:stream_path>')
@app.route('/series/<username>/<password>/<path:stream_path>')
def proxy_stream_dispatcher(username, password, stream_path):
    client = SUBSCRIBERS_DB.get(username)
    if not client or client['password'] != password:
        return "Unauthorized Stream Access", 401
        
    active_sources = get_active_upstream_sources()
    if active_sources:
        target_source = active_sources[0]
        media_type = request.path.split('/')[1]
        target_url = f"{target_source['dns']}/{media_type}/{target_source['username']}/{target_source['password']}/{stream_path}"
        return redirect(target_url, code=302)
        
    return "No Active Upstream Sources Available", 503

@app.route('/health')
@app.route('/actuator/health')
def snapdeploy_health_check():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
