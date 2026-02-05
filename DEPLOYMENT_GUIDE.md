# Deployment Guide - Interview Prep Agent

This guide will help you deploy your Interview Prep Agent to production.

## Architecture
- **Backend**: Deployed to Render
- **Frontend**: Deployed to Vercel
- **Database**: Supabase (already set up)

---

## Part 1: Deploy Backend to Render

### Step 1: Push Code to GitHub (if not already)

```bash
cd "/Users/vizuara/Desktop/Agent Building/Interview-Prep-Agent"
git add .
git commit -m "Prepare for deployment"
git push origin main
```

If you don't have a GitHub repository yet:
```bash
# Create a new repo on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/Interview-Prep-Agent.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Render

1. Go to https://render.com and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `interview-prep-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`

5. **Add Environment Variables** (click "Advanced"):
   ```
   SUPABASE_URL=your_supabase_url_here
   SUPABASE_KEY=your_supabase_anon_key_here
   DATABASE_URL=your_database_connection_string_here
   OPENAI_API_KEY=your_openai_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   ELEVENLABS_VOICE_ID=your_voice_id_here
   ```

6. Click **"Create Web Service"**

7. Wait for deployment (5-10 minutes). Your backend URL will be:
   ```
   https://interview-prep-backend.onrender.com
   ```

---

## Part 2: Deploy Frontend to Vercel

### Step 1: Update Frontend API URL

Before deploying, update the frontend to use your Render backend URL.

1. Find your frontend API configuration file (likely in `frontend/` directory)
2. Update the API base URL from `http://localhost:8000` to your Render URL

**If there's a config file**, update it. **If API calls are hardcoded**, we'll set an environment variable.

### Step 2: Deploy to Vercel

1. Go to https://vercel.com and sign up/login
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository
4. Configure the project:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (auto-detected)
   - **Output Directory**: `.next` (auto-detected)

5. **Add Environment Variable**:
   ```
   NEXT_PUBLIC_API_URL=https://interview-prep-backend.onrender.com
   ```

6. Click **"Deploy"**

7. Your frontend will be live at:
   ```
   https://interview-prep-agent.vercel.app
   ```
   (Or a generated Vercel URL)

---

## Part 3: Update CORS Settings

After deployment, update your backend CORS settings to allow your Vercel domain.

**Edit** `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://interview-prep-agent.vercel.app",  # Add your Vercel URL
        "https://*.vercel.app"  # Allow all Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then commit and push:
```bash
git add backend/main.py
git commit -m "Update CORS for production"
git push
```

Render will automatically redeploy.

---

## Part 4: Test Your Deployment

1. Visit your Vercel URL
2. Upload a resume
3. Start an interview
4. Verify everything works!

---

## Troubleshooting

### Backend Issues
- **Check Logs**: Go to Render dashboard → Your service → Logs
- **Common Issue**: Missing environment variables
- **Solution**: Verify all env vars are set correctly in Render

### Frontend Issues
- **Check Logs**: Go to Vercel dashboard → Your project → Logs
- **Common Issue**: API URL not configured
- **Solution**: Check `NEXT_PUBLIC_API_URL` is set in Vercel

### Database Connection Issues
- **Issue**: Backend can't connect to Supabase
- **Solution**: Verify `SUPABASE_URL` and `SUPABASE_KEY` are correct

---

## Custom Domain (Optional)

### For Frontend (Vercel):
1. Go to your Vercel project → Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed

### For Backend (Render):
1. Go to your Render service → Settings → Custom Domain
2. Add your custom domain
3. Update DNS records as instructed

---

## Environment Variables Summary

**Backend (Render)**:
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `DATABASE_URL`
- `OPENAI_API_KEY`
- `ELEVENLABS_API_KEY`
- `ELEVENLABS_VOICE_ID`

**Frontend (Vercel)**:
- `NEXT_PUBLIC_API_URL` (your Render backend URL)

---

## Cost

- **Render Free Tier**: ✅ Backend hosting (spins down after 15 min of inactivity)
- **Vercel Free Tier**: ✅ Frontend hosting
- **Supabase Free Tier**: ✅ Database (you're already using this)

**Total Cost**: $0/month (Free tier limits apply)

---

## Next Steps

Once deployed, share your Vercel URL and you're live! 🎉

Need help? Check the logs in Render and Vercel dashboards.
