# Frontend

React (Vite) single-page app for the QFT Bank quantum computing platform.
It talks to the FastAPI backend through `src/api.js` and is served by nginx
in the Docker image (`nginx.conf` proxies `/api` to the backend service).

## Run locally

```bash
npm install
npm run dev        # http://localhost:5173
```

The backend must be running on port 8000 (see the root `README.md`).

## Build

```bash
npm run build      # output in dist/
docker build -t qft-frontend .
```

## Structure

- `src/App.jsx` - layout, navigation and login state
- `src/api.js` - API client (attaches the JWT to every request)
- `src/components/` - one component per platform module (Dashboard, CircuitDesigner,
  Algorithms, Portfolio, PQCReadiness, Frameworks, MLComparison, Analytics, Login)
