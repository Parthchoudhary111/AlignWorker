# Deploying AlignWorker to Cloud (Render & Railway)

AlignWorker is containerized with Playwright Chromium pre-installed. You can deploy it to **Render** or **Railway** in just a few clicks directly from your GitHub repository.

---

## 🌐 Option 1: Deploy on Render (Recommended Free/Standard Cloud)

Render offers free and low-cost Docker web services with automatic HTTPS and continuous deployment on every Git push.

### Step-by-Step Instructions:

1. **Push your latest changes to GitHub**:
   ```bash
   git add .
   git commit -m "Add Docker and cloud deployment configs"
   git push origin main
   ```

2. **Go to Render**:
   - Visit [dashboard.render.com](https://dashboard.render.com/) and sign in with GitHub.

3. **Create a New Web Service**:
   - Click **New +** > **Web Service**.
   - Select **Build and deploy from a Git repository**.
   - Choose your repository: `Parthchoudhary111/AlignWorker`.

4. **Configure Service Settings**:
   - **Name**: `alignworker` (or any custom name)
   - **Language / Runtime**: **Docker** (Render will automatically detect the `Dockerfile`)
   - **Region**: Choose the region closest to you (e.g., Oregon, Frankfurt, Singapore)
   - **Instance Type**: **Free** or **Starter**

5. **Environment Variables (Optional)**:
   Under **Environment Variables**, add:
   - `GEMINI_API_KEY`: *(Optional)* Your Google Gemini API key if you want live LLM extraction. (If left unset, AlignWorker automatically uses its deterministic cognitive engine!).

6. **Deploy**:
   - Click **Deploy Web Service**.
   - Render will build the Docker container and start your service.
   - Once the deploy logs display `Application startup complete`, your app is live!

7. **Access your Live App**:
   - **Neural Agent Studio:** `https://your-app-name.onrender.com/agent`
   - **AcmeFlow ERP Ledger:** `https://your-app-name.onrender.com/`

---

## 🚂 Option 2: Deploy on Railway

Railway provides fast deployment with Docker container support and built-in metric dashboards.

### Step-by-Step Instructions:

1. **Push your latest changes to GitHub**:
   ```bash
   git add .
   git commit -m "Add Docker and cloud deployment configs"
   git push origin main
   ```

2. **Go to Railway**:
   - Visit [railway.com](https://railway.com/) and log in with your GitHub account.

3. **Start New Project**:
   - Click **New Project** > **Deploy from GitHub repo**.
   - Select `Parthchoudhary111/AlignWorker`.

4. **Automatic Detection**:
   - Railway will detect the `Dockerfile` and `railway.json` automatically and begin building.

5. **Generate Public Domain**:
   - Go to your service's **Settings** tab.
   - Under **Networking** / **Public Networking**, click **Generate Domain**.
   - Railway assigns a public URL (e.g. `alignworker-production.up.railway.app`).

6. **Environment Variables (Optional)**:
   - In the **Variables** tab, you can add `GEMINI_API_KEY` if desired.

7. **Access the App**:
   - Visit `https://your-service.up.railway.app/agent` to interact with the Autonomous Agent Command Console.

---

## 🧪 Testing Locally via Docker (Optional)

If you have Docker Desktop running locally, you can test the production image before deploying:

```bash
# Build the Docker image
docker build -t alignworker:latest .

# Run the container locally on port 8000
docker run -p 8000:8000 -e PORT=8000 alignworker:latest
```

Then open `http://localhost:8000/agent` in your browser.
