# Nedlloyd Logistics website — developer handover (v1.4.0)

This folder is the complete, self-contained website + backend. Nothing else is needed.

## 1. Run locally (any Mac/Linux/Windows with Python 3.9+)
    python3 server.py 8090        # or double-click "START WEBSITE.command" on Mac
    → http://localhost:8090/nedlloydgroup.com/
No pip installs required (standard library only).

## 2. Host it (production)
Option A — one VPS (Hostinger/DigitalOcean/AWS, Ubuntu):
    sudo apt install -y python3 nginx
    copy this folder to /var/www/nedlloyd
    run as a service:  see deploy/nedlloyd.service  (systemd)  → python3 server.py 8090
    nginx reverse proxy: see deploy/nginx.conf (serves https://www.nedlloydgroup.com → 127.0.0.1:8090, rewrites / to /nedlloydgroup.com/)
    HTTPS: sudo certbot --nginx -d nedlloydgroup.com -d www.nedlloydgroup.com
Option B — Docker:  docker build -t nedlloyd . && docker run -p 8090:8090 -v $PWD/data:/app/data nedlloyd
Option C — static-only hosting (Netlify/Vercel/cPanel): upload the folder as-is; all pages, animations and themes work. Features that need the backend fall back gracefully (quote form → email, chat → built-in answers, dashboard needs server).

## 3. Where things live
    nedlloydgroup.com/      every page (index.html = home). Edit text directly in the HTML.
    nedlloydgroup.com/downloads/   Company Profile PDF
    addons/nedlloyd.js      feature layer: themes, WhatsApp, quote form, AI chat/search, tools, accessibility
    addons/nedlloyd.css     styles for the feature layer
    addons/faq.json         the 100 FAQs (chatbot answers from this too) — edit here AND in faq.html
    addons/dashboard.html   Customer Dashboard (copied to nedlloydgroup.com/dashboard.html)
    server.py               static server (video range streaming) + JSON API + SQLite
    data/nedlloyd.db        created on first run: users, jobs, leads, notes, chats, feedback, hits
    cdn.prod.website-files.com/   CSS, fonts, images, videos, 700 scroll-animation frames (do not rename)
    app/, vendor/           animation engine (GSAP, Three.js globe, Lenis, Barba). Do not edit.

## 4. Common edits
    Phone / email / WhatsApp number:  addons/nedlloyd.js  top of file (WA, PHONE, EMAIL) + search-replace in nedlloydgroup.com/*.html
    Logo:                             cdn.prod.website-files.com/…/logo*.svg (replace file, same name) — or search "header-logo" in index.html
    Colours (Blue theme):             addons/nedlloyd.css → html[data-nl-theme="blue"]  (navy #0B2A5B, orange #FF6A00)
    Make Blue the default theme:      addons/nedlloyd.js → var saved='white'  → 'blue'
    Globe flight routes:              app/chunks/my-flights-*.js → AirportsCollection / FlightsCollection
    Client logos strip:               cdn.prod.website-files.com/clients/*.png (replace PNGs, keep names) — home index.html "Our clients"
    Enable full Claude AI answers:    export ANTHROPIC_API_KEY=sk-...  before starting server.py (offline answers work without it)
    Demo logins:                      admin/admin · client/client · customer/customer · employee/employee — change via dashboard "Password" or delete data/nedlloyd.db to reseed
    Analytics:                        add your GA/Meta tag before </head> in every page (United Carriers' tags were removed)

## 5. API (server.py)
    POST /api/leads /api/subscribe /api/feedback /api/hit /api/chat /api/login /api/password
    GET  /api/track/<job>  /api/me  /api/jobs  /api/jobs.csv  /api/jobs/<job>/notes  /api/updates  /api/leads  /api/stats  /api/customers
    Auth: Authorization: Bearer <token from /api/login>

## 6. Known items / next
    - Photos, videos, hero frames and logo are still the reference (United Carriers) assets → replace in the brand pass.
    - About page team profiles are placeholders until names/photos are supplied.
    - FEATURES.md lists 82 built + 17 queued; CHANGELOG.md has version history; QA-REPORT.md has the 6 checks.
