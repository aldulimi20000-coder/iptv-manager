import os
from datetime import datetime
from flask import Flask, redirect, request, jsonify, render_template_string
import requests
import concurrent.futures
import random

app = Flask(__name__)

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
        r = requests.get(url, timeout=3, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code == 200:
            data = r.json()
            if data.get("user_info", {}).get("auth") == 1:
                return source
    except:
        pass
    return None

def get_working_sources():
    all_sources = load_sources()
    working = []
    print(f"Testing {len(all_sources)} sources for active status...")
    # فحص جميع المصادر بالتوازي في ثوانٍ معدودة لاستخراج الشغالة فقط
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(test_source, all_sources)
        for res in results:
            if res:
                working.append(res)
    print(f"Found {len(working)} working sources out of {len(all_sources)}.")
    # إذا لم يعمل أي مصدر لأي سبب طارئ، نعود للقائمة الأصلية كاحتياط
    return working if working else all_sources

# تحميل المصادر النشطة فقط وتخزينها في الذاكرة
XTREAM_SOURCES = get_working_sources()

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
            <div>📡 المصادر النشطة والشغالة: <strong>{{ sources_count }}</strong></div>
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
            <label style="display:block; text-align:right; margin-top:5px; font-size:13px;">ت
