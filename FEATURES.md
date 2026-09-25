# Nedlloyd website — feature plan vs original nedlloydgroup.com  (✅ built · 🔜 next · 🧩 needs input)

## Reach & lead capture
1 ✅ Get a Quote form (mode, origin, destination, cargo, date) → leads DB + reference
2 ✅ WhatsApp floating button, pre-filled message
3 ✅ Post-quote "continue on WhatsApp" handoff with reference
4 ✅ Download Company Profile PDF (top bar, every page)
5 ✅ Every "Talk with us / Work with us / Email us" CTA opens the quote form
6 ✅ Lead inbox in Admin dashboard with pipeline (new→contacted→quoted→won→lost)
7 ✅ Mailto fallback if server offline
8 🧩 Email/WhatsApp alert to sales on new lead (needs SMTP / WhatsApp Business API)
9 ✅ Callback request (quote form mode)
10 ✅ Partner / Vendor registration (quote form mode)
11 ✅ Careers apply form → leads inbox (CV file upload next)
12 ✅ Newsletter signup endpoint
13 ✅ Google Maps directions for all 10 offices (Offices page)
14 ✅ Click-to-call on every phone number
15 ✅ UTM / gclid / fbclid captured on leads
## AI
16 ✅ AI assistant — offline knowledge base + 100 FAQs; Claude-powered when ANTHROPIC_API_KEY set
17 ✅ AI site search (65 pages)
18 ✅ Chat transcripts stored (MIS)
19 🔜 AI quote pre-qualifier (collects details, files lead)
20 🔜 Hindi + regional languages
21 🔜 AI reply drafts for leads (admin)
22 🔜 "Which service do I need?" wizard
23 🔜 Voice input on mobile
## Tracking & client experience
24 ✅ Track by Job Number in assistant (10 milestones + dates)
25 ✅ Customer Dashboard — Admin / Client / Client's Customer / Employee
26 ✅ Client creates read-only logins for its own customers
27 ✅ Milestone timeline with document slots
28 ✅ Employee "Advance milestone"; Admin "Create job"
29 ✅ MIS: jobs by mode/client, visits, chats, leads
30 🔜 Document upload/download per milestone
31 🧩 Email/WhatsApp milestone alerts
32 ✅ Public tracking page (no login) — track.html?job=…
33 🔜 Live job routes on globe
34 ✅ Export jobs CSV
35 🔜 Client KPIs (on-time %, transit days, spend)
## Design & UX
36 ✅ Theme toggle White / Blue / Dark, remembered
37 ✅ Back-to-top, toasts
38 ✅ Delhi-centric globe routes (19 lanes)
39 ✅ Client logo strip (9 clients)
40 🧩 Brand pass — logo, navy/orange default, project-cargo photography (needs assets)
41 🧩 Hero video — project-cargo footage
42 ✅ Offices & Warehouses page (10 locations)
43 ✅ Case Studies page (6 stories) + home cards
44 🔜 Downloadable certificates
## Content & SEO
45 ✅ Real company data (address, phones, offices, founded 2001, 20+ warehouses, values, motto)
46 ✅ 12 services incl. Charter, 4PL, Courier, E-commerce, Reverse
47 ✅ 12 industries incl. BESS, Solar, Wind, Defence, Telecom
48 🔜 Insights articles (market updates)
49 ✅ Terms of Use + Privacy (DPDP 2023, SMS consent) rewritten
50 ✅ JSON-LD Organization, sitemap.xml, robots.txt
51 🔜 Hindi toggle
52 🧩 Analytics / pixel under Nedlloyd IDs (UC's removed)
53 ✅ FAQ page — 100 Q&As with live search
54 ✅ Quick-links tab in assistant (14 short links)
## Ops
55 ✅ Range-capable server, SQLite, one-click START
56 🔜 Deploy to Hostinger/Vercel + HTTPS
57 🔜 Admin content editor

## v1.3.0 additions (25 Sep 2026)
58 ✅ Freight Tools page — CBM / volumetric / chargeable weight calculator
59 ✅ Transit time estimator (8 lanes × air/sea/land)
60 ✅ Document checklist generator (import, export, ODC, DG, domestic) with copy
61 ✅ Freight Glossary — 40 terms
62 ✅ Incoterms 2020 guide
63 ✅ Container & ULD size reference
64 ✅ Custom 404 page (server returns it for missing pages)
65 ✅ Cookie / privacy notice bar (DPDP)
66 ✅ Scroll progress bar
67 ✅ "Open now / Opens 9AM IST" live indicator in top bar
68 ✅ Share this page (native share / WhatsApp)
69 ✅ Keyboard shortcuts — / search · ? ask AI · q quote · Esc close
70 ✅ Copy tracking link + print on public Track page
71 ✅ Dashboard job filter (text + status)
72 ✅ Build tag on every page (meta nl-build) + VERSION / CHANGELOG

## v1.4.0 additions — 25 user-experience features (25 Sep 2026)
73 ✅ Hindi / English toggle (chat greeting, chips, buttons)
74 ✅ Larger-text toggle (A+)
75 ✅ Reduce-motion toggle
76 ✅ High-contrast mode
77 ✅ Voice input in chat (mic)
78 ✅ Read answers aloud (speaker)
79 ✅ Chat history persists across pages
80 ✅ Email this chat
81 ✅ Clear chat
82 ✅ "Which service do I need?" wizard (3 questions → recommendation)
83 ✅ Quick-quote flow inside chat (7 questions → lead filed)
84 ✅ Recently viewed pages in Quick links
85 ✅ FAQ "Helpful? 👍👎" votes (stored)
86 ✅ Page feedback widget on every content page
87 ✅ Estimated read time + Home › breadcrumb on content pages
88 ✅ Auto table-of-contents on long pages (FAQ, Incoterms, Tools…)
89 ✅ Print-friendly stylesheet (widgets/header/video hidden)
90 ✅ Offline / back-online notices
91 ✅ "We'll reply by <day>" ETA on quote confirmation (business-hours aware)
92 ✅ Share shipment status on WhatsApp (Track page)
93 ✅ Dashboard: notes & comments per job
94 ✅ Dashboard: activity log (milestone events) per job
95 ✅ Dashboard: 🔔 updates in last 24h
96 ✅ Dashboard: print job sheet + WhatsApp about this job
97 ✅ Dashboard: change password
98 ✅ Careers job alerts (email subscribe)
99 ✅ HTML Site Map page
