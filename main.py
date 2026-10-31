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
    format='[%(asctime)s] [%(levelname)s] [%(name)s] (DEEP_CORE) >>> %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("IPTV_DEEP_MAXIMUM_MASTER")

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY", "bashar_deep_maximum_enterprise_master_2026")
TIMEOUT_LIMIT = 8
CACHE_TTL = 300  # التخزين المؤقت للمصادر النشطة (5 دقائق)
cache_lock = threading.Lock()

# ==============================================================================
# 1. الذاكرة المؤقتة الذكية وإدارة الخلفية (Advanced Thread-Safe Caching Engine)
# ==============================================================================
_DEEP_CACHE_STORAGE = {
    "active_sources": [],
    "raw_count": 0,
    "last_updated": 0,
    "system_status": "Deep Operational",
    "request_counter": 0,
    "error_counter": 0,
    "active_streams_count": 0
}

def load_sources_from_disk_deep():
    """قراءة ملف sources.txt مع فحص السلامة والهيكلة بدقة مطلقة واستبعاد التعليقات"""
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
        logger.info(f"تم بنجاح تحميل عدد {len(parsed_sources)} مصدراً خاماً من ملف sources.txt في النمط العميق.")
    except Exception as err:
        logger.error(f"خطأ حرج أثناء قراءة ملف المصادر بالعمق: {str(err)}")
        with cache_lock:
            _DEEP_CACHE_STORAGE["error_counter"] += 1
    return parsed_sources

def evaluate_single_upstream_node_deep(node_info):
    """فحص عقدة مزود خدمة واحدة للتأكد من صلاحيتها واستقرارها عبر الـ API"""
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

def fetch_and_filter_active_sources_deep():
    """محرك الفحص المتوازي فائق السرعة مع تأمين الخيوط (Thread-Safe Multi-threading)"""
    global _DEEP_CACHE_STORAGE
    now_timestamp = time.time()
    
    with cache_lock:
        if now_timestamp - _DEEP_CACHE_STORAGE["last_updated"] < CACHE_TTL and _DEEP_CACHE_STORAGE["active_sources"]:
            return _DEEP_CACHE_STORAGE["active_sources"]
            
    raw_list = load_sources_from_disk_deep()
    with cache_lock:
        _DEEP_CACHE_STORAGE["raw_count"] = len(raw_list)
        
    functional_sources = []
    if raw_list:
        logger.info("بدء الفحص الصحي المتوازي العميق لجميع المصادر المرفوعة...")
        with ThreadPoolExecutor(max_workers=45) as thread_pool:
            eval_results = thread_pool.map(evaluate_single_upstream_node_deep, raw_list)
        for res_node in eval_results:
            if res_node:
                functional_sources.append(res_node)
                
    if not functional_sources and raw_list:
        functional_sources = raw_list[:1]  # ضمان وجود مصدر احتياطي دائماً لعدم التوقف
        
    with cache_lock:
        _DEEP_CACHE_STORAGE["active_sources"] = functional_sources
        _DEEP_CACHE_STORAGE["last_updated"] = now_timestamp
        _DEEP_CACHE_STORAGE["active_streams_count"] = len(functional_sources)
        
    logger.info(f"اكتمل الفحص العميق بنجاح. المصادر النشطة والشغالة: {len(functional_sources)} من أصل {len(raw_list)}")
    return functional_sources

# ==============================================================================
# 2. قاعدة بيانات المشتركين المركزية ونظام الأمان المتقدم (Subscribers Deep DB)
# ==============================================================================
SUBSCRIBERS_DB = {
    "client_bashar": {
        "password": "123",
        "expiry_date": "2026-12-31",
        "max_connections": 5,
        "allowed_device": "Android TV / TiviMate / IPTV Smarters Pro / VLC / Enigma2",
        "status": "Active",
        "current_active_connections": 1
    }
}

# ==============================================================================
# 3. واجهة التحكم الإدارية السينمائية الفائقة (Deep Maximum Admin Dashboard)
# ==============================================================================
@app.route('/')
def deep_maximum_admin_panel():
    raw_sources_list = load_sources_from_disk_deep()
    active_sources_list = fetch_and_filter_active_sources_deep()
    
    dashboard_html_deep = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>لوحة القيادة والسيطرة القصوى - IPTV Deep Maximum Core</title>
        <style>
            :root { --bg-base: #010409; --panel-bg: #0d1117; --accent-cyan: #38bdf8; --text-main: #c9d1d9; --success-clr: #3fb950; --warning-clr: #d29922; --border-clr: #30363d; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg-base); color: var(--text-main); margin: 0; padding: 30px; }
            .container-deep { max-width: 1500px; margin: auto; }
            .header-deep { text-align: center; margin-bottom: 40px; padding: 45px; background: var(--panel-bg); border-radius: 24px; border: 1px solid var(--border-clr); box-shadow: 0 25px 60px rgba(0,0,0,0.9); }
            .header-deep h1 { color: var(--accent-cyan); margin: 0; font-size: 34px; text-shadow: 0 0 35px rgba(56,189,248,0.6); }
            .header-deep p { color: #8b949e; font-size: 15px; margin-top: 15px; }
            .grid-deep { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 22px; margin-bottom: 35px; }
            .card-deep { background: var(--panel-bg); padding: 28px; border-radius: 20px; border: 1px solid var(--border-clr); box-shadow: 0 12px 35px rgba(0,0,0,0.6); }
            .card-deep h3 { margin-top: 0; color: var(--accent-cyan); border-bottom: 2px solid var(--border-clr); padding-bottom: 14px; font-size: 19px; }
            .metric-val { font-size: 38px; font-weight: bold; color: var(--success-clr); }
            .table-wrap { width: 100%; overflow-x: auto; }
            table { width: 100%; border-collapse: collapse; margin-top: 18px; min-width: 850px; }
            th, td { padding: 18px 16px; text-align: right; border-bottom: 1px solid var(--border-clr); font-size: 14px; }
            th { color: var(--accent-cyan); background: var(--border-clr); }
            tr:hover { background: rgba(48, 54, 61, 0.4); }
            .badge-deep { background: var(--accent-cyan); color: #010409; padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container-deep">
            <div class="header-deep">
                <h1>⚡ النظام المركزي الأقصى عمقاً - IPTV Deep Maximum Proxy Engine</h1>
                <p>إدارة عميقة متكاملة، فحص مصادر فوري متعدد الخيوط، دمج قنوات وأفلام ومسلسلات، وتتبع حي فائق الأداء</p>
            </div>
            
            <div class="grid-deep">
                <div class="card-deep">
                    <h3>🌐 حالة مصادر الـ Xtream (sources.txt)</h3>
                    <p>إجمالي المصادر في الملف: <span class="metric-val" style="color:var(--accent-cyan);">{{ total_raw }}</span> مصدراً</p>
                    <p>المصادر النشطة والشغالة فقط: <span class="metric-val">{{ active_count }}</span> مصدراً</p>
                </div>
                <div class="card-deep">
                    <h3>👥 مراقبة وإدارة المشتركين والاتصالات</h3>
                    <p>إجمالي العملاء المسجلين: <span class="metric-val">{{ total_subs }}</span> عميلاً</p>
                    <p>حالة النظام السحابي: <span class="badge-deep" style="background:var(--success-clr); color:white;">يعمل بكفاءة عميقة 24/7</span></p>
                </div>
                <div class="card-deep">
                    <h3>📊 إحصائيات المعالجة والطلب الحية</h3>
                    <p>إجمالي الطلبات المستلمة: <span class="metric-val" style="color:var(--warning-clr);">{{ req_count }}</span> طلباً</p>
                    <p>أخطاء النظام المسجلة: <span class="metric-val" style="color:#f85149; font-size:26px;">{{ err_count }}</span> أخطاء</p>
                </div>
            </div>

            <div class="card-deep">
                <h3>📋 جدول التحكم المركزي العميق بالمشتركين والصلاحيات</h3>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>اسم المستخدم (Username)</th>
                                <th>كلمة المرور (Password)</th>
                                <th>تاريخ انتهاء الاشتراك</th>
                                <th>عدد الأجهزة المسموحة</th>
                                <th>نوع الأجهزة المعتمدة</th>
                                <th>حالة الحساب</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for uname, info in subs_data.items() %}
                            <tr>
                                <td><strong>{{ uname }}</strong></td>
                                <td><code>{{ info.password }}</code></td>
                                <td><span style="color: var(--accent-cyan); font-weight:bold;">{{ info.expiry_date }}</span></td>
                                <td><span class="badge-deep">{{ info.max_connections }} أجهزة</span></td>
                                <td>{{ info.allowed_device }}</td>
                                <td><span style="color: var(--success-clr); font-weight: bold;">{{ info.status }}</span></td>
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
        dashboard_html_deep,
        total_raw=len(raw_sources_list),
        active_count=len(active_sources_list),
        total_subs=len(SUBSCRIBERS_DB),
        subs_data=SUBSCRIBERS_DB,
        req_count=_DEEP_CACHE_STORAGE["request_counter"],
        err_count=_DEEP_CACHE_STORAGE["error_counter"]
    )

# ==============================================================================
# 4. محرك توجيه وتوحيد واجهة الـ API العملاقة (Xtream Deep API Gateway)
# ==============================================================================
@app.route('/player_api.php')
def xtream_deep_gateway_api():
    global _DEEP_CACHE_STORAGE
    with cache_lock:
        _DEEP_CACHE_STORAGE["request_counter"] += 1
    
    usr = request.args.get('username')
    pwd = request.args.get('password')
    act = request.args.get('action')
    
    subscriber_profile = SUBSCRIBERS_DB.get(usr)
    if not subscriber_profile or subscriber_profile['password'] != pwd or subscriber_profile.get('status') != "Active":
        logger.warning(f"محاولة دخول غير مصرح بها للعميق باستخدام اسم المستخدم: {usr}")
        with cache_lock:
            _DEEP_CACHE_STORAGE["error_counter"] += 1
        return jsonify({"user_info": {"auth": 0, "status": "Unauthorized or Expired"}}), 401
        
    valid_sources = fetch_and_filter_active_sources_deep()
    
    # معالجة وتجميع الطلبات الشاملة بالعمق الكامل (القنوات، الأقسام، الأفلام، المسلسلات، الحلقات، EPG)
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
                                    # إضافة بادئة تعريفا عازلة لتجنب تصادم المعرفات بين المصادر المتعددة
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
        except Exception as system_exc:
            logger.error(f"خطأ عميق أثناء دمج بيانات الـ API: {str(system_exc)}")
            with cache_lock:
                _DEEP_CACHE_STORAGE["error_counter"] += 1
            return jsonify([])

    # رد تسجيل الدخول الأساسي العميق المتوافق 100% مع جميع تطبيقات الـ IPTV
    login_response_packet = {
        "user_info": {
            "username": usr,
            "password": pwd,
            "status": "Active",
            "exp_date": "1893456000",
            "is_trial": "0",
            "active_cons": str(subscriber_profile['current_active_connections']),
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
# 5. محرك تسيير وإعادة توجيه البث فائق الذكاء العميق (Deep Smart Stream Dispatcher)
# ==============================================================================
@app.route('/live/<usr>/<pwd>/<path:stream_subpath>')
@app.route('/movie/<usr>/<pwd>/<path:stream_subpath>')
@app.route('/series/<usr>/<pwd>/<path:stream_subpath>')
def deep_ultimate_stream_redirection_engine(usr, pwd, stream_subpath):
    subscriber_profile = SUBSCRIBERS_DB.get(usr)
    if not subscriber_profile or subscriber_profile['password'] != pwd:
        return "Unauthorized Deep Stream Access", 401
        
    valid_sources = fetch_and_filter_active_sources_deep()
    selected_target_source = valid_sources[0] if valid_sources else None
    unpacked_stream_path = stream_subpath
    
    # فك المعرف المدمج لمعرفة المصدر الأصلي وتوجيه الطلب إليه مباشرة بدرجة عمق قصوى
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
        
    return "No Active Deep Upstream Sources Available", 503

# ==============================================================================
# 6. مسارات فحص الصحة والسلامة للمنصات السحابية العميق (Health Check Endpoints)
# ==============================================================================
@app.route('/health')
@app.route('/actuator/health')
def cloud_deployment_deep_health_probe():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
