# Watch - Listen - Act

Run order (each in its own terminal):
1) MongoDB service (systemd): `sudo systemctl status mongod`
2) Express API: `cd api && npm run dev`
3) FastAPI (uvicorn from notebook cell) OR classic `uvicorn app:app --reload`
4) React web: `cd web && npm run dev`