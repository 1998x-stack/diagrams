# traj-gep · Specimen Archive (viz)

A dark-academic specimen catalogue for the GEP genes mined under
`traj-gep/output/{wzp,zzj}/genes.json`.

```
viz/
├── backend/
│   ├── main.py           FastAPI: /api/genes, /api/genes/{project}, /api/stats, static
│   └── requirements.txt
└── frontend/
    └── index.html        Vue 3 (CDN) · Fraunces / Inter Tight / JetBrains Mono / Noto Serif SC
```

## Run

```bash
cd traj-gep/viz
python3 -m pip install -r backend/requirements.txt
python3 -m uvicorn backend.main:app --port 8765 --reload
```

Open <http://localhost:8765>.

## Endpoints

- `GET  /api/genes`               — both projects, enriched with `project` / `family`
- `GET  /api/genes/{project}`     — `wzp` or `zzj`
- `GET  /api/stats`               — counts, top signals, evidence totals

## Aesthetic notes

- **Specimen archive × academic journal** — dark ink ground (`#0c0a08`),
  parchment text (`#ece1cd`), single bold accent rust (`#c2542a`), with
  family-coded sage/oxide/crimson/gold for gene category bars.
- Display serif **Fraunces** (variable optical-size + SOFT axis) for big
  numerals and titles; **Noto Serif SC** for Chinese titles; **JetBrains
  Mono** for IDs and chip labels; **Inter Tight** for body sans.
- Each gene card carries a left rule tinted by category, a specimen
  number in monospace, the Chinese title in heavy serif, the English
  subtitle in italic Fraunces, the first two strategy steps with
  numbered marginalia, and a footer carrying `frequency` and
  `session_count`.
- Click any card → modal with the full 7-field gene plus `_provenance`.
