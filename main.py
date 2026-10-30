import os
import time
from datetime import datetime
from flask import Flask, redirect, request, jsonify, render_template_string
import requests

app = Flask(__name__)

# ذاكرة مؤقتة لدمج محتوى الـ 59 حساباً بالكامل
MASTER_CACHE = {
    "sources": [],
    "live_streams": [],
    "vod_streams": [],
    "series_streams": [],
    "live_categories": [],
    "vod_categories": [],
    "series_categories": [],
    "stream_to_source": {},
    "last_updated": 0
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

def fetch_all_content():
    global MASTER_CACHE
    current_time = time.time()
    
    if not MASTER_CACHE["sources"] or (current_time - MASTER_CACHE["last_updated"] > 900):
        all_sources = load_sources()
        MASTER_CACHE["sources"] = all_sources
        
        live_list, vod_list, series_list = [], [], []
        live_cat, vod_cat, series_cat = [], [], []
        stream_map = {}
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        for idx, src in enumerate(all_sources):
            base_url = f"{src['dns']}/player_api.php?username={src['user']}&password={src['pass']}"
            try:
                r_live = requests.get(f"{base_url}&action=get_live_streams", headers=headers, timeout=2)
                if r_live.status_code == 200:
                    streams = r_live.json()
                    if isinstance(streams, list):
                        for s in streams:
                            orig_id = s.get("stream_id")
                            if orig_id:
                                unique_id = f"L_{idx}_{orig_id}"
                                s["stream_id"] = unique_id
                                stream_map[unique_id] = {"source": src, "orig_id": orig_id}
                                live_list.append(s)
                
                r_vod = requests.get(f"{base_url}&action=get_vod_streams", headers=headers, timeout=2)
                if r_vod.status_code == 200:
                    vods = r_vod.json()
                    if isinstance(vods, list):
                        for v in vods:
                            orig_id = v.get("stream_id") or v.get("vod_id")
                            if orig_id:
                                unique_id = f"V_{idx}_{orig_id}"
                                v["stream_id"] = unique_id
                                stream_map[unique_id] = {"source": src, "orig_id": orig_id}
                                vod_list.append(v)

                r_ser = requests.get(f"{base_url}&action=get_series", headers=headers, timeout=2)
                if r_ser.status_code == 200:
                    sers = r_ser.json()
                    if isinstance(sers, list):
                        for sr in sers:
                            orig_id = sr.get("series_id")
                            if orig_id:
                                unique_id = f"S_{idx}_{orig_id}"
                                sr["series_id"] = unique_id
                                stream_map[unique_id] = {"source": src, "orig_id": orig_id}
                                series_list.append(sr)
            except:
                continue

        if all_sources:
            try:
                src = all_sources[0]
                b_url = f"{src['dns']}/player_api.php?username={src['user']}&password={src['pass']}"
                live_cat = requests.get(f"{b_url}&action=get_live_categories", headers=headers, timeout=2).json()
                vod_cat = requests.get(f"{b_url}&action=get_vod_categories", headers=headers, timeout=2).json()
                series_cat = requests.get(f"{b_url}&action=get_series_categories", headers=headers, timeout=2).json()
            except:
                pass

        MASTER_CACHE["live_streams"] = live_list
        MASTER_CACHE["vod_streams"] = vod_list
        MASTER_CACHE["series_streams"] = series_list
        MASTER_CACHE["live_categories"] = live_cat if isinstance(live_cat, list) else []
        MASTER_CACHE["vod_categories"] = vod_cat if isinstance(vod_cat, list) else []
        MASTER_CACHE["series_categories"] = series_cat if isinstance(series_cat, list) else []
        MASTER_CACHE["stream_to_source"] = stream_map
        MASTER_CACHE["last_updated"] = current_time

USERS = {
    "bashar": {"password": "123", "max_connections": 2, "expiry": "2027-12-31"},
    "12345": {"password": "12345", "max_connections": 1, "expiry": "2026-11-08"}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>لوحة تحكم وإدارة اشتراكات IPTV الشاملة</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: Tahoma, sans-serif; margin: 0; padding: 15px; }
        .container { max-width: 900px; margin: auto; background: #1e293b; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        h1, h2 { color: #38bdf8; text-align: center; }
        .stats { display: flex; justify-content: space-around; background: #334155; padding: 12px; border-radius: 8px; margin-bottom: 15px; font-size: 13px; flex-wrap: wrap; gap: 5px; }
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
        <h1>لوحة تحكم وإدارة اشتراكات IPTV الشاملة</h1>
        
        <div class="stats">
            <div>📡 إجمالي الحسابات المدمجة: <strong>{{ sources_count }}</strong></div>
            <div>📺 إجمالي القنوات: <strong>{{ live_count }}</strong></div>
            <div>🎬 الأفلام والمسلسلات: <strong>{{ vod_count + series_count }}</strong></div>
            <div>👥 المستخدمين: <strong>{{ users|length }}</strong></div>
        </div>

        <div class="url-box">
            <span>🌐 رابط السيرفر الأساسي (Server URL):</span>
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
    fetch_all_content()
    # تثبيت الرابط ليظهر http://sxstreem.net في اللوحة
    host_url = "http://sxstreem.net"
    return render_template_string(
        HTML_TEMPLATE, 
        sources_count=len(MASTER_CACHE["sources"]),
        live_count=len(MASTER_CACHE["live_streams"]),
        vod_count=len(MASTER_CACHE["vod_streams"]),
        series_count=len(MASTER_CACHE["series_streams"]),
        users=USERS, 
        host_url=host_url
    )

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
    fetch_all_content()
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
    
    if action == 'get_live_categories':
        return jsonify(MASTER_CACHE["live_categories"])
    elif action == 'get_live_streams':
        return jsonify(MASTER_CACHE["live_streams"])
    elif action == 'get_vod_categories':
        return jsonify(MASTER_CACHE["vod_categories"])
    elif action == 'get_vod_streams':
        return jsonify(MASTER_CACHE["vod_streams"])
    elif action == 'get_series_categories':
        return jsonify(MASTER_CACHE["series_categories"])
    elif action == 'get_series':
        return jsonify(MASTER_CACHE["series_streams"])
    elif action in ['get_series_info', 'get_vod_info']:
        stream_id = request.args.get('series_id') or request.args.get('vod_id')
        mapping = MASTER_CACHE["stream_to_source"].get(str(stream_id))
        if mapping:
            src = mapping["source"]
            orig_id = mapping["orig_id"]
            target_url = f"{src['dns']}/player_api.php?username={src['user']}&password={src['pass']}&action={action}&{'series_id' if 'series_id' in request.args else 'vod_id'}={orig_id}"
            try:
                r = requests.get(target_url, timeout=3)
                if r.status_code == 200:
                    return jsonify(r.json())
            except:
                pass
        return jsonify({})

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
            "url": "sxstreem.net",
            "port": "80",
            "https_port": "443",
            "server_protocol": "http",
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
    
    mapping = MASTER_CACHE["stream_to_source"].get(str(stream_id))
    if mapping:
        src = mapping["source"]
        orig_id = mapping["orig_id"]
        target_url = f"{src['dns']}/live/{src['user']}/{src['pass']}/{orig_id}.ts"
        return redirect(target_url, code=302)
        
    sources = MASTER_CACHE["sources"]
    if sources:
        src = sources[0]
        return redirect(f"{src['dns']}/live/{src['user']}/{src['pass']}/{stream_id}.ts", code=302)
        
    return "All sources offline", 503

@app.route('/movie/<username>/<password>/<movie_id>.<ext>')
def movie_proxy(username, password, movie_id, ext):
    if username not in USERS or USERS[username]['password'] != password:
        return "Unauthorized", 401
    
    mapping = MASTER_CACHE["stream_to_source"].get(str(movie_id))
    if mapping:
        src = mapping["source"]
        orig_id = mapping["orig_id"]
        target_url = f"{src['dns']}/movie/{src['user']}/{src['pass']}/{orig_id}.{ext}"
        return redirect(target_url, code=302)
        
    sources = MASTER_CACHE["sources"]
    if sources:
        src = sources[0]
        return redirect(f"{src['dns']}/movie/{src['user']}/{src['pass']}/{movie_id}.{ext}", code=302)
        
    return "Offline", 503

@app.route('/series/<username>/<password>/<path:path_info>')
def series_proxy(username, password, path_info):
    if username not in USERS or USERS[username]['password'] != password:
        return "Unauthorized", 401
        
    parts = path_info.split('/')
    series_id = parts[0].split('.')[0] if parts else ""
    
    mapping = MASTER_CACHE["stream_to_source"].get(str(series_id))
    if mapping:
        src = mapping["source"]
        orig_path = path_info.replace(str(series_id), str(mapping["orig_id"]), 1)
        target_url = f"{src['dns']}/series/{src['user']}/{src['pass']}/{orig_path}"
        return redirect(target_url, code=302)
        
    sources = MASTER_CACHE["sources"]
    if sources:
        src = sources[0]
        return redirect(f"{src['dns']}/series/{src['user']}/{src['pass']}/{path_info}", code=302)
        
    return "Offline", 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
