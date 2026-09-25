#!/usr/bin/env python3
"""Nedlloyd site server: static files (with HTTP Range for video) + JSON API + SQLite.
Run:  python3 server.py [port]      (default 8090)
AI:   export ANTHROPIC_API_KEY=...  (optional; without it the assistant answers from the built-in knowledge base)
"""
import os, sys, json, sqlite3, hashlib, secrets, time, re, urllib.request
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, unquote

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "data", "nedlloyd.db")
os.makedirs(os.path.dirname(DB), exist_ok=True)
MILESTONES = ["Booking Confirmed","Cargo Picked Up","Customs (Origin)","Departed","In Transit","Arrived Destination","Customs (Dest.)","Out for Delivery","Delivered (POD)","Job Closed"]
DOCS = ["Booking Note","Invoice + PL","Shipping Bill","BL / AWB","","","BOE / DO","","POD Copy",""]

def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

def init():
    c = db(); q = c.executescript
    q("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, pw TEXT, role TEXT, name TEXT, client TEXT, parent TEXT);
    CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY, job TEXT UNIQUE, client TEXT, customer TEXT, origin TEXT, destination TEXT, mode TEXT, cargo TEXT, stage INTEGER, dates TEXT, notes TEXT, created REAL);
    CREATE TABLE IF NOT EXISTS leads(id INTEGER PRIMARY KEY, ref TEXT, data TEXT, page TEXT, status TEXT DEFAULT 'new', created REAL);
    CREATE TABLE IF NOT EXISTS hits(id INTEGER PRIMARY KEY, page TEXT, ref TEXT, created REAL);
    CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY, page TEXT, item TEXT, vote TEXT, created REAL);
    CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY, job TEXT, author TEXT, kind TEXT, text TEXT, created REAL);
    CREATE TABLE IF NOT EXISTS chats(id INTEGER PRIMARY KEY, q TEXT, a TEXT, page TEXT, created REAL);
    """)
    if not c.execute("SELECT 1 FROM users").fetchone():
        for u,p,r,n,cl,par in [("admin","admin","admin","Nedlloyd Admin","",""),("client","client","client","Supply Chain Lead","Alstom India",""),
                                ("customer","customer","customer","Site Manager","Alstom India","client"),("employee","employee","employee","Ops Executive","","")]:
            c.execute("INSERT INTO users(username,pw,role,name,client,parent) VALUES(?,?,?,?,?,?)",(u,H(p),r,n,cl,par))
        seed=[("NL-2026-0001","Alstom India","Site Manager","Chennai","Dallas, TX","Sea · Breakbulk","2 × traction transformers, 46 t each",6),
              ("NL-2026-0002","Alstom India","","Shanghai","Dankuni, Kolkata","Sea · FCL","12 × 40' HC bogie frames",3),
              ("NL-2026-0003","Jindal Steel","","Hamburg","Angul, Odisha","Air · Charter","Rolling mill spares, 8.2 t",9),
              ("NL-2026-0004","BSNL","","Bhiwandi WH","Bangalore","Land · Road","Telecom equipment, 14 pallets",8),
              ("NL-2026-0005","Sony India","","Tokyo","Delhi Rangpuri WH","Air · Freight",'Consumer electronics, 3.1 t',5),
              ("NL-2026-0006","Alstom India","Site Manager","Mississauga","Hooghly","Sea · RO/RO","Metro coach shell, OOG",1)]
        for j in seed:
            dates=[time.strftime("%d %b",time.localtime(time.time()-86400*(j[7]-i)*2)) if i<j[7] else "" for i in range(10)]
            c.execute("INSERT INTO jobs(job,client,customer,origin,destination,mode,cargo,stage,dates,notes,created) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(*j,json.dumps(dates),"",time.time()))
    c.commit(); c.close()

def H(p): return hashlib.sha256(("nl~"+p).encode()).hexdigest()
TOK = {}

KB = """Nedlloyd Logistics India Pvt. Ltd. — founded New Delhi 2001. Integrated Project Logistics Management company; preferred partner to companies in Energy, Steel, Power, Oil & Gas, Infrastructure, Automotive and Rail.
Services: Air freight, Sea freight (FCL/LCL/breakbulk/RO-RO), Land transport (road & rail across India), Customs brokerage, Warehousing & distribution (20+ IT-enabled warehouses: general, bonded, temperature-controlled, project), Project cargo & heavy lift (route surveys, permits, escorts, engineered load plans, on-site supervision), Charter (air/sea), 4PL, Express courier & cargo, E-commerce fulfilment, Reverse logistics, Cargo insurance.
Industries: Oil & Gas, Power, BESS, Solar, Wind, EPC & Infrastructure, Steel & Cement, Automotive, Rail (metro + conventional), Defence, Telecom, Heavy Engineering.
Tracking: every job has one Job Number and 10 milestones (Booking Confirmed, Cargo Picked Up, Customs Origin, Departed, In Transit, Arrived Destination, Customs Dest, Out for Delivery, Delivered POD, Job Closed) with documents attached; role-based dashboards for Admin, Client, Client's Customer, Employee.
Offices: HQ T-95A, 4th Floor, C.L. House, Yusuf Sarai Commercial Centre, Gautam Nagar, New Delhi-110049 (+91 11 4986 6666, +91 99106 94210, info@nedlloydgroup.com, Mon-Sat 9-6); Delhi Rangpuri warehouse; Mumbai (Bhiwandi, CBD Belapur); Bangalore (Tumkur Road); Kolkata (Dankuni). USA: Nedlloyd Logistics Americas, 5900 Balcones Dr, Austin TX (+1 512 961 3445, usacs@nedlloydgroup.com); Miami; Cleveland. Canada: Nedlloyd Logistics Canada Inc., 1030 Kamato Rd, Mississauga ON. UAE presence.
Certifications: ISO 9001:2015, ISO 14001, OHSAS 18001, WCA Network. Values: Client value creation, Best people, Respect for individuals, Integrity, Business excellence. Motto: TEAM — Together Everyone Achieves More.
Clients include Sony, BSNL, Alstom, HP, Jindal, Haier, Somany, Teracom, Javi Systems.
Quotes: use the Get a Quote form or WhatsApp +91 99106 94210; reply within one business day."""

FAQ=[]
try: FAQ=json.load(open(os.path.join(ROOT,"addons","faq.json")))
except Exception: pass
def faq_answer(q):
    t=[w for w in re.findall(r"[a-z0-9]+",q.lower()) if len(w)>2]; best=None; bs=0
    for f in FAQ:
        ql=f["q"].lower(); al=f["a"].lower(); sc=sum(2 if w in ql else (1 if w in al else 0) for w in t)
        if sc>bs: bs,best=sc,f
    return best["a"] if best and bs>=3 else None
def ai_reply(messages, page):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        try:
            body = json.dumps({"model":"claude-sonnet-4-6","max_tokens":500,"system":"You are the Nedlloyd Logistics website assistant. Answer briefly (max 90 words), warmly, in plain text; when useful end with a suggestion to Get a Quote or WhatsApp +91 99106 94210. Only use this knowledge:\n"+KB,"messages":messages}).encode()
            req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={"content-type":"application/json","x-api-key":key,"anthropic-version":"2023-06-01"})
            r = json.loads(urllib.request.urlopen(req, timeout=30).read())
            return "".join(b.get("text","") for b in r.get("content",[]))
        except Exception as e:
            pass
    q = (messages[-1]["content"] if messages else "").lower()
    fa = faq_answer(q)
    if fa: return fa
    rules = [(r"track|status|where is", "Use the Track shipment tab with your Job Number, or sign in to the Customer Dashboard. Every job runs through 10 milestones from Booking Confirmed to Job Closed."),
             (r"quote|price|rate|cost", "Tap Get a Quote or WhatsApp +91 99106 94210 with origin, destination, cargo weight/dimensions and target date — we reply within one business day."),
             (r"office|address|where are|contact|phone|email", "Head office: T-95A, 4th Floor, C.L. House, Yusuf Sarai Commercial Centre, New Delhi-110049 · +91 11 4986 6666 · info@nedlloydgroup.com. Also Mumbai, Bangalore, Kolkata; Austin, Miami, Cleveland (USA); Mississauga (Canada)."),
             (r"\bair\b|flight", "Air freight: express, priority and deferred options through reliable airlines, plus air charter for urgent or oversized cargo. AWB and customs milestones are tracked on your dashboard."),
             (r"sea|ocean|vessel|container", "Sea freight: FCL, LCL, breakbulk and RO/RO — including project and out-of-gauge cargo on breakbulk and heavy-lift vessels."),
             (r"road|rail|land|truck|trailer", "Land transport: road and rail across India's industrial corridors, ports and inland hubs, heavy-haul and over-dimensional included, every leg tracked."),
             (r"project|heavy|odc|over.?dimension|oversize|transformer|turbine", "Yes — project cargo is our core work: route surveys, permits and escorts, engineered load plans, hydraulic axles and cranes, customs project registration and on-site supervision."),
             (r"warehouse|storage|bonded", "20+ IT-enabled warehouses across India — general, custom-bonded, temperature-controlled and project warehousing with real-time inventory visibility."),
             (r"customs|clearance|broker", "Customs brokerage at origin and destination: documentation, duty and restriction advice, payment of duties and bonds — shipping bills and BOE/DO attached to each milestone."),
             (r"service|what do you|offer", "Air, Sea and Land freight, Customs Brokerage, Warehousing & Distribution, Project Cargo & Heavy Lift, Charter, 4PL, Express Courier, E-commerce Fulfilment, Reverse Logistics and Cargo Insurance."),
             (r"industr|sector|oil|power|steel|rail|auto|defence|solar|wind|telecom", "We move for Oil & Gas, Power, BESS, Solar, Wind, EPC & Infrastructure, Steel & Cement, Automotive, Rail, Defence and Telecom."),
             (r"career|job|hiring|vacanc", "We're growing across India and abroad — see the Careers page for open roles."),
             (r"iso|certif|complian|wca", "Certified ISO 9001:2015, ISO 14001 and OHSAS 18001; WCA Network partner."),
             (r"hello|hi\b|hey", "Hello! Ask me about air, sea or land freight, project cargo, our offices — or track a shipment by Job Number.")]
    for p,a in rules:
        if re.search(p,q): return a
    return "I can help with services, industries, offices, tracking and quotes. Try: \"Do you handle over-dimensional cargo?\" — or tap Get a Quote."

def linkify(t):
    return t.replace("Get a Quote","<b>Get a Quote</b>")

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**k): super().__init__(*a,directory=ROOT,**k)
    def log_message(self,*a): pass
    def _json(self, obj, code=200):
        b=json.dumps(obj).encode(); self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def _body(self):
        n=int(self.headers.get("Content-Length") or 0); return json.loads(self.rfile.read(n) or b"{}") if n else {}
    def _user(self):
        t=(self.headers.get("Authorization") or "").replace("Bearer ","").strip(); return TOK.get(t)
    # ---------- API ----------
    def do_POST(self):
        p=urlparse(self.path).path
        if p.startswith("/.wf_graphql") or "/ga/" in p or p.startswith("/9i1h"): return self._json({"ok":True})
        try:
            if p=="/api/leads":
                d=self._body(); ref="Q-"+time.strftime("%y%m%d")+"-"+secrets.token_hex(2).upper()
                c=db(); c.execute("INSERT INTO leads(ref,data,page,created) VALUES(?,?,?,?)",(ref,json.dumps(d),d.get("page",""),time.time())); c.commit(); c.close()
                return self._json({"ok":True,"ref":ref})
            if p=="/api/chat":
                d=self._body(); msgs=[m for m in d.get("messages",[]) if m.get("role") in ("user","assistant") and m.get("content")]
                a=ai_reply(msgs,d.get("page","")); c=db(); c.execute("INSERT INTO chats(q,a,page,created) VALUES(?,?,?,?)",(msgs[-1]["content"] if msgs else "",a,d.get("page",""),time.time())); c.commit(); c.close()
                return self._json({"text":a,"html":linkify(a)})
            if p=="/api/subscribe":
                d=self._body(); c=db(); c.execute("INSERT INTO leads(ref,data,page,status,created) VALUES(?,?,?,?,?)","SUB",json.dumps({"email":d.get("email",""),"type":"newsletter"}),d.get("page",""),"new",time.time()); c.commit(); c.close(); return self._json({"ok":True})
            if p=="/api/feedback":
                d=self._body(); c=db(); c.execute("INSERT INTO feedback(page,item,vote,created) VALUES(?,?,?,?)",(d.get("page",""),d.get("item",""),d.get("vote",""),time.time())); c.commit(); c.close(); return self._json({"ok":True})
            if p=="/api/password":
                u=self._user()
                if not u: return self._json({"error":"login required"},401)
                d=self._body(); c=db(); r=c.execute("SELECT 1 FROM users WHERE username=? AND pw=?",(u["username"],H(d.get("old","")))).fetchone()
                if not r or len(d.get("new",""))<4: c.close(); return self._json({"error":"wrong current password or new one too short"},400)
                c.execute("UPDATE users SET pw=? WHERE username=?",(H(d["new"]),u["username"])); c.commit(); c.close(); return self._json({"ok":True})
            m=re.match(r"/api/jobs/([^/]+)/notes",p)
            if m:
                u=self._user()
                if not u: return self._json({"error":"login required"},401)
                d=self._body(); c=db(); c.execute("INSERT INTO notes(job,author,kind,text,created) VALUES(?,?,?,?,?)",(unquote(m.group(1)),u["name"]+" ("+u["role"]+")","note",d.get("text","")[:1000],time.time())); c.commit(); c.close(); return self._json({"ok":True})
            if p=="/api/hit":
                d=self._body(); c=db(); c.execute("INSERT INTO hits(page,ref,created) VALUES(?,?,?)",(d.get("page",""),d.get("ref",""),time.time())); c.commit(); c.close(); return self._json({"ok":True})
            if p=="/api/login":
                d=self._body(); c=db(); u=c.execute("SELECT * FROM users WHERE username=? AND pw=?",(d.get("username",""),H(d.get("password","")))).fetchone(); c.close()
                if not u: return self._json({"error":"Invalid credentials"},401)
                t=secrets.token_hex(16); TOK[t]=dict(u); return self._json({"token":t,"user":{k:u[k] for k in ("username","role","name","client")}})
            if p=="/api/jobs":
                u=self._user()
                if not u or u["role"]!="admin": return self._json({"error":"admin only"},403)
                d=self._body(); c=db(); n=c.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]; job=d.get("job") or f"NL-2026-{n+1:04d}"
                c.execute("INSERT INTO jobs(job,client,customer,origin,destination,mode,cargo,stage,dates,notes,created) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                          (job,d.get("client",""),d.get("customer",""),d.get("origin",""),d.get("destination",""),d.get("mode",""),d.get("cargo",""),1,json.dumps([time.strftime("%d %b")]+[""]*9),d.get("notes",""),time.time())); c.commit(); c.close()
                return self._json({"ok":True,"job":job})
            m=re.match(r"/api/jobs/([^/]+)/advance",p)
            if m:
                u=self._user()
                if not u or u["role"] not in ("admin","employee"): return self._json({"error":"staff only"},403)
                c=db(); j=c.execute("SELECT * FROM jobs WHERE job=?",(unquote(m.group(1)),)).fetchone()
                if not j: c.close(); return self._json({"error":"not found"},404)
                st=min(10,j["stage"]+1); dates=json.loads(j["dates"]); dates[st-1]=time.strftime("%d %b")
                c.execute("UPDATE jobs SET stage=?,dates=? WHERE id=?",(st,json.dumps(dates),j["id"])); c.execute("INSERT INTO notes(job,author,kind,text,created) VALUES(?,?,?,?,?)",(j["job"],u["name"]+" ("+u["role"]+")","event","Milestone "+str(st)+" — "+MILESTONES[st-1],time.time())); c.commit(); c.close(); return self._json({"ok":True,"stage":st})
            m=re.match(r"/api/leads/([0-9]+)/status",p)
            if m:
                u=self._user()
                if not u or u["role"]!="admin": return self._json({"error":"admin only"},403)
                d=self._body(); c=db(); c.execute("UPDATE leads SET status=? WHERE id=?",(d.get("status","new"),int(m.group(1)))); c.commit(); c.close(); return self._json({"ok":True})
            if p=="/api/customers":
                u=self._user()
                if not u or u["role"]!="client": return self._json({"error":"client only"},403)
                d=self._body(); c=db()
                try: c.execute("INSERT INTO users(username,pw,role,name,client,parent) VALUES(?,?,?,?,?,?)",(d["username"],H(d["password"]),"customer",d.get("name",""),u["client"],u["username"])); c.commit()
                except Exception as e: c.close(); return self._json({"error":"username taken"},400)
                c.close(); return self._json({"ok":True})
            return self._json({"error":"unknown"},404)
        except Exception as e:
            return self._json({"error":str(e)},500)
    def do_GET(self):
        p=urlparse(self.path).path
        if p.startswith("/api/"):
            try:
                m=re.match(r"/api/track/([^/]+)",p)
                if m:
                    c=db(); j=c.execute("SELECT * FROM jobs WHERE job=?",(unquote(m.group(1)).upper(),)).fetchone(); c.close()
                    if not j: return self._json({"error":"not found"},404)
                    d=dict(j); d["dates"]=json.loads(d["dates"]); d["milestones"]=MILESTONES; d["docs"]=DOCS; return self._json(d)
                u=self._user()
                if p=="/api/me": return self._json({"user":u} if u else {"user":None})
                if not u: return self._json({"error":"login required"},401)
                c=db()
                if p=="/api/jobs":
                    if u["role"]=="admin" or u["role"]=="employee": rows=c.execute("SELECT * FROM jobs ORDER BY created DESC").fetchall()
                    elif u["role"]=="client": rows=c.execute("SELECT * FROM jobs WHERE client=? ORDER BY created DESC",(u["client"],)).fetchall()
                    else: rows=c.execute("SELECT * FROM jobs WHERE client=? AND customer=? ORDER BY created DESC",(u["client"],u["name"])).fetchall()
                    out=[]
                    for r in rows: d=dict(r); d["dates"]=json.loads(d["dates"]); out.append(d)
                    c.close(); return self._json({"jobs":out,"milestones":MILESTONES,"docs":DOCS})
                m=re.match(r"/api/jobs/([^/]+)/notes",p)
                if m:
                    rows=c.execute("SELECT author,kind,text,created FROM notes WHERE job=? ORDER BY created DESC",(unquote(m.group(1)),)).fetchall(); c.close(); return self._json({"notes":[dict(r) for r in rows]})
                if p=="/api/updates":
                    since=time.time()-86400; scope="" if u["role"] in ("admin","employee") else " AND job IN (SELECT job FROM jobs WHERE client=?)"
                    rows=c.execute("SELECT job,text,created FROM notes WHERE kind='event' AND created>?"+scope+" ORDER BY created DESC LIMIT 20",(since,) if not scope else (since,u["client"])).fetchall(); c.close(); return self._json({"updates":[dict(r) for r in rows]})
                if p=="/api/jobs.csv":
                    rows=c.execute("SELECT job,client,customer,origin,destination,mode,cargo,stage FROM jobs" + ("" if u["role"] in ("admin","employee") else " WHERE client=?"), () if u["role"] in ("admin","employee") else (u["client"],)).fetchall(); c.close()
                    csv="job,client,customer,origin,destination,mode,cargo,stage\n"+"\n".join(",".join('"'+str(x).replace('"',"'")+'"' for x in r) for r in rows)
                    b=csv.encode(); self.send_response(200); self.send_header("Content-Type","text/csv"); self.send_header("Content-Disposition","attachment; filename=nedlloyd-jobs.csv"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b); return
                if p=="/api/leads" and u["role"]=="admin":
                    rows=c.execute("SELECT * FROM leads ORDER BY created DESC LIMIT 200").fetchall(); c.close()
                    return self._json({"leads":[dict(r,data=json.loads(r["data"])) for r in rows]})
                if p=="/api/stats" and u["role"] in ("admin","employee"):
                    s={"jobs":c.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],"open":c.execute("SELECT COUNT(*) FROM jobs WHERE stage<10").fetchone()[0],
                       "delivered":c.execute("SELECT COUNT(*) FROM jobs WHERE stage>=9").fetchone()[0],"leads":c.execute("SELECT COUNT(*) FROM leads WHERE status='new'").fetchone()[0],
                       "hits7d":c.execute("SELECT COUNT(*) FROM hits WHERE created>?",(time.time()-7*86400,)).fetchone()[0],"chats":c.execute("SELECT COUNT(*) FROM chats").fetchone()[0],
                       "top_pages":[dict(r) for r in c.execute("SELECT page,COUNT(*) n FROM hits GROUP BY page ORDER BY n DESC LIMIT 8").fetchall()],
                       "by_mode":[dict(r) for r in c.execute("SELECT mode,COUNT(*) n FROM jobs GROUP BY mode ORDER BY n DESC").fetchall()],
                       "by_client":[dict(r) for r in c.execute("SELECT client,COUNT(*) n FROM jobs GROUP BY client ORDER BY n DESC").fetchall()]}
                    c.close(); return self._json(s)
                if p=="/api/customers" and u["role"]=="client":
                    rows=c.execute("SELECT username,name FROM users WHERE role='customer' AND parent=?",(u["username"],)).fetchall(); c.close(); return self._json({"customers":[dict(r) for r in rows]})
                c.close(); return self._json({"error":"unknown"},404)
            except Exception as e: return self._json({"error":str(e)},500)
        if p.startswith("/.wf_graphql"): return self._json({"csrf":"x"})
        if p in ("","/"): self.send_response(302); self.send_header("Location","/nedlloydgroup.com/"); self.end_headers(); return
        return self.send_static()
    # ---------- static with Range ----------
    def send_static(self):
        path=self.translate_path(self.path)
        if os.path.isdir(path): path=os.path.join(path,"index.html")
        if not os.path.isfile(path):
            nf=os.path.join(ROOT,"nedlloydgroup.com","404.html")
            if path.endswith(".html") and os.path.isfile(nf): path=nf; self.send_response(404); b=open(nf,"rb").read(); self.send_header("Content-Type","text/html"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b); return
            self.send_error(404); return
        size=os.path.getsize(path); rng=self.headers.get("Range"); ctype=self.guess_type(path)
        start,end=0,size-1
        if rng:
            m=re.match(r"bytes=(\d*)-(\d*)",rng)
            if m:
                if m.group(1): start=int(m.group(1))
                if m.group(2): end=int(m.group(2))
                if not m.group(1): start=size-int(m.group(2)); end=size-1
                end=min(end,size-1)
                self.send_response(206); self.send_header("Content-Range",f"bytes {start}-{end}/{size}")
            else: self.send_response(200)
        else: self.send_response(200)
        self.send_header("Content-Type",ctype); self.send_header("Accept-Ranges","bytes"); self.send_header("Content-Length",str(end-start+1)); self.send_header("Cache-Control","public, max-age=3600"); self.end_headers()
        with open(path,"rb") as f:
            f.seek(start); left=end-start+1
            while left>0:
                chunk=f.read(min(1<<16,left))
                if not chunk: break
                try: self.wfile.write(chunk)
                except (BrokenPipeError,ConnectionResetError): return
                left-=len(chunk)

if __name__=="__main__":
    init(); port=int(sys.argv[1]) if len(sys.argv)>1 else 8090
    print(f"Nedlloyd site → http://localhost:{port}/nedlloydgroup.com/   (dashboard: /nedlloydgroup.com/dashboard.html · admin/admin, client/client, customer/customer, employee/employee)")
    ThreadingHTTPServer(("0.0.0.0",port),Handler).serve_forever()
