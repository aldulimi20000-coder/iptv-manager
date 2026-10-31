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
    format='[%(asctime)s] [%(levelname)s] [%(name)s] (STREAM_CHUNK_FIX) >>> %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("IPTV_STREAM_CHUNK")

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY", "bashar_chunk_fix_2026")
TIMEOUT_LIMIT = 20
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
            button.danger {{ background:
