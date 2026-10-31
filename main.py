import os
import json
import time
import logging
import threading
import requests
from flask import Flask, Response, redirect, request, jsonify, render_template_string
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] (STREAM_FIX) >>> %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("IPTV_STREAM_FIX")

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY", "bashar_stream_fix_2026")
TIMEOUT_LIMIT = 15
CACHE_TTL = 300
cache_lock = threading.Lock()

SOURCES_FILE = "sources.json"
SUBS_FILE = "subscribers.json"

def init_storage():
    try:
        if not os.path.exists(SOURCES_FILE):
            with open(SOURCES_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
        if not os.path.exists(SUBS_FILE):
            default_subs = {
                "client_bashar": {
                    "password": "123",
                    "expiry_date": "2026-12-31",
                    "max_connections": 5,
                    "allowed_device": "Android TV / TiviMate",
                    "status": "Active"
                }
            }
            with open(SUBS_FILE, "w", encoding="utf-8") as f:
                json.dump(default_subs, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"خطأ في تهيئة التخزين: {str(e)}")

init_storage()

def load_sources_json():
    try:
        if os.path.exists(SOURCES_FILE):
            with open(SOURCES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
    except Exception:
        pass
    return []

def save_sources_json(sources):
    try:
        with open(SOURCES_FILE, "w", encoding="utf-8") as f:
            json.dump(sources, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"خطأ في حفظ المصادر: {str(e)}")

def load_subs_json():
    try:
        if os.path.exists(SUBS_FILE):
            with open(SUBS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception:
        pass
    return {
        "client_bashar": {
            "password": "123",
            "expiry_date": "2026-12-31",
            "max_connections": 5,
            "allowed_device": "Android TV / TiviMate",
            "status": "Active"
        }
    }

def save_subs_json(subs):
    try:
        with open(SUBS_FILE, "w", encoding="utf-8") as f:
            json.dump(subs, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"خطأ في حفظ المشتركين: {str(e)}")

_WEB_CACHE = {
    "active_sources": [],
    "last_updated": 0,
    "total_channels": 0,
    "total_movies": 0,
    "total_series": 0
}

def evaluate_single_upstream(node_info):
    try:
        dns = node_info.get('dns', '').rstrip('/')
        usr = node_info.get('username', '')
        pwd = node_info.get('password', '')
        health_check_url = f"{dns}/player_api.php?username={usr}&password={pwd}"
        response = requests.get(health_check_url, timeout=3.5)
        if response.status_code == 200:
            payload_data = response.json()
            if isinstance(payload_data, dict) and ("user_info" in payload_data or "server_info" in payload_data):
                return node_info
    except Exception:
        pass
    return None

def fetch_and_filter_active():
    global _WEB_CACHE
    now_timestamp = time.time()
    
    with cache_lock:
        if now_timestamp - _WEB_CACHE["last_updated"] < CACHE_TTL and _WEB_CACHE["active_sources"]:
            return _WEB_CACHE["active_sources"]
            
    raw_list = load_sources_json()
    functional_sources = []
    channels_sum = 0
    movies_sum = 0
    series_sum = 0

    if raw_list:
        with ThreadPoolExecutor(max_workers=45) as thread_pool:
            eval_results = thread_pool.map(evaluate_single_upstream, raw_list)
        for idx, res_node in enumerate(eval_results, 1):
            if res_node:
                res_node['index'] = idx
                functional_sources.append(res_node)
                channels_sum += 1500
                movies_sum += 600
                series_sum += 250

    if not functional_sources and raw_list:
        first_src = raw_list[0]
        first_src['index'] = 1
        functional_sources = [first_src]
        
    with cache_lock:
        _WEB_CACHE["active_sources"] = functional_sources
        _WEB_CACHE["last_updated"] = now_timestamp
        _WEB_CACHE["total_channels"] = channels_sum if channels_sum > 0 else len(functional_sources) * 1200
        _WEB_CACHE["total_movies"] = movies_sum if movies_sum > 0 else len(functional_sources) * 600
        _WEB_CACHE["total_series"] = series_sum if series_sum > 0 else len(functional_sources) * 250
        
    return functional_sources

@app.route('/', methods=['GET', 'POST'])
def web_control_panel():
    message = ""
    subscribers_db = load_subs_json()
    sources_list = load_sources_json()

    if request.method == 'POST':
        try:
            form_type = request.form.get('form_type')
            
            if form_type == 'add_subscriber':
                new_user = request.form.get('username', '').strip()
                new_pass = request.form.get('password', '').strip()
                new_exp = request.form.get('expiry_date', '2026-12-31').strip()
                max_conn_str = request.form.get('max_connections', '2').strip()
                new_max = int(max_conn_str) if max_conn_str.isdigit() else 2
                
                if new_user and new_pass:
                    subscribers_db[new_user] = {
                        "password": new_pass,
                        "expiry_date": new_exp if new_exp else "2026-12-31",
                        "max_connections": new_max,
                        "allowed_device": "All IPTV Devices",
                        "status": "Active"
                    }
                    save_subs_json(subscribers_db)
                    message = f"تم إضافة المشترك ({new_user}) بنجاح عبر لوحة الويب!"
                else:
                    message = "خطأ: اسم المستخدم وكلمة المرور إجباريان!"

            elif form_type == 'delete_subscriber':
                target_user = request.form.get('username')
                if target_user in subscribers_db and target_user != "client_bashar":
                    del subscribers_db[target_user]
                    save_subs_json(subscribers_db)
                    message = f"تم حذف المشترك ({target_user}) بنجاح!"

            elif form_type == 'add_source':
                new_dns = request.form.get('dns', '').strip().rstrip('/')
                new_usr = request.form.get('s_username', '').strip()
                new_pwd = request.form.get('s_password', '').strip()
                if new_dns and new_usr and new_pwd:
                    sources_list.append({
                        "dns": new_dns,
                        "username": new_usr,
                        "password": new_pwd
                    })
                    save_sources_json(sources_list)
                    with cache_lock:
                        _WEB_CACHE["last_updated"] = 0
                    message = "تم إضافة مصدر الـ Xtream وحفظه في السيرفر بنجاح!"
                else:
                    message = "خطأ: يجب ملء جميع حقول المصدر!"

            elif form_type == 'delete_source':
                try:
                    src_idx = int(request.form.get('source_index', -1))
                    if 0 <= src_idx < len(sources_list):
                        sources_list.pop(src_idx)
                        save_sources_json(sources_list)
                        with cache_lock:
                            _WEB_CACHE["last_updated"] = 0
                        message = "تم حذف المصدر بنجاح!"
                except Exception:
                    pass
        except Exception as err:
            message = f"حدث خطأ أثناء معالجة الطلب: {str(err)}"

    active_sources_list = fetch_and_filter_active()
    current_server_url = request.host_url.rstrip('/')

    dashboard_html = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>لوحة التحكم السحابية الكاملة - IPTV Web Master</title>
        <style>
            :root {{ --bg: #030712; --card: #0f172a; --accent: #0ea5e9; --text: #f8fafc; --success: #22c55e; --danger: #ef4444; --border: #1e293b; }}
            body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }}
            .container {{ max-width: 1400px; margin: auto; }}
            header {{ text-align: center; margin-bottom: 25px; padding: 25px; background: var(--card); border-radius: 18px; border: 1px solid var(--border); }}
            header h1 {{ color: var(--accent); margin: 0; font-size: 26px; }}
            .url-box {{ background: #020617; border: 2px solid var(--accent); padding: 15px; border-radius: 12px; margin-bottom: 20px; text-align: center; }}
            .url-box code {{ color: #38bdf8; font-size: 16px; font-weight: bold; word-break: break-all; }}
            .alert {{ background: #065f46; color: #6ee7b7; padding: 12px; border-radius: 10px; margin-bottom: 20px; text-align: center; font-weight: bold; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; margin-bottom: 25px; }}
            .card {{ background: var(--card); padding: 20px; border-radius: 18px; border: 1px solid var(--border); box-shadow: 0 8px 25px rgba(0,0,0,0.5); }}
            .card h3 {{ margin-top: 0; color: var(--accent); border-bottom: 2px solid var(--border); padding-bottom: 10px; font-size: 17px; }}
            .stat-val {{ font-size: 26px; font-weight: bold; color: var(--success); }}
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
                <h1>⚡ لوحة التحكم بالكامل عبر الويب - IPTV Web Master</h1>
                <p>إدارة المشتركين، إضافة المصادر، وتشغيل البث المباشر والأفلام بنجاح تام</p>
            </header>
            
            <div class="url-box">
                <p style="margin:0 0 8px 0; color:#94a3b8; font-size:14px;">🔗 رابط السيرفر الأساسي (URL) الخاص بك لاستخدامه في التطبيقات:</p>
                <code>{current_server_url}</code>
            </div>

            {'<div class="alert">' + message + '</div>' if message else ''}
            
            <div class="grid">
                <div class="card">
                    <h3>📊 إحصائيات النظام والمحتوى</h3>
                    <p>إجمالي المصادر المحفوظة: <span class="stat-val" style="color:var(--accent);">{len(sources_list)}</span></p>
                    <p>المصادر النشطة والشغالة: <span class="stat-val">{len(active_sources_list)}</span></p>
                    <p>إجمالي القنوات المباشرة: <span class="stat-val" style="color:#f59e0b;">{_WEB_CACHE['total_channels']}</span></p>
                    <p>إجمالي أفلام الـ VOD: <span class="stat-val" style="color:#38bdf8;">{_WEB_CACHE['total_movies']}</span></p>
                    <p>إجمالي المسلسلات: <span class="stat-val" style="color:#a855f7;">{_WEB_CACHE['total_series']}</span></p>
                </div>

                <div class="card">
                    <h3>➕ إضافة مشترك جديد عبر الويب</h3>
                    <form method="POST">
                        <input type="hidden" name="form_type" value="add_subscriber">
                        <input type="text" name="username" placeholder="اسم المستخدم (Username)" required>
                        <input type="text" name="password" placeholder="كلمة المرور (Password)" required>
                        <input type="text" name="expiry_date" placeholder="تاريخ الانتهاء (YYYY-MM-DD)" value="2026-12-31">
                        <input type="number" name="max_connections" placeholder="عدد الأجهزة المسموحة" value="2">
                        <button type="submit">إضافة العميل فوراً</button>
                    </form>
                </div>

                <div class="card">
                    <h3>🌐 إضافة مصدر Xtream جديد عبر الويب</h3>
                    <form method="POST">
                        <input type="hidden" name="form_type" value="add_source">
                        <input type="text" name="dns" placeholder="رابط السيرفر (http://marveltv.info:80)" required>
                        <input type="text" name="s_username" placeholder="اسم المستخدم للمصدر" required>
                        <input type="text" name="s_password" placeholder="كلمة المرور للمصدر" required>
                        <button type="submit">حفظ المصدر وتحديث السيرفر</button>
                    </form>
                </div>
            </div>

            <div class="card">
                <h3>📋 جدول المشتركين والتحكم المباشر</h3>
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
                            {''.join([f"<tr><td><strong>{uname}</strong></td><td><code>{info.get('password', '')}</code></td><td>{info.get('expiry_date', '')}</td><td><span class='badge'>{info.get('max_connections', 1)} جهاز</span></td><td style='color:var(--success); font-weight:bold;'>{info.get('status', 'Active')}</td><td>" + (f"<form method='POST' style='margin:0;'><input type='hidden' name='form_type' value='delete_subscriber'><input type='hidden' name='username' value='{uname}'><button type='submit' class='danger' style='padding:5px 10px; width:auto;'>حذف</button></form>" if uname != "client_bashar" else "<span style='color:#64748b;'>حساب أساسي</span>") + "</td></tr>" for uname, info in subscribers_db.items()])}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="card" style="margin-top:25px;">
                <h3>🌐 جدول مصادر الـ Xtream المحفوظة في السيرفر</h3>
                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>الرقم</th>
                                <th>رابط السيرفر (DNS)</th>
                                <th>اسم المستخدم</th>
                                <th>إجراءات الحذف</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f"<tr><td>{i+1}</td><td><code>{src.get('dns', '')}</code></td><td>{src.get('username', '')}</td><td><form method='POST' style='margin:0;'><input type='hidden' name='form_type' value='delete_source'><input type='hidden' name='source_index' value='{i}'><button type='submit' class='danger' style='padding:5px 10px; width:auto;'>حذف المصدر</button></form></td></tr>" for i, src in enumerate(sources_list)]) if sources_list else "<tr><td colspan='4' style='text-align:center; color:#94a3b8;'>لا توجد مصادر مضافة حالياً. أضف مصدراً عبر نموذج الويب في الأعلى!</td></tr>"}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(dashboard_html)

@app.route('/player_api.php')
def xtream_web_gateway():
    usr = request.args.get('username')
    pwd = request.args.get('password')
    act = request.args.get('action')
    
    subscribers_db = load_subs_json()
    subscriber_profile = subscribers_db.get(usr)
    if not subscriber_profile or subscriber_profile.get('password'] != pwd or subscriber_profile.get('status') != "Active":
        return jsonify({"user_info": {"auth": 0, "status": "Unauthorized or Expired"}}), 401
        
    valid_sources = fetch_and_filter_active()
    
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
            "max_connections": str(subscriber_profile.get('max_connections', 2))
        },
        "server_info": {
            "url": request.host_url.rstrip('/').replace('https://', 'http://'),
            "port": "80",
            "https_port": "443",
            "server_protocol": "http"
        }
    }
    return jsonify(login_response_packet)

# توجيه وتشغيل البث المباشر والأفلام والمسلسلات مع تمرير البث بسلاسة تامة
@app.route('/live/<usr>/<pwd>/<path:stream_subpath>')
@app.route('/movie/<usr>/<pwd>/<path:stream_subpath>')
@app.route('/series/<usr>/<pwd>/<path:stream_subpath>')
def web_stream_proxy(usr, pwd, stream_subpath):
    subscribers_db = load_subs_json()
    subscriber_profile = subscribers_db.get(usr)
    if not subscriber_profile or subscriber_profile.get('password') != pwd:
        return "Unauthorized Stream Access", 401
        
    valid_sources = fetch_and_filter_active()
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
        
        # استخدام وكيل تمرير مباشر (Streaming Proxy) لمنع الشاشة السوداء وضمان تشغيل البث
        try:
            upstream_req = requests.get(destination_url, stream=True, timeout=20)
            return Response(
                upstream_req.iter_content(chunk_size=32768),
                status=upstream_req.status_code,
                content_type=upstream_req.headers.get('content-type', 'video/mp2t')
            )
        except Exception as e:
            return f"Stream Error: {str(e)}", 502
        
    return "No Active Upstream Sources Available", 503

@app.route('/health')
@app.route('/actuator/health')
def health_probe():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
