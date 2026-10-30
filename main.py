import os
from flask import Flask, request, Response, jsonify
import requests

app = Flask(__name__)

# تحميل الاشتراكات تلقائياً من ملف sources.txt
XTREAM_SOURCES = []
try:
    if os.path.exists('sources.txt'):
        with open('sources.txt', 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    XTREAM_SOURCES.append({
                        "dns": parts[0].strip(),
                        "user": parts[1].strip(),
                        "pass": parts[2].strip()
                    })
except Exception as e:
    print(f"Error loading sources: {e}")

# حسابات المستخدمين المسموح لهم بالدخول للوحة أو التطبيق
USERS = {
    "bashar": {"password": "123", "max_connections": 2}
}

@app.route('/')
def home():
    return f"""
    <html>
    <head><title>IPTV Aggregator Admin Panel</title></head>
    <body style="background:#111; color:#fff; font-family:Arial; text-align:center; padding:50px;">
        <h1>!تعمل بنجاح IPTV لوحة تحكم تجميع سيرفرات</h1>
        <p>تم تحميل عدد {len(XTREAM_SOURCES)} اشتراك بنجاح والخدمة تعمل بكفاءة.</p>
    </body>
    </html>
    """

@app.route('/player_api.php')
def xtream_api():
    username = request.args.get('username')
    password = request.args.get('password')
    action = request.args.get('action')
    
    if username not in USERS or USERS[username]['password'] != password:
        return jsonify({"user_info": {"auth": 0, "status": "Disabled"}})
    
    if action == 'get_live_categories':
        return jsonify([{"category_id": "1", "category_name": "المقاطع العامة والرياضية"}])
    elif action == 'get_live_streams':
        return jsonify([])
    
    return jsonify({
        "user_info": {
            "username": username,
            "status": "Active",
            "max_connections": USERS[username].get('max_connections', 1),
            "auth": 1
        }
    })

@app.route('/live/<username>/<password>/<stream_id>.ts')
def stream_proxy(username, password, stream_id):
    if username not in USERS or USERS[username]['password'] != password:
        return "Unauthorized", 401
    
    for source in XTREAM_SOURCES:
        try:
            target_url = f"{source['dns']}/live/{source['user']}/{source['pass']}/{stream_id}.ts"
            r = requests.get(target_url, stream=True, timeout=3)
            if r.status_code == 200:
                return Response(r.iter_content(chunk_size=1024), content_type=r.headers.get('Content-Type'))
        except:
            continue
            
    return "All sources offline", 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
