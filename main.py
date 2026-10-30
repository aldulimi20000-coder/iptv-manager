import os
from datetime import datetime
from flask import Flask, redirect, request, jsonify, render_template_string, Response
import requests

app = Flask(__name__)

# تحميل الاشتراكات تلقائياً من ملف sources.txt
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

XTREAM_SOURCES = load_sources()

USERS = {
    "bashar": {"password": "123", "max_connections": 2, "expiry": "2027-12-31"}
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
