import os
import time
import logging
import threading
import requests
from flask import Flask, Response, redirect, request, jsonify, render_template_string
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# ==============================================================================
# 0. التهيئة العسكرية المتقدمة لنظام السجلات والتتبع (Enterprise Audit Logger)
# ==============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] (INTERACTIVE_CORE) >>> %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("IPTV_INTERACTIVE_MASTER")

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY", "bashar_interactive_supreme_master_2026")
TIMEOUT_LIMIT = 8
CACHE_TTL = 300
cache_lock = threading.Lock()

# ==============================================================================
# 1. الذاكرة المؤقتة الذكية وإدارة الملفات (Thread-Safe Caching & Storage Engine)
# ==============================================================================
_INTERACTIVE_CACHE = {
    "active_sources": [],
    "raw_count": 0,
    "last_updated": 0,
    "request_counter": 0,
    "error_counter": 0
}

# قاعدة بيانات المشتركين القابلة للتعديل والتحكم المباشر
SUBSCRIBERS_DB = {
    "client_bashar": {
        "password": "123",
        "expiry_date": "2026-12-31",
        "max_connections": 5,
        "allowed_device": "Android TV / TiviMate / IPTV Smarters",
        "status": "Active",
        "current_active_connections": 1
    }
}

def load_sources_from_disk_interactive():
    parsed_sources = []
    try:
        if os.path.exists("sources.txt"):
            with open("sources.txt", "r", encoding="utf-8") as file_obj:
                for line_num, raw_line in enumerate(file_obj, 1):
                    cleaned_line = raw_line.strip()
                    if cleaned_line and not cleaned_line.startswith("#"):
                        segments = cleaned_line.split(",")
                        if len(segments) >= 3:
                            parsed_sources.append({
                                "index": line_num,
                                "dns": segments[0].strip(),
                                "username": segments[1].strip(),
                                "password": segments[2].strip()
                            })
    except Exception as err:
        logger.error(f"خطأ في قراءة المصادر: {str(err)}")
    return parsed_sources

def evaluate_single_upstream_interactive(node_info):
    try:
        health_check_url = f"{node_info['dns']}/player_api.php?username={node_info['username']}&password={node_info['password']}"
        response = requests.get(health_check_url, timeout=3.5)
        if response.status_code == 200:
            payload_data = response.json()
            if isinstance(payload_data, dict) and ("user_info" in payload_data or "server_info" in payload_data):
                return node_info
    except Exception:
        pass
    return None

def fetch_and_filter_active_interactive():
    global _INTERACTIVE_CACHE
    now_timestamp = time.time()
    
    with cache_lock:
        if now_timestamp - _INTERACTIVE_CACHE["last_updated"] < CACHE_TTL and _INTERACTIVE_CACHE["active_sources"]:
            return _INTERACTIVE_CACHE["active_sources"]
            
    raw_list = load_sources_from_disk_interactive()
    with cache_lock:
        _INTERACTIVE_CACHE["raw_count"] = len(raw_list)
        
    functional_sources = []
    if raw_list:
        with ThreadPoolExecutor(max_workers=45) as thread_pool:
            eval_results = thread_pool.map(evaluate_single_upstream_interactive, raw_list)
        for res_node in eval_results:
            if res_node:
                functional_sources.append(res_node)
                
    if not functional_sources and raw_list:
        functional_sources = raw_list[:1]
        
    with cache_lock:
        _INTERACTIVE_CACHE["active_sources"] = functional_sources
        _INTERACTIVE_CACHE["last_updated"] = now_timestamp
        
    return functional_sources

# ==============================================================================
# 2. واجهة التحكم الإدارية التفاعلية بالكامل (Interactive Admin Dashboard)
# ==============================================================================
@app.route('/', methods=['GET', 'POST'])
def interactive_admin_panel():
    message = ""
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        # إضافة مشترك جديد مباشرة من المتصفح
        if form_type == 'add_subscriber':
            new_user = request.form.get('username').strip()
            new_pass = request.form.get('password').strip()
            new_exp = request.form.get('expiry_date').strip()
            new_max = int(request.form.get('max_connections', 2))
            
            if new_user and new_pass:
                SUBSCRIBERS_DB[new_user] = {
                    "password": new_pass,
                    "expiry_date": new_exp if new_exp else "2026-12-31",
                    "max_connections": new_max,
                    "allowed_device": "All IPTV Devices",
                    "status": "Active",
                    "current_active_connections": 0
                }
                message = f"تم إضافة المشترك ({new_user}) بنجاح!"

        # حذف مشترك
        elif form_type == 'delete_subscriber':
            target_user = request.form.get('username')
            if target_user in SUBSCRIBERS_DB and target_user != "client_bashar":
                del SUBSCRIBERS_DB[target_user]
                message = f"تم حذف المشترك ({target_user}) بنجاح!"

        # إضافة مصدر Xtream جديد مباشرة إلى ملف sources.txt من الواجهة
        elif form_type == 'add_source':
            new_dns = request.form.get('dns').strip()
            new_usr = request.form.get('s_username').strip()
            new_pwd = request.form.get('s_password').strip()
            if new_dns and new_usr and new_pwd:
                with open("sources.txt", "a", encoding="utf-8") as f:
                    f.write(f"\n{new_dns},{new_usr},{new_pwd}")
                # إعادة ضبط الكاش لتحديث المصادر فوراً
                with cache_lock:
                    _INTERACTIVE_CACHE["last_updated"] = 0
                message = "تم إضافة المصدر الجديد بنجاح وتم تحديث السيرفر!"

    raw_sources_list = load_sources_from_disk_interactive()
    active_sources_list = fetch_and_filter_active_interactive()
    
    dashboard_html = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>لوحة التحكم التفاعلية المطلقة - IPTV Master</title>
        <style>
            :root {{ --bg: #030712; --card: #0f172a; --accent: #0ea5e9; --text: #f8fafc; --success: #22c55e; --danger: #ef4444; --border: #1e293b; }}
            body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }}
            .container {{ max-width: 1300px; margin: auto; }}
            header {{ text-align: center; margin-bottom: 25px; padding: 25px; background: var(--card); border-radius: 18px; border: 1px solid var(--border); }}
            header h1 {{ color: var(--accent); margin: 0; font-size: 26px; }}
            .alert {{ background: #065f46; color: #6ee7b7; padding: 12px; border-radius: 10px; margin-bottom: 20px; text-align: center; font-weight: bold; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; margin-bottom: 25px; }}
            .card {{ background: var(--card); padding: 20px; border-radius: 18px; border: 1px solid var(--border); box-shadow: 0 8px 25px rgba(0,0,0,0.5); }}
            .card h3 {{ margin-top: 0; color: var(--accent); border-bottom: 2px solid var(--border); padding-bottom: 10px; font-size: 17px; }}
            .stat-val {{ font-size: 30px; font-weight: bold; color: var(--success); }}
            input, select {{ width: 100%; padding: 10px; margin: 8px 0; background: #020617; border: 1px solid var(--border); color: white; border-radius: 8px; box-sizing: border-box; }}
            button {{ background: var(--accent); color: white; border: none; padding: 10px 15px; border-radius: 8px; cursor: pointer; font-weight: bold; width: 100%; margin-top: 5px; }}
            button:hover {{ opacity: 0.9; }}
            button.danger {{ background: var(--danger); }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; min-width: 600px; }}
            th, td {{ padding: 12px; text-align: right; border-bottom: 1px solid var(--border); font-size: 13px; }}
            th {{ color: var(--accent); background: var(--border); }}
            .badge {{ background: var(--accent); color: white; padding: 4px 10px; border-radius: 6px; font-size: 11px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>⚡ لوحة التحكم التفاعلية بالكامل - IPTV Control Panel</h1>
                <p>تحكم مطلق بالمشتركين، أضف أو احذف العملاء، وتحكم بمصادر الـ Xtream مباشرة من المتصفح</p>
            </header>
            
            {'<div class="alert">' + message + '</div>' if message else ''}
            
            <div class="grid">
                <!-- إحصائيات النظام -->
                <div class="card">
                    <h3>📊 حالة السيرفر والمصادر</h3>
                    <p>إجمالي المصادر في الملف: <span class="stat-val" style="color:var(--accent);">{len(raw_sources_list)}</span></p>
                    <p>المصادر النشطة والشغالة: <span class="stat-val">{len(active_sources_list)}</span></p>
                    <p>إجمالي المشتركين المسجلين: <span class="stat-val">{len(SUBSCRIBERS_DB)}</span></p>
                </div>

                <!-- إضافة مشترك جديد -->
                <div class="card">
                    <h3>➕ إضافة مشترك جديد</h3>
                    <form method="POST">
                        <input type="hidden" name="form_type" value="add_subscriber">
                        <input type="text" name="username" placeholder="اسم المستخدم (Username)" required>
                        <input type="text" name="password" placeholder="كلمة المرور (Password)" required>
                        <input type="text" name="expiry_date" placeholder="تاريخ الانتهاء (YYYY-MM-DD)" value="2026-12-31">
                        <input type="number" name="max_connections" placeholder="عدد الأجهزة المسموحة" value="2">
                        <button type="submit">حفظ وإضافة العميل</button>
                    </form>
                </div>

                <!-- إضافة مصدر Xtream جديد -->
                <div class="card">
                    <h3>🌐 إضافة مصدر Xtream جديد</h3>
                    <form method="POST">
                        <input type="hidden" name="form_type" value="add_source">
                        <input type="text" name="dns" placeholder="رابط السيرفر (http://domain.com:port)" required>
                        <input type="text" name="s_username" placeholder="اسم المستخدم للمصدر" required>
                        <input type="text" name="s_password" placeholder="كلمة المرور للمصدر" required>
                        <button type="submit">إضافة المصدر وتحديث الفحص</button>
                    </form>
                </div>
            </div>

            <!-- جدول المشتركين والتفاعل معهم -->
            <div class="card">
                <h3>📋 جدول المشتركين والإدارة المباشرة</h3>
                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>اسم المستخدم</th>
                                <th>كلمة المرور</th>
                                <th>تاريخ الانتهاء</th>
                                <th>الأجهزة</th>
                                <th>الحالة</th>
                                <th>إجراءات الحذف</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f"<tr><td><strong>{uname}</strong></td><td><code>{info['password']}</code></td><td>{info['expiry_date']}</td><td><span class='badge'>{info['max_connections']} جهاز</span></td><td style='color:var(--success); font-weight:bold;'>{info['status']}</td><td>" + (f"<form method='POST' style='margin:0;'><input type='hidden' name='form_type' value='delete_subscriber'><input type='hidden' name='username' value='{uname}'><button type='submit' class='danger' style='padding:5px 10px; width:auto;'>حذف</button></form>" if uname != "client_bashar" else "<span style='color:#64748b;'>حساب أساسي</span>") + "</td></tr>" for uname, info in SUBSCRIBERS_DB.items()])}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(dashboard_html)

# ==============================================================================
# 3. بوابة توجيه الـ API وتوحيد المحتوى (Xtream API Gateway)
# ==============================================================================
@app.route('/player_api.php')
def xtream_interactive_gateway():
    usr = request.args.get('username')
    pwd = request.args.get('password')
    act = request.args.get('action')
    
    subscriber_profile = SUBSCRIBERS_DB.get(usr)
    if not subscriber_profile or subscriber_profile['password'] != pwd or subscriber_profile.get('status') != "Active":
        return jsonify({"user_info": {"auth": 0, "status": "Unauthorized or Expired"}}), 401
        
    valid_sources = fetch_and_filter_active_interactive()
    
    if act and valid_sources:
        try:
            aggregated_payload = []
            for src_item in valid_sources:
                upstream_endpoint = f"{src_item['dns']}/player_api.php?username={src_item['username']}&password={src_item['password']}&action={act}"
                for query_key, query_val in request.args.items():
                    if query_key not in ['username', 'password']:
                        upstream_endpoint += f"&{query_key}={query_val}"
                
                try:
                    upstream_resp = requests.get(upstream_endpoint, timeout=TIMEOUT_LIMIT)
                    if upstream_resp.status_code == 200:
                        json_content = upstream_resp.json()
                        if isinstance(json_content, list):
                            for element in json_content:
                                if isinstance(element, dict):
                                    if 'stream_id' in element:
                                        element['stream_id'] = f"s{src_item['index']}_{element['stream_id']}"
                                    elif 'series_id' in element:
                                        element['series_id'] = f"s{src_item['index']}_{element['series_id']}"
                                    elif 'category_id' in element:
                                        element['category_id'] = f"s{src_item['index']}_{element['category_id']}"
                                    aggregated_payload.append(element)
                        elif isinstance(json_content, dict):
                            return jsonify(json_content)
                except Exception:
                    continue
            return jsonify(aggregated_payload)
        except Exception:
            return jsonify([])

    login_response_packet = {
        "user_info": {
            "username": usr,
            "password": pwd,
            "status": "Active",
            "exp_date": "1893456000",
            "is_trial": "0",
            "active_cons": "1",
            "max_connections": str(subscriber_profile['max_connections'])
        },
        "server_info": {
            "url": request.host_url.rstrip('/').replace('https://', 'http://'),
            "port": "8080",
            "https_port": "8080",
            "server_protocol": "http"
        }
    }
    return jsonify(login_response_packet)

# ==============================================================================
# 4. محرك توجيه وإعادة توجيه البث (Smart Stream Dispatcher)
# ==============================================================================
@app.route('/live/<usr>/<pwd>/<path:stream_subpath>')
@app.route('/movie/<usr>/<pwd>/<path:stream_subpath>')
@app.route('/series/<usr>/<pwd>/<path:stream_subpath>')
def interactive_stream_redirection(usr, pwd, stream_subpath):
    subscriber_profile = SUBSCRIBERS_DB.get(usr)
    if not subscriber_profile or subscriber_profile['password'] != pwd:
        return "Unauthorized Stream Access", 401
        
    valid_sources = fetch_and_filter_active_interactive()
    selected_target_source = valid_sources[0] if valid_sources else None
    unpacked_stream_path = stream_subpath
    
    if stream_subpath.startswith("s") and "_" in stream_subpath:
        try:
            tokens = stream_subpath.split("_", 1)
            target_source_idx = int(tokens[0][1:])
            unpacked_stream_path = tokens[1]
            for candidate in valid_sources:
                if candidate['index'] == target_source_idx:
                    selected_target_source = candidate
                    break
        except Exception:
            pass
            
    if selected_target_source:
        media_category = request.path.split('/')[1]
        destination_url = f"{selected_target_source['dns']}/{media_category}/{selected_target_source['username']}/{selected_target_source['password']}/{unpacked_stream_path}"
        return redirect(destination_url, code=302)
        
    return "No Active Upstream Sources Available", 503

@app.route('/health')
@app.route('/actuator/health')
def health_probe():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
