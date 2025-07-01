# Frontend Deployment Guide

## Option 1: Vercel (Recommended)

### Step 1: Get Your Railway Backend URL
1. Go to your Railway dashboard
2. Click on your genome-filtering-tool project
3. Your backend URL is: `https://web-production-b2868.up.railway.app`

### Step 2: Update Environment Variables
1. Open `frontend/.env.production`
2. The URL is already set to your Railway URL:
   ```
   REACT_APP_API_URL=https://web-production-b2868.up.railway.app
   ```

### Step 3: Deploy to Vercel
1. Go to [vercel.com](https://vercel.com)
2. Sign up with your GitHub account
3. Click "Import Project"
4. Select your genome-filtering-tool repository
5. Configure deployment settings:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Create React App
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
6. Add environment variable in Vercel dashboard:
   - Name: `REACT_APP_API_URL`
   - Value: Your Railway backend URL
7. Click "Deploy"

## Option 2: Netlify

### Deploy via Netlify
1. Go to [netlify.com](https://netlify.com)
2. Connect your GitHub repository
3. Set build settings:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/build`
4. Add environment variables in Netlify dashboard

## Option 3: Manual Build and Upload

### Local Build
```bash
cd frontend
npm install
npm run build
```

Then drag and drop the `build` folder to:
- Netlify Drop (netlify.com/drop)
- Surge.sh
- Any static hosting service

## Testing Your Deployment

Once deployed, test these features:
1. **File Upload**: Upload a FASTA file
2. **API Connection**: Check browser console for API calls
3. **Filtering**: Try applying filters
4. **Download**: Download filtered results

## Troubleshooting

### CORS Issues
If you get CORS errors, update your backend CORS settings in `backend/api/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-url.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
