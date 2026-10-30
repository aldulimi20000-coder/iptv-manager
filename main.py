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

# جدول المستخدمين والاشتراكات (يمكنك إدارتهم مباشرة عبر اللوحة)
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
        body { background: #0f172a; color: #f8fafc; font-family: Tahoma, sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 900px; margin: auto; background: #1e293b; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        h1, h2 { color: #38bdf8; text-align: center; }
        .stats { display: flex; justify-content: space-around; background: #334155; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; border-bottom: 1px solid #475569; text-align: center; }
        th { background: #0284c7; color: #fff; }
        form { background: #334155; padding: 15px; border-radius: 8px; margin-top: 20px; }
        input, button { padding: 10px; margin: 5px 0; width: 100%; box-sizing: border-box; border-radius: 5px; border: none; }
        input { background: #1e293b; color: #fff; border: 1px solid #475569; }
        button { background: #22c55e; color: #fff; font-weight: bold; cursor: pointer; }
        button:hover { background: #16a34a; }
        .btn-danger { background: #ef4444; }
        .btn-danger:hover { background: #dc2626; }
    </style>
</head>
<body>
    <div class="container">
        <h1>لوحة تحكم وإدارة اشتراكات IPTV</h1>
        <div class="stats">
            <div>📡 مصادر Xtream المحملة: <strong>{{ sources_count }}</strong></div>
            <div>👥 عدد المستخدمين: <strong>{{ users|length }}</strong></div>
        </div>

        <h2>إضافة مستخدم جديد أو تعديل اشتراك</h2>
        <form method="POST" action="/add_user">
            <input type="text" name="username" placeholder="اسم المستخدم" required>
            <input type="text" name="password" placeholder="كلمة المرور" required>
            <input type="number" name="max_connections" placeholder="عدد الاتصالات المسموحة (مثال: 1)" value="1" required>
            <label style="display:block; text-align:right; margin-top:5px;">تاريخ انتهاء الاشتراك:</label>
            <input type="date" name="expiry" required>
            <button type="submit">حفظ / إضافة المستخدم</button>
        </form>

        <h2>قائمة المستخدمين الحاليين</h2>
        <table>
            <tr>
                <th>اسم المستخدم</th>
                <th>كلمة المرور</th>
                <th>الاتصالات</th>
                <th>تاريخ الانتهاء</th>
                <th>الإجراء</th>
            </tr>
            {% for uname, data in users.items() %}
            <tr>
                <td>{{ uname }}</td>
                <td>{{ data.password }}</td>
                <td>{{ data.max_connections }}</td>
                <td>{{ data.expiry }}</td>
                <td>
                    <form method="POST" action="/delete_user" style="margin:0; padding:0; background:none;">
                        <input type="hidden" name="username" value="{{ uname }}">
                        <button type="submit" class="btn-danger" style="width: auto; padding: 5px 10px;">حذف</button>
                    </form>
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
    return render_template_string(HTML_TEMPLATE, sources_count=len(XTREAM_SOURCES), users=USERS)

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
    
    # التحقق من تاريخ انتهاء الاشتراك
    expiry_str = USERS[username].get('expiry', '2099-12-31')
    try:
        expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
        if datetime.now() > expiry_date:
            return jsonify({"user_info": {"auth": 0, "status": "Expired", "message": "Subscription Expired"}})
    except:
        pass
    
    if action == 'get_live_categories':
        return jsonify([{"category_id": "1", "category_name": "باقات الـ VIP والرياضة"}])
    elif action == 'get_live_streams':
        return jsonify([])
    
    return jsonify({
        "user_info": {
            "username": username,
            "status": "Active",
            "max_connections": USERS[username].get('max_connections', 1),
            "auth": 1,
            "exp_date": expiry_str
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
