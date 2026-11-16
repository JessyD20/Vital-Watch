
from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "vitalwatch.db"

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS patients(
            id INTEGER PRIMARY KEY, name TEXT, age TEXT, ward TEXT, bed TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS readings(
            id INTEGER PRIMARY KEY, patient_id INTEGER, systolic REAL,
            diastolic REAL, pulse REAL, temperature REAL, spo2 REAL,
            time TEXT, alerts TEXT, score INTEGER)""")

def check(v):
    limits = [
        ("systolic", 90, 140, "Systolic BP"),
        ("diastolic", 60, 90, "Diastolic BP"),
        ("pulse", 60, 100, "Pulse"),
        ("temperature", 36, 38, "Temperature"),
        ("spo2", 95, 100, "SpO2")
    ]
    return [name + " outside demo range"
            for key, low, high, name in limits
            if not low <= v[key] <= high]

def risk(score):
    if score == 0:
        return "Normal", "green"
    if score <= 2:
        return "Warning", "yellow"
    return "Critical", "red"

STYLE = """
<style>
*{box-sizing:border-box}
body{margin:0;background:#edf4fb;color:#18334d;font-family:Arial}
header{background:#125b96;color:white;padding:22px 5%}
header h1{margin:0}
main{max-width:1100px;margin:25px auto;padding:20px}
.card{background:white;padding:18px;margin:14px 0;border-radius:12px;
box-shadow:0 2px 10px #d8e3ef}
h2{color:#145b96}
input{padding:11px;margin:5px;border:1px solid #c5d5e5;border-radius:6px}
button,.btn{background:#145b96;color:white;padding:11px 17px;
border:0;border-radius:6px;cursor:pointer;text-decoration:none}
a{color:#145b96}
.green{background:#d9f5e5;color:#147442}
.yellow{background:#fff0c2;color:#926000}
.red{background:#ffe0e0;color:#b42323}
.badge{padding:7px 12px;border-radius:20px;font-weight:bold;display:inline-block}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
table{width:100%;border-collapse:collapse;background:white}
td,th{padding:11px;border:1px solid #d5e1ed;text-align:left}
.bar{height:13px;background:#e3edf7;border-radius:10px;margin:7px 0}
.fill{height:13px;background:#2685c5;border-radius:10px}
.small{font-size:13px;color:#657c91}
.alert{background:#ffe0e0;color:#a51d1d;padding:10px;border-radius:7px}
@media print{button,.btn,input{display:none}body{background:white}}
</style>
"""

HOME = """
<header><h1>VitalWatch</h1>
<p>Patient Vitals Monitoring and Early-Alert System</p></header>
<main>
<div class=grid>
<div class=card><h2>{{patients|length}}</h2>Total Patients</div>
<div class=card><h2>{{alerts|length}}</h2>Active Alerts</div>
</div>
<div class=card>
<h2>Register Patient</h2>
<form method=post action=/add>
<input name=name placeholder="Patient Name" required>
<input name=age placeholder=Age>
<input name=ward placeholder=Ward required>
<input name=bed placeholder=Bed>
<button>Add Patient</button></form>
</div>
<div class=card>
<h2>Search Patients</h2>
<form method=get>
<input name=q placeholder="Search patient name or ward" value="{{q}}">
<button>Search</button>
<a href="/">Clear</a>
</form>
</div>
<h2>Patient List</h2>
{% for p in patients %}
<div class=card>
<div class=grid>
<div><h3>{{p.name}}</h3>
<p>{{p.ward}} | Bed {{p.bed or '-'}}</p></div>
<div><span class="badge {{p.color}}">{{p.status}}</span>
<p class=small>Risk score: {{p.score}}</p></div>
</div>
<a class=btn href="/patient/{{p.id}}">View Patient</a>
</div>
{% else %}<div class=card>No patients found.</div>{% endfor %}
<h2>Active Alerts</h2>
{% for a in alerts %}
<div class=alert><b>{{a.name}}</b> — {{a.alerts}}</div>
{% else %}<div class=card>No active alerts.</div>{% endfor %}
<div class=card><a class=btn href="/handover">Shift Handover Summary</a>
<a href="/history">Alert History</a></div>
</main>
"""

PATIENT = """
<header><h1>{{p.name}}</h1><p>{{p.ward}} | Bed {{p.bed or '-'}}</p></header>
<main>
<a href="/">← Dashboard</a>
<div class=card>
<h2>Current Risk Status</h2>
<span class="badge {{status_color}}">{{status}}</span>
<p>Early-warning score: {{score}} / 5</p>
</div>
<div class=card>
<h2>Record Patient Vitals</h2>
<form method=post>
<input name=systolic type=number step=.1 placeholder="Systolic BP" required>
<input name=diastolic type=number step=.1 placeholder="Diastolic BP" required>
<input name=pulse type=number step=.1 placeholder="Pulse" required>
<input name=temperature type=number step=.1 placeholder="Temperature °C" required>
<input name=spo2 type=number step=.1 placeholder="SpO2 %" required>
<button>Save Reading</button>
</form></div>
<div class=card>
<h2>Trend: {{trend}}</h2>
{% if escalate %}<div class=alert>Escalation: risk score increased in two consecutive intervals.</div>{% endif %}
<h2>Vital Signs Graphs</h2>
{% for label,key,limit in metrics %}
<h3>{{label}}</h3>
{% for r in chart %}
<div class=small>{{r.time}} — {{r[key]}}</div>
<div class=bar><div class=fill style="width:{{[r[key]/limit*100,100]|min}}%"></div></div>
{% endfor %}
{% endfor %}
</div>
<div class=card>
<h2>Last 3 Readings</h2>
{% for r in readings %}
<p><b>{{r.time}}</b></p>
BP: {{r.systolic}}/{{r.diastolic}} |
Pulse: {{r.pulse}} |
Temp: {{r.temperature}}°C |
SpO2: {{r.spo2}}%
<p>Score: {{r.score}}</p>
{% if r.alerts %}<div class=alert>{{r.alerts}}</div>
{% else %}<span class=badge green>Normal</span>{% endif %}
<hr>
{% else %}No readings yet{% endfor %}
</div>
<div class=card><a href="/history">View Alert History</a></div>
</main>
"""

HANDOVER = """
<header><h1>Ward Shift Handover</h1></header>
<main><a href="/">← Dashboard</a>
<p>Generated: {{now}}</p>
<button onclick="window.print()">Print Summary</button>
<table>
<tr><th>Patient</th><th>Ward/Bed</th><th>Latest Vitals</th><th>Score</th><th>Alerts</th></tr>
{% for r in rows %}
<tr><td>{{r.name}}</td><td>{{r.ward}}/{{r.bed or '-'}}</td>
<td>{% if r.time %}{{r.time}}<br>
BP {{r.systolic}}/{{r.diastolic}}<br>
Pulse {{r.pulse}}<br>Temp {{r.temperature}}<br>SpO2 {{r.spo2}}
{% else %}No readings{% endif %}</td>
<td>{{r.score if r.score is not none else '-'}}</td>
<td>{{r.alerts or 'None'}}</td></tr>
{% endfor %}
</table>
</main>
"""

HISTORY = """
<header><h1>Alert History</h1></header>
<main><a href="/">← Dashboard</a>
{% for r in rows %}
<div class=card>
<h3>{{r.name}}</h3>
<p>{{r.time}} | Ward {{r.ward}} | Bed {{r.bed or '-'}}</p>
<div class=alert>{{r.alerts}}</div>
<p>Risk score: {{r.score}}</p>
</div>
{% else %}<div class=card>No previous alerts.</div>{% endfor %}
</main>
"""

def page(html, **data):
    return render_template_string(
        "<html><head><title>VitalWatch</title>"+STYLE+
        "</head><body>"+html+"</body></html>", **data)

@app.route("/")
def home():
    q = request.args.get("q", "")
    with db() as c:
        patients = c.execute(
            "SELECT * FROM patients WHERE name LIKE ? OR ward LIKE ? ORDER BY name",
            (f"%{q}%", f"%{q}%")).fetchall()
        result = []
        for p in patients:
            r = c.execute(
                "SELECT * FROM readings WHERE patient_id=? ORDER BY id DESC LIMIT 1",
                (p["id"],)).fetchone()
            score = r["score"] if r else 0
            status, color = risk(score)
            result.append(dict(p, score=score, status=status, color=color))
        alerts = c.execute("""SELECT p.name,r.alerts FROM patients p JOIN readings r
            ON r.id=(SELECT MAX(id) FROM readings WHERE patient_id=p.id)
            WHERE r.score>0""").fetchall()
    return page(HOME, patients=result, alerts=alerts, q=q)

@app.route("/add", methods=["POST"])
def add():
    with db() as c:
        c.execute("INSERT INTO patients(name,age,ward,bed) VALUES(?,?,?,?)",
                  (request.form["name"], request.form["age"],
                   request.form["ward"], request.form["bed"]))
    return redirect("/")

@app.route("/patient/<int:pid>", methods=["GET","POST"])
def patient(pid):
    if request.method == "POST":
        v = {k:float(request.form[k]) for k in
             ["systolic","diastolic","pulse","temperature","spo2"]}
        alerts = check(v)
        with db() as c:
            c.execute("""INSERT INTO readings(patient_id,systolic,diastolic,pulse,
                temperature,spo2,time,alerts,score)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (pid,v["systolic"],v["diastolic"],v["pulse"],
                 v["temperature"],v["spo2"],
                 datetime.now().strftime("%Y-%m-%d %H:%M"),
                 "; ".join(alerts),len(alerts)))
        return redirect(f"/patient/{pid}")

    with db() as c:
        p = c.execute("SELECT * FROM patients WHERE id=?", (pid,)).fetchone()
        readings = c.execute(
            "SELECT * FROM readings WHERE patient_id=? ORDER BY id DESC LIMIT 3",
            (pid,)).fetchall()

    score = readings[0]["score"] if readings else 0
    status, color = risk(score)
    trend, escalate = "Not enough readings", False

    if len(readings) == 3:
        s = [r["score"] for r in readings]
        trend = ("Improving" if s[0] < s[1] < s[2] else
                 "Worsening" if s[0] > s[1] > s[2] else "Stable")
        escalate = s[0] > s[1] > s[2] > 0

    chart = list(reversed(readings))
    metrics = [
        ("Systolic BP", "systolic", 180),
        ("Diastolic BP", "diastolic", 120),
        ("Pulse", "pulse", 150),
        ("Temperature", "temperature", 42),
        ("SpO2", "spo2", 100)
    ]
    return page(PATIENT, p=p, readings=readings, chart=chart,
                metrics=metrics, trend=trend, escalate=escalate,
                score=score, status=status, status_color=color)

@app.route("/history")
def history():
    with db() as c:
        rows = c.execute("""SELECT p.name,p.ward,p.bed,r.* FROM readings r
            JOIN patients p ON p.id=r.patient_id
            WHERE r.alerts!='' ORDER BY r.id DESC""").fetchall()
    return page(HISTORY, rows=rows)

@app.route("/handover")
def handover():
    with db() as c:
        rows = c.execute("""SELECT p.name,p.ward,p.bed,r.* FROM patients p
            LEFT JOIN readings r ON r.id=
            (SELECT MAX(id) FROM readings WHERE patient_id=p.id)
            ORDER BY p.ward,p.bed""").fetchall()
    return page(HANDOVER, rows=rows,
                now=datetime.now().strftime("%Y-%m-%d %H:%M"))

if __name__ == "__main__":
    init()
    app.run(debug=True)
