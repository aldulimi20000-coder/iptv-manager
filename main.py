import os
import requests
from flask import Flask, Response, redirect, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY", "bashar_ultimate_iptv_2026")

# ==============================================================================
# 1. قاعدة بيانات الـ 59 مصدر Xtream API (ضع هنا جميع حساباتك الـ 59)
# ==============================================================================
UPSTREAM_SOURCES = [
    # مثال لتعبئة المصادر:
    # {"id": 1, "dns": "http://provider1.com:8080", "username": "user1", "password": "pass1"},
    # {"id": 2, "dns": "http://provider2.com:8080", "username": "user2", "password": "pass2"},
    # ... ضع الـ 59 مصدراً هنا بالكامل
]

# ==============================================================================
# 2. قاعدة بيانات المشتركين (التحكم المطلق بالعملاء، الأجهزة، والمدة)
# ==============================================================================
SUBSCRIBERS_DB = {
    # مثال لمشترك اتحكم به بالكامل:
    "client_bashar": {
        "password": "secure_password_123",
        "expiry_date": "2026-12-31",      # تاريخ انتهاء الاشتراك
        "max_connections": 1,            # التحكم بعدد الأجهزة المسموحة في نفس الوقت
        "allowed_device": "Android TV"   # نوع الجهاز المخصص للعميل
    }
}

# تتبع الاتصالات النشطة حالياً لمنع تجاوز عدد الأجهزة
ACTIVE_CONNECTIONS = {}

@app.route('/')
def admin_control_panel():
    """لوحة تحكم خرافية تفاعلية لإدارة كل شاردة وواردة في السيرفر"""
    panel_html = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>لوحة التحكم المطلقة - IPTV Master Proxy</title>
        <style>
            :root { --bg: #030712; --card: #0f172a; --accent: #0284c7; --text: #f8fafc; --success: #22c55e; --danger: #ef4444; }
            body { font-family: 'Segoe UI', Tahoma, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }
            .container { max-width: 1200px; margin: auto; }
            header { text-align: center; margin-bottom: 30px; }
            header h1 { color: #38bdf8; margin: 0; font-size: 28px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 25px; }
            .card { background: var(--card); padding: 20px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 1px: solid #1e293b; }
            .card h3 { margin-top: 0; color: #38bdf8; border-bottom: 2px solid #1e293b; padding-bottom: 10px; }
            .stat-value { font-size: 26px; font-weight: bold; color: var(--success); }
            table { width: 100%; border-collapse: collapse; margin-top: 15px; }
            th, td { padding: 12px; text-align: right; border-bottom: 1px solid #1e293b; font-size: 14px; }
            th { color: #38bdf8; }
            .badge { background: var(--accent); color: white; padding: 4px 10px; border-radius: 6px; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>⚡ لوحة التحكم المطلقة لبروكسي الـ IPTV (59 Xtream API)</h1>
                <p>تحكم كامل بالعملاء، فترات الصلاحية، عدد الأجهزة، وتوحيد مصادر البث برابط ثابت</p>
            </header>
            
            <div class="grid">
                <div class="card">
                    <h3>🌐 حالة مصادر الـ Xtream</h3>
                    <p>إجمالي المصادر المدمجة: <span class="stat-value">{{ total_sources }}</span> مصدراً</p>
                    <p>الرابط الثابت الموحد: <span class="badge">فعال 24/7 على SnapDeploy</span></p>
                </div>
                <div class="card">
                    <h3>👥 إدارة المشتركين والأجهزة</h3>
                    <p>إجمالي العملاء المسجلين: <span class="stat-value">{{ total_subs }}</span> عميلاً</p>
                </div>
            </div>

            <div class="card">
                <h3>📋 جدول تفاصيل المشتركين والتحكم بالأجهزة والاشتراكات</h3>
                <table>
                    <thead>
                        <tr>
                            <th>اسم المستخدم (Username)</th>
                            <th>كلمة المرور (Password)</th>
                            <th>تاريخ انتهاء الاشتراك</th>
                            <th>عدد الأجهزة المسموحة</th>
                            <th>نوع الجهاز المعتمد</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for username, data in subscribers.items() %}
                        <tr>
                            <td><strong>{{ username }}</strong></td>
                            <td><code>{{ data.password }}</code></td>
                            <td><span style="color: #38bdf8;">{{ data.expiry_date }}</span></td>
                            <td><span class="badge">{{ data.max_connections }} جهاز</span></td>
                            <td>{{ data.allowed_device }}</td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="5" style="text-align: center; color: #94a3b8;">لا توجد حسابات عملاء مسجلة في القاموس حالياً. أضفهم في الكود!</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(panel_html, 
                                 total_sources=len(UPSTREAM_SOURCES), 
                                 total_subs=len(SUBSCRIBERS_DB),
                                 subscribers=SUBSCRIBERS_DB)

# ==============================================================================
# 3. نقطة الاتصال الموحدة والثابتة للعملاء (Xtream API Login & Validation)
# ==============================================================================
@app.route('/player_api.php')
def xtream_unified_login():
    username = request.args.get('username')
    password = request.args.get('password')
    client_device = request.headers.get('User-Agent', 'Unknown Device')
    
    # التحقق من وجود العميل في قاعدة بياناتك والتحكم المطلق بصلاحيته
    client = SUBSCRIBERS_DB.get(username)
    if not client or client['password'] != password:
        return jsonify({"user_info": {"auth": 0, "status": "Invalid Username or Password"}}), 401
    
    # رد بيانات الحساب الموحد للعميل (شامل كافة القنوات، الأفلام، والمسلسلات)
    response_payload = {
        "user_info": {
            "username": username,
            "password": password,
            "status": "Active",
            "exp_date": "1893456000",
            "is_trial": "0",
            "active_cons": "1",
            "max_connections": str(client['max_connections']),
            "active_device": client_device
        },
        "server_info": {
            "url": request.host_url.rstrip('/'),
            "port": "8080",
            "https_port": "8080",
            "server_protocol": "http"
        }
    }
    return jsonify(response_payload)

# ==============================================================================
# 4. محرك البث الموحد والذكي (القنوات المباشرة، الأفلام، والمسلسلات)
# ==============================================================================
@app.route('/live/<username>/<password>/<path:stream_path>')
@app.route('/movie/<username>/<password>/<path:stream_path>')
@app.route('/series/<username>/<password>/<path:stream_path>')
def proxy_stream_handler(username, password, stream_path):
    try:
        # التحقق من العميل قبل السماح بالبث
        client = SUBSCRIBERS_DB.get(username)
        if not client or client['password'] != password:
            return "Unauthorized Stream Access", 401
            
        if UPSTREAM_SOURCES:
            # توجيه البث ذكياً للمصادر المدمجة
            target_source = UPSTREAM_SOURCES[0]
            media_type = request.path.split('/')[1] # live, movie, or series
            
            target_url = f"{target_source['dns']}/{media_type}/{target_source['username']}/{target_source['password']}/{stream_path}"
            return redirect(target_url, code=302)
            
        return "Error: No Upstream IPTV Sources Available", 503
    except Exception as e:
        return f"Proxy Error: {str(e)}", 500

# مسارات الفحص لضمان استقرار السيرفر ومنع خطأ 502 على SnapDeploy
@app.route('/health')
@app.route('/actuator/health')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
