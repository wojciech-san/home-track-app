# Home Track

Monthly utility usage tracker (water, energy, gas, rent) across multiple properties.

```
home-track-app/
├── frontend/  → Streamlit app
│   ├── streamlit_app.py     → router: page config, sidebar nav (st.navigation)
│   ├── .streamlit/config.toml → color theme
│   ├── lib/api.py            → HTTP client for the backend
│   ├── views/
│   │   ├── home.py
│   │   ├── dashboard.py
│   │   ├── properties.py
│   │   ├── utility_types.py
│   │   ├── usage.py
│   │   └── leases.py
│   └── requirements.txt
└── backend/   → FastAPI backend + Postgres models
    ├── app/
    ├── scripts/
    ├── requirements.txt
    └── README.md
```

### Frontend (Streamlit)

Requires the backend running (see below) — the frontend talks to it over HTTP.

```
cd frontend
pip install -r requirements.txt
streamlit run streamlit_app.py
```

By default the app connects to `http://localhost:8000`. If your backend runs elsewhere, set
`API_BASE_URL` before starting Streamlit:

```
API_BASE_URL=https://your-backend-host streamlit run streamlit_app.py
```

Sidebar, grouped in two sections: **Overview** (landing page + **Dashboard** — charts of usage and
cost over time), and **Manage data** (**Properties**, **Utility Types** — rates drive the cost
auto-calculation, **Usage** — log a monthly reading, **Leases** — tenant info, add or end a lease).

> If deploying on Streamlit Community Cloud, set the app's main file path to `frontend/streamlit_app.py`.

### Backend (FastAPI)

See [`backend/README.md`](backend/README.md) for setup and API endpoints.
