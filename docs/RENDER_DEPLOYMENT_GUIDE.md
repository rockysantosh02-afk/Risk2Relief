# Risk2Relief Render Deployment Guide

Step-by-step instructions for deploying Risk2Relief to Render across Backend (FastAPI Web Service), Frontend (React Static Site), and Managed PostgreSQL Database.

---

## 1. Prerequisites

1. A [Render Account](https://render.com).
2. A [Firebase Project](https://console.firebase.google.com) with **Authentication** enabled (Email/Password and/or Google Sign-In).
3. The Risk2Relief repository pushed to GitHub or GitLab.

---

## 2. Deployment Method A: Automated Render Blueprint (Recommended)

The repository includes a ready-to-use `render.yaml` Blueprint specification.

1. In Render Dashboard, click **New +** → **Blueprint**.
2. Connect your **Risk2Relief** repository.
3. Render will automatically parse `render.yaml` and discover:
   - **`risk2relief-postgres`**: Managed PostgreSQL database.
   - **`risk2relief-backend`**: FastAPI Python Web Service.
   - **`risk2relief-frontend`**: React Vite Static Site.
4. Click **Apply**.
5. Once initial provisioning completes, configure the environment variables as outlined below.

---

## 3. Deployment Method B: Manual Service Creation

### Step 1: Create Managed PostgreSQL Database
1. In Render, click **New +** → **PostgreSQL**.
2. **Name**: `risk2relief-postgres`
3. **Database**: `risk2relief_db`
4. **User**: `risk2relief_user`
5. **Plan**: Free / Starter
6. Click **Create Database** and copy the **Internal Database URL** (or External URL).

### Step 2: Create Backend Web Service
1. Click **New +** → **Web Service**.
2. Connect the Risk2Relief repository.
3. **Name**: `risk2relief-backend`
4. **Language**: `Python 3`
5. **Root Directory**: `backend`
6. **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
7. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
8. **Health Check Path**: `/health`
9. **Environment Variables**:
   - `DATABASE_URL`: *(Paste your Render PostgreSQL connection string)*
   - `ENVIRONMENT`: `production`
   - `DEBUG`: `false`
   - `LOG_LEVEL`: `INFO`
   - `FIREBASE_PROJECT_ID`: `your-firebase-project-id`
   - `CORS_ORIGINS`: `http://localhost:5173` *(Will be updated with the frontend Render URL in Step 4)*
10. Click **Create Web Service**.
11. Note your deployed Backend URL (e.g. `https://risk2relief-backend.onrender.com`).

### Step 3: Create Frontend Static Site
1. Click **New +** → **Static Site**.
2. Connect the Risk2Relief repository.
3. **Name**: `risk2relief-frontend`
4. **Root Directory**: `frontend`
5. **Build Command**: `npm install && npm run build`
6. **Publish Directory**: `dist`
7. **Redirects/Rewrites**:
   - **Type**: `Rewrite`
   - **Source**: `/*`
   - **Destination**: `/index.html`
8. **Environment Variables**:
   - `VITE_API_BASE_URL`: `https://risk2relief-backend.onrender.com` *(Your backend Render URL)*
   - `VITE_FIREBASE_API_KEY`: `AIzaSy...`
   - `VITE_FIREBASE_AUTH_DOMAIN`: `your-project.firebaseapp.com`
   - `VITE_FIREBASE_PROJECT_ID`: `your-project-id`
   - `VITE_FIREBASE_APP_ID`: `1:...`
9. Click **Create Static Site**.
10. Note your deployed Frontend URL (e.g. `https://risk2relief-frontend.onrender.com`).

---

## 4. Post-Deployment URL Integration Checklist

Once both services are deployed, perform the final 2-minute wiring:

1. **Update Backend CORS**:
   - Go to `risk2relief-backend` → **Environment**.
   - Set `CORS_ORIGINS`: `https://risk2relief-frontend.onrender.com,http://localhost:5173`
   - Save changes (Render will trigger a quick zero-downtime redeploy).

2. **Add Authorized Domain in Firebase Console**:
   - Open [Firebase Console](https://console.firebase.google.com) → **Authentication** → **Settings** → **Authorized domains**.
   - Click **Add domain** and enter `risk2relief-frontend.onrender.com`.

3. **Verify Connection**:
   - Open `https://risk2relief-frontend.onrender.com`.
   - Inspect browser developer tools (Network tab).
   - Ensure `GET https://risk2relief-backend.onrender.com/health` returns HTTP 200 `{"status":"healthy",...}`.
   - Run a Live Scenario from the UI to confirm seamless end-to-end telemetry evaluation.
