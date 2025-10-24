#!/bin/bash
pip install plotly>=5.17.0
python -m streamlit run helpdesk_app.py --server.port=8000 --server.address=0.0.0.0 --server.headless=true
