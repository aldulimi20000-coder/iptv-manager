import os
import time
from datetime import datetime
from flask import Flask, redirect, request, jsonify, render_template_string
import requests
import concurrent.futures

app = Flask(__name__)

# تخزين مؤقت لحالة المصادر لتفادي إعادة الفحص البطيء مع كل طلب
CACHE = {
    "sources": [],
    "last_checked": 0,
    "active_index": 0
}

def load_sources():
    sources = []
    try:
        if os.path.exists('sources.txt'):
            with open('sources.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 3:
                        sources.append({
                            "dns": parts[0].strip(),
                            "user": parts[1].strip(),
                            "pass": parts[2].strip()
                        })
    except Exception as e:
        print(f"Error loading sources: {e}")
    return sources

def test_source(source):
    try:
        url = f"{source['dns']}/player_api.php?username={source['user']}&password={source['pass']}"
        r = requests.get(url, timeout=2.5, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code == 200:
            data = r.json()
            if data.get("user_info", {}).get("auth") == 1:
                return source
    except:
        pass
    return None

def get_active_sources(force_refresh=False):
    global CACHE
    current_time = time.time()
    # إعادة الفحص التلقائي كل 10 دقائق لتحديث الحسابات التي عادت للعمل أو ماتت
    if force_refresh or not CACHE["sources"] or (current_time - CACHE["last_checked"] > 600):
        all_sources = load_sources()
        working = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            results = executor.map(test_source, all_sources)
            for res in results:
                if res:
                    working.append(res)
        
        CACHE["sources"] = working if working else all_sources
        CACHE["last_checked"] = current_time
    return CACHE["sources"]

USERS = {
    "bashar": {"password": "123", "max_connections": 2, "expiry": "2027-12-31"},
    "12345": {"password": "12345", "max_connections": 1, "expiry": "2026-11-08"}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>لوحة تحكم مدير IPTV</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: Tahoma, sans-serif; margin: 0; padding: 15px; }
        .container { max-width: 900px; margin: auto; background: #1e293b; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        h1, h2 { color: #38bdf8; text-align: center; }
        .stats { display: flex; justify-content: space-around; background: #334155; padding: 12px; border-radius: 8px; margin-bottom: 15px; font-size: 14px; }
        .url-box { background: #0284c7; padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; }
        .url-box input { width: 100%; padding: 8px; background: #0f172a; color: #38bdf8; border: none; border-radius: 5px; text-align: center; font-size: 15px; font-weight: bold; margin-top: 5px; box-sizing: border-box; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }
        th, td { padding: 10px; border-bottom: 1px solid #475569; text-align: center; word-break: break-all; }
        th { background: #0284c7; color: #fff; }
        form { background: #334155; padding: 15px; border-radius: 8px; margin-top: 20px; }
        input, button { padding: 10px; margin: 5px 0; width: 100%; box-sizing: border-box; border-radius: 5px; border: none; }
        input[type="text"], input[type="password"], input[type="number"], input[type="date"] { background: #1e293b; color: #fff; border: 1px solid #475569; }
        button { background: #22c55e; color: #fff; font-weight: bold; cursor: pointer; }
        button:hover { background: #16a34a; }
        .btn-danger { background: #ef4444; width: auto; padding: 5px 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>لوحة تحكم وإدارة اشتراكات IPTV</h1>
        
        <div class="stats">
            <div>⚡ الحسابات النشطة (تعمل بالذات): <strong>{{ sources_count }}</strong></div>
            <div>👥 المستخدمين: <strong>{{ users|length }}</strong></div>
        </div>

        <div class="url-box">
            <span>🌐 رابط السيرفر الأساسي (Server URL) لإعطائه للزبائن:</span>
            <input type="text" value="{{ host_url }}" readonly onclick="this.select();">
        </div>

        <h2>إضافة مستخدم جديد</h2>
        <form method="POST" action="/add_user">
            <input type="text" name="username" placeholder="اسم المستخدم (مثال: client1)" required>
            <input type="text" name="password" placeholder="كلمة المرور (مثال: 456)" required>
            <input type="number" name="max_connections" placeholder="عدد الاتصالات (مثال: 1)" value="1" required>
            <label style="display:block; text-align:right; margin-top:5px; font-size:13px;">تاريخ انتهاء الاشتراك:</label>
            <input type="date" name="expiry" required>
            <button type="submit">حفظ / إضافة المستخدم</button>
        </form>

        <h2>قائمة المستخدمين وبياناتهم للزبائن</h2>
        <table>
            <tr>
                <th>المستخدم</th>
                <th>كلمة المرور</th>
                <th>اتصالات</th>
                <th>الانتهاء</th>
                <th>الإجراء</th>
            </tr>
            {% for uname, data in users.items() %}
            <tr>
                <td><strong>{{ uname }}</strong></td>
                <td>{{ data.password }}</td>
                <td>{{ data.max_connections }}</td>
                <td>{{ data.expiry }}</td>
                <td>
                    {% if uname != 'bashar' %}
                    <form method="POST" action="/delete_user" style="margin:0; padding:0; background:none;">
                        <input type="hidden" name="username" value="{{ uname }}">
                        <button type="submit" class="btn-danger">حذف</button>
                    </form>
                    {% else %}
                    <span style="color:#94a3b8; font-size:11px;">المدير</span>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    host_url = request.host_url.rstrip('/')
    sources = get_active_sources()
    return render_template_string(HTML_TEMPLATE, sources_count=len(sources), users=USERS, host_url=host_url)

@app.route('/add_user', methods=['POST'])
def add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    max_conn = int(request.form.get('max_connections', 1))
    expiry = request.form.get('expiry')
    if username and password:
        USERS[username] = {
            "password": password,
            "max_connections": max_conn,
            "expiry": expiry
        }
    return redirect('/')

@app.route('/delete_user', methods=['POST'])
def delete_user():
    username = request.form.get('username')
    if username in USERS and username != "bashar":
        del USERS[username]
    return redirect('/')

@app.route('/player_api.php')
def xtream_api():
    username = request.args.get('username')
    password = request.args.get('password')
    action = request.args.get('action')
    
    if username not in USERS or USERS[username]['password'] != password:
        return jsonify({"user_info": {"auth": 0, "status": "Disabled"}})
    
    expiry_str = USERS[username].get('expiry', '2099-12-31')
    try:
        expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
        if datetime.now() > expiry_date:
            return jsonify({"user_info": {"auth": 0, "status": "Expired", "message": "Subscription Expired"}})
        exp_timestamp = int(expiry_date.timestamp())
    except:
        exp_timestamp = int(datetime.now().timestamp()) + 31536000
    
    sources = get_active_sources()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    # نظام التجربة الذكية: إذا فشل مصدر، يجرب المصدر التالي تلقائياً حتى ينجح
    if action in ['get_live_categories', 'get_live_streams', 'get_vod_categories', 'get_vod_streams', 'get_series_categories', 'get_series']:
        for source in sources:
            try:
                target_url = f"{source['dns']}/player_api.php?username={source['user']}&password={source['pass']}&action={action}"
                for key, val in request.args.items():
                    if key not in ['username', 'password', 'action']:
                        target_url += f"&{key}={val}"
                
                r = requests.get(target_url, headers=headers, timeout=3)
                if r.status_code == 200:
                    data = r.json()
                    if data:
                        return jsonify(data)
            except:
                continue
        return jsonify([])

    return jsonify({
        "user_info": {
            "username": username,
            "password": password,
            "message": "",
            "auth": 1,
            "status": "Active",
            "exp_date": str(exp_timestamp),
            "is_trial": "0",
            "active_cons": "1",
            "max_connections": str(USERS[username].get('max_connections', 1)),
            "allowed_output_formats": ["m3u8", "ts", "rtmp"]
        },
        "server_info": {
            "url": request.host,
            "port": "443",
            "https_port": "443",
            "server_protocol": "https",
            "rtmp_port": "8080",
            "timezone": "UTC",
            "timestamp_now": int(datetime.now().timestamp()),
            "time_now": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "process": True
        }
    })

@app.route('/live/<username>/<password>/<stream_id>.ts')
def stream_proxy(username, password, stream_id):
    if username not in USERS or USERS[username]['password'] != password:
        return "Unauthorized", 401
    
    sources = get_active_sources()
    if sources:
        # التبديل الذكي التلقائي: اختيار المصدر بناءً على رقم القناة مع نظام تدوير تلقائي
        idx = abs(hash(str(stream_id))) % len(sources)
        source = sources[idx]
        target_url = f"{source['dns']}/live/{source['user']}/{source['pass']}/{stream_id}.ts"
        return redirect(target_url, code=302)
        
    return "All sources offline", 503

@app.route('/movie/<username>/<password>/<int:movie_id>.<ext>')
def movie_proxy(username, password, movie_id, ext):
    if username not in USERS or USERS[username]['password'] != password:
        return "Unauthorized", 401
    sources = get_active_sources()
    if sources:
        idx = abs(hash(str(movie_id))) % len(sources)
        source = sources[idx]
        target_url = f"{source['dns']}/movie/{source['user']}/{source['pass']}/{movie_id}.{ext}"
        return redirect(target_url, code=302)
    return "Offline", 503

@app.route('/series/<username>/<password>/<int:series_id>.<ext>')
def series_proxy(username, password, series_id, ext):
    if username not in USERS or USERS[username]['password'] != password:
        return "Unauthorized", 401
    sources = get_active_sources()
    if sources:
        idx = abs(hash(str(series_id))) % len(sources)
        source = sources[idx]
        target_url = f"{source['dns']}/series/{source['user']}/{source['pass']}/{series_id}.{ext}"
        return redirect(target_url, code=302)
    return "Offline", 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
