import os
import requests
from flask import Flask, Response, redirect, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY", "bashar_supreme_ultimate_iptv_master_2026")
TIMEOUT_LIMIT = 20

# ==============================================================================
# 1. قاعدة بيانات المصادر (قم بتعبئة بيانات سيرفرك الحقيقي هنا)
# ==============================================================================
UPSTREAM_SOURCES = [
    # مثال واضح: ضع هنا بيانات سيرفرك الأصلي لكي يسحب منها التطبيق القنوات والأفلام
    {
        "id": 1, 
        "dns": "http://your-provider-dns.com:8080", 
        "username": "your_upstream_username", 
        "password": "your_upstream_password", 
        "active": True
    },
    # يمكنك إضافة بقية الحسابات هنا تباعاً حتى 59 مصدراً
]

# ==============================================================================
# 2. قاعدة بيانات المشتركين (أنت من يتحكم باسم المستخدم وكلمة المرور الخاصة بك وبعملائك)
# ==============================================================================
SUBSCRIBERS_DB = {
    "client_bashar": {
        "password": "123",                          # كلمة المرور التي سيدخلها العميل في التطبيق
        "expiry_date": "2026-12-31",              # تاريخ انتهاء الاشتراك
        "max_connections": 1,                     # عدد الأجهزة المسموحة
        "allowed_device": "Android TV / TiviMate / IPTV Smarters",
        "status": "Active"
    }
}

ACTIVE_SESSIONS = {}

# ==============================================================================
# 3. لوحة التحكم الإدارية المرئية (Admin Dashboard)
# ==============================================================================
@app.route('/')
def admin_master_dashboard():
    dashboard_html = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>لوحة التحكم المطلقة - IPTV Master Proxy</title>
        <style>
            :root { --bg: #020617; --card: #0f172a; --accent: #0ea5e9; --text: #f8fafc; --success: #22c55e; }
            body { font-family: 'Segoe UI', Tahoma, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 25px; }
            .container { max-width: 1300px; margin: auto; }
            header { text-align: center; margin-bottom: 40px; }
            header h1 { color: #38bdf8; margin: 0; font-size: 32px; text-shadow: 0 0 25px rgba(56,189,248,0.4); }
            header p { color: #94a3b8; font-size: 16px; margin-top: 10px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .card { background: var(--card); padding: 25px; border-radius: 18px; box-shadow: 0 10px 30px rgba(0,0,0,0.6); border: 1px solid #1e293b; }
            .card h3 { margin-top: 0; color: #38bdf8; border-bottom: 2px solid #1e293b; padding-bottom: 12px; font-size: 18px; }
            .stat-value { font-size: 30px; font-weight: bold; color: var(--success); }
            table { width: 100%; border-collapse: collapse; margin-top: 15px; }
            th, td { padding: 15px; text-align: right; border-bottom: 1px solid #1e293b; font-size: 14px; }
            th { color: #38bdf8; background: #1e293b; }
            tr:hover { background: rgba(30, 41, 59, 0.5); }
            .badge { background: var(--accent); color: white; padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>⚡ نظام إدارة وتوحيد الـ IPTV الأقصى قوة</h1>
                <p>إدارة مركزية كاملة لتوحيد المصادر، التحكم بالعملاء، وتوافق تام مع تطبيقات الـ IPTV</p>
            </header>
            
            <div class="grid">
                <div class="card">
                    <h3>🌐 حالة مصادر الـ Xtream المدمجة</h3>
                    <p>إجمالي المصادر الفعالة: <span class="stat-value">{{ total_sources }}</span> مصدراً</p>
                    <p>حالة السيرفر: <span class="badge" style="background:var(--success);">مستقر وعامل 24/7 على SnapDeploy</span></p>
                </div>
                <div class="card">
                    <h3>👥 إدارة المشتركين والأجهزة</h3>
                    <p>إجمالي العملاء المسجلين: <span class="stat-value">{{ total_subs }}</span> عميلاً</p>
                    <p>بروتوكول الربط: <span class="badge">Xtream Codes API Full Proxy</span></p>
                </div>
            </div>

            <div class="card">
                <h3>📋 جدول التحكم المطلق بالعملاء وتواريخ الصلاحية</h3>
                <table>
                    <thead>
                        <tr>
                            <th>اسم المستخدم (Username)</th>
                            <th>كلمة المرور (Password)</th>
                            <th>تاريخ انتهاء الاشتراك</th>
                            <th>عدد الأجهزة المسموحة</th>
                            <th>الحالة</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for username, data in subscribers.items() %}
                        <tr>
                            <td><strong>{{ username }}</strong></td>
                            <td><code>{{ data.password }}</code></td>
                            <td><span style="color: #38bdf8; font-weight:bold;">{{ data.expiry_date }}</span></td>
                            <td><span class="badge">{{ data.max_connections }} جهاز</span></td>
                            <td><span style="color: var(--success); font-weight: bold;">{{ data.status }}</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(dashboard_html, total_sources=len(UPSTREAM_SOURCES), total_subs=len(SUBSCRIBERS_DB), subscribers=SUBSCRIBERS_DB)

# ==============================================================================
# 4. محرك البروكسي الشامل لتطبيقات الـ IPTV (Xtream API Login & Actions Proxy)
# ==============================================================================
@app.route('/player_api.php')
def xtream_player_api_proxy():
    username = request.args.get('username')
    password = request.args.get('password')
    action = request.args.get('action')
    
    # 1. التحقق الأمني من العميل
    client = SUBSCRIBERS_DB.get(username)
    if not client or client['password'] != password or client.get('status') != "Active":
        return jsonify({"user_info": {"auth": 0, "status": "Unauthorized or Expired"}}), 401
        
    # 2. بروكسي العمليات والأقسام وقوائم القنوات لتطبيق الـ IPTV
    if action and UPSTREAM_SOURCES:
        try:
            target_source = UPSTREAM_SOURCES[0]
            upstream_url = f"{target_source['dns']}/player_api.php?username={target_source['username']}&password={target_source['password']}&action={action}"
            
            for key, val in request.args.items():
                if key not in ['username', 'password']:
                    upstream_url += f"&{key}={val}"
            
            resp = requests.get(upstream_url, timeout=TIMEOUT_LIMIT)
            return resp.content, resp.status_code, dict(resp.headers)
        except Exception as e:
            return jsonify({"error": f"Upstream Action Proxy Failed: {str(e)}"}), 500

    # 3. استجابة تسجيل الدخول النظامية لتطبيق الـ IPTV
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
# 5. محرك توجيه البث الذكي (القنوات، الأفلام، المسلسلات)
# ==============================================================================
@app.route('/live/<username>/<password>/<path:stream_path>')
@app.route('/movie/<username>/<password>/<path:stream_path>')
@app.route('/series/<username>/<password>/<path:stream_path>')
def proxy_stream_dispatcher(username, password, stream_path):
    try:
        client = SUBSCRIBERS_DB.get(username)
        if not client or client['password'] != password:
            return "Unauthorized Stream Access", 401
            
        if UPSTREAM_SOURCES:
            target_source = UPSTREAM_SOURCES[0]
            media_type = request.path.split('/')[1]
            
            target_url = f"{target_source['dns']}/{media_type}/{target_source['username']}/{target_source['password']}/{stream_path}"
            return redirect(target_url, code=302)
            
        return "Error: No Upstream IPTV Sources Configured", 503
    except Exception as e:
        return f"Proxy Critical Stream Error: {str(e)}", 500

# ==============================================================================
# 6. مسارات فحص الصحة لمنع خطأ 502 على SnapDeploy
# ==============================================================================
@app.route('/health')
@app.route('/actuator/health')
def snapdeploy_health_check():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
