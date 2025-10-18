# Watch - Listen - Act

Run order (each in its own terminal):
1) MongoDB service (systemd): `sudo systemctl status mongod`
2) Express API: `cd api && npm run dev` (API listening on http://localhost 3001)
3) FastAPI run notebook from folder services/ `setup.ipynb` to install the requirements
4) FastAPI run notebook from folder sevices/ `server.ipynb` (Uvicorn running on http://0.0.0.0:8000)
4) React web: `cd web && npm run dev` ( Access from browser ➜  Local: http://localhost:5173/)