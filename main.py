import os
import time
from datetime import datetime
from flask import Flask, redirect, request, jsonify, render_template_string
import requests
import concurrent.futures

app = Flask(__name__)

# ذاكرة مؤقتة لدمج محتوى الـ 59 حساباً بالكامل دون فلترة
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
    
    # سحب ودمج محتوى الـ 59 حساباً بالكامل
    if not MASTER_CACHE["sources"] or (current_time - MASTER_CACHE["last_updated"] > 900):
        all_sources = load_sources()
        MASTER_CACHE["sources"] = all_sources
        
        live_list, vod_list, series_list = [], [], []
        live_cat, vod_cat, series_cat = [], [], []
        stream_map = {}
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        # سحب البيانات من جميع الحسابات لضمان شمولية الأفلام والمسلسلات والقنوات
        for idx, src in enumerate(all_sources):
            base_url = f"{src['dns']}/player_api.php?username={src['user']}&password={src['pass']}"
            try:
                # سحب القنوات المباشرة
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
                
                # سحب الأفلام (VOD)
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

                # سحب المسلسلات
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

        # جلب التصنيفات من أول حساب
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
    <title>لوحة تحكم مدير IPTV</title>
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
            <span>🌐 رابط السيرفر الأساسي (Server URL) للزبائن:</span>
            <input type="text" value="{{ host_url }}" readonly onclick="this.select();">
        </div>

        <h2>إضافة مستخدم جديد</h2>
        <form method="POST" action="/add_user
