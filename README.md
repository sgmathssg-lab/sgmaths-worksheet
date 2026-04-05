# SGMaths Worksheet Generator — Deployment Guide

## What's in this folder

| File | What it does |
|---|---|
| `app.py` | The web server — receives requests, generates PDF, sends it back |
| `make_worksheet.py` | The PDF generator (the script we built) |
| `sgmaths_logo.png` | Your logo |
| `requirements.txt` | List of Python packages needed |
| `Procfile` | Tells Render how to start the server |
| `wordpress-embed.html` | Paste this into your WordPress page |

---

## Step 1 — Create a GitHub account

1. Go to **github.com**
2. Click **Sign up**
3. Enter your email, create a password, choose a username
4. Verify your email

---

## Step 2 — Create a new GitHub repository

1. Once logged in, click the **+** button (top right) → **New repository**
2. Name it: `sgmaths-worksheet`
3. Set it to **Public**
4. Click **Create repository**

---

## Step 3 — Upload your files to GitHub

1. On your new repository page, click **uploading an existing file**
2. Drag and drop ALL files from this folder:
   - `app.py`
   - `make_worksheet.py`
   - `sgmaths_logo.png`
   - `requirements.txt`
   - `Procfile`
3. Scroll down, click **Commit changes**

---

## Step 4 — Create a Render account

1. Go to **render.com**
2. Click **Get Started** → sign up with GitHub (use the same account)
3. Authorise Render to access your GitHub

---

## Step 5 — Deploy on Render

1. In Render dashboard, click **New** → **Web Service**
2. Select your `sgmaths-worksheet` repository
3. Fill in these settings:
   - **Name**: sgmaths-worksheet
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free
4. Click **Create Web Service**
5. Wait ~3 minutes for it to build and deploy
6. Copy your URL — it looks like: `https://sgmaths-worksheet.onrender.com`

---

## Step 6 — Connect to your WordPress site

1. Open `wordpress-embed.html` in a text editor (Notepad is fine)
2. Find this line near the bottom:
   ```
   var SGM_SERVER = "https://YOUR_RENDER_URL.onrender.com";
   ```
3. Replace `YOUR_RENDER_URL` with your actual Render URL from Step 5
4. Copy the entire contents of the file
5. In WordPress: edit any page → click **+** → search **Custom HTML** → paste

---

## Done! ✅

Your worksheet generator is now live on sgmaths.sg.
Visitors can pick topics, click Download, and get a PDF instantly.

---

## Notes

- The free Render plan "spins down" after 15 minutes of inactivity.
  The first request after that takes ~30 seconds to wake up.
  This is fine for a worksheet generator — just show a loading message.
  (The wordpress-embed.html already does this.)

- If you want it always-on, upgrade to Render's $7/month plan.
