# Home Track

Monthly utility usage tracker (water, energy, gas, rent) across multiple properties.

```
home-track-app/
├── frontend/  → Streamlit dashboard
│   ├── streamlit_app.py
│   └── requirements.txt
└── backend/   → FastAPI backend + Postgres models
    ├── app/
    ├── scripts/
    ├── requirements.txt
    └── README.md
```

### Frontend (Streamlit)

```
cd frontend
pip install -r requirements.txt
streamlit run streamlit_app.py
```

> If deploying on Streamlit Community Cloud, set the app's main file path to `frontend/streamlit_app.py`.

### Backend (FastAPI)

See [`backend/README.md`](backend/README.md) for setup and API endpoints.
