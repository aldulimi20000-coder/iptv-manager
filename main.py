import os
import requests
from flask import Flask, Response, redirect, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY", "bashar_supreme_ultimate_iptv_2026")

# ==============================================================================
# 1. قاعدة بيانات الـ 59 مصدر Xtream API الأصلية (ضع هنا جميع حساباتك الـ 59 بالكامل)
# ==============================================================================
UPSTREAM_SOURCES = [
    # مثال هيكلي لكل مصدر:
    # {"id": 1, "dns": "http://provider1.com:8080", "username": "user1", "password": "pass1"},
    # {"id": 2, "dns": "http://provider2.com:8080", "username": "user2", "password": "pass2"},
    # ... أكمل حتى الـ 59 مصدراً لتوزيع الأحمال بكفاءة قصوى
]

# ==============================================================================
# 2. قاعدة بيانات المشتركين (التحكم المطلق: الصلاحية، عدد الأجهزة، وكلمات المرور)
# ==============================================================================
SUBSCRIBERS_DB = {
    # مثال لتحكمك الكامل بمشترك معين وتطبيق الـ IPTV الخاص به:
    "client_bashar": {
        "password": "123",
        "expiry_date": "2026-12-31",      # تاريخ انتهاء الاشتراك بدقة
        "max_connections": 1,            # التحكم المطلق بعدد الأجهزة المسموحة في نفس الوقت
        "allowed_device": "Android TV / IPTV Smarters / TiviMate"
    }
}

# ==============================================================================
# 3. لوحة التحكم الإدارية المطلقة (Dashboard)
# ==============================================================================
@app.route('/')
def admin_control_panel():
    """لوحة تحكم مرئية وتفاعلية خرافية لإدارة كل شاردة وواردة في السيرفر وتطبيقات الـ IPTV"""
    dashboard_html = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>لوحة التحكم المطلقة والقصوى - IPTV Master Proxy</title>
        <style>
            :root { --bg: #020617; --card: #0f172a; --accent: #0ea5e9; --text: #f8fafc; --success: #22c55e; }
            body { font-family: 'Segoe UI', Tahoma, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }
            .container { max-width: 1250px; margin: auto; }
            header { text-align: center; margin-bottom: 35px; }
            header h1 { color: #38bdf8; margin: 0; font-size: 28px; text-shadow: 0 0 20px rgba(56,189,248,0.3); }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .card { background: var(--card); padding: 25px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.6); border: 1px solid #1e293b; }
            .card h3 { margin-top: 0; color: #38bdf8; border-bottom: 2px solid #1e293b; padding-bottom: 12px; font-size: 18px; }
            .stat-value { font-size: 28px; font-weight: bold; color: var(--success); }
            table { width: 100%; border-collapse: collapse; margin-top: 15px; }
            th, td { padding: 14px; text-align: right; border-bottom: 1px solid #1e293b; font-size: 14px; }
            th { color: #38bdf8; }
            .badge { background: var(--accent); color: white; padding: 5px 12px; border-radius: 8px; font-size: 12px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>⚡ نظام إدارة وتوحيد الـ IPTV الأقصى قوة (59 Xtream API)</h1>
                <p>إدارة مركزية لتوحيد المصادر برابط ثابت، التحكم بفترات الصلاحية، وتوافق تام مع تطبيقات الـ IPTV</p>
            </header>
            
            <div class="grid">
                <div class="card">
                    <h3>🌐 حالة مصادر الـ Xtream المدمجة</h3>
                    <p>إجمالي المصادر الفعالة: <span class="stat-value">{{ total_sources }}</span> مصدراً</p>
                    <p>حالة الرابط الموحد: <span class="badge" style="background:var(--success);">مستقر 24/7 على SnapDeploy</span></p>
                </div>
                <div class="card">
                    <h3>👥 إدارة المشتركين والأجهزة</h3>
                    <p>إجمالي العملاء المسجلين: <span class="stat-value">{{ total_subs }}</span> عميلاً</p>
                    <p>توافق التطبيقات: <span class="badge">Xtream API Protocol Active</span></p>
                </div>
            </div>

            <div class="card">
                <h3>📋 جدول التحكم المطلق بالعملاء والاشتراكات وتطبيقاتهم</h3>
                <table>
                    <thead>
                        <tr>
                            <th>اسم المستخدم (Username)</th>
                            <th>كلمة المرور (Password)</th>
                            <th>تاريخ انتهاء الاشتراك</th>
                            <th>الأجهزة المسموحة</th>
                            <th>نوع الجهاز المعتمد</th>
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
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="5" style="text-align: center; color: #94a3b8; padding: 20px;">لا توجد حسابات عملاء مسجلة حالياً. أضفهم في SUBSCRIBERS_DB!</td>
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
# 4. نقطة الاتصال وتوافق تطبيقات IPTV (Xtream API Login & Actions Proxy)
# ==============================================================================
@app.route('/player_api.php')
def xtream_player_api():
    username = request.args.get('username')
    password = request.args.get('password')
    action = request.args.get('action')
    client_device = request.headers.get('User-Agent', 'Unknown Device')
    
    # التحقق من العميل
    client = SUBSCRIBERS_DB.get(username)
    if not client or client['password'] != password:
        return jsonify({"user_info": {"auth": 0, "status": "Invalid"}}), 401
        
    # ميزة خارقة: إذا طلب تطبيق الـ IPTV أقساماً أو قوائم قنوات (Actions)، نقوم بجلبها من المصدر الأصلي وتمريرها للتطبيق بسلاسة
    if action and UPSTREAM_SOURCES:
        try:
            src = UPSTREAM_SOURCES[0]
            upstream_url = f"{src['dns']}/player_api.php?username={src['username']}&password={src['password']}&action={action}"
            for key, val in request.args.items():
                if key not in ['username', 'password']:
                    upstream_url += f"&{key}={val}"
            
            resp = requests.get(upstream_url, timeout=15)
            return resp.content, resp.status_code, resp.headers.items()
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # استجابة تسجيل الدخول الأساسية التي يتوقعها تطبيق الـ IPTV
    response_data = {
        "user_info": {
            "username
