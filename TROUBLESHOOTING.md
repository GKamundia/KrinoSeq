# Frontend Deployment Troubleshooting

## Issue: 404 NOT_FOUND Error

This typically happens with Single Page Applications (SPAs) when the hosting platform doesn't properly handle client-side routing.

## Fixed Solutions:

### Option 1: Redeploy on Vercel with Updated Config

1. **Delete the current Vercel deployment** (if any)
2. **Make sure you're in the root directory** when deploying, not the frontend folder
3. **In Vercel dashboard:**
   - **Root Directory**: `frontend`
   - **Framework Preset**: Create React App
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
   - **Environment Variables**: `REACT_APP_API_URL=https://web-production-b2868.up.railway.app`

### Option 2: Try Netlify Instead

1. Go to [netlify.com](https://netlify.com)
2. "New site from Git"
3. Connect GitHub and select your repository
4. **Build settings:**
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/build`
5. **Environment variables:**
   - `REACT_APP_API_URL` = `https://web-production-b2868.up.railway.app`

### Option 3: Manual Build and Deploy

```bash
# In your project root
cd frontend
npm install
npm run build
```

Then drag the `frontend/build` folder to:

- [Netlify Drop](https://app.netlify.com/drop)
- [Surge.sh](https://surge.sh)

### Option 4: GitHub Pages

```bash
cd frontend
npm install
npm install --save-dev gh-pages
npm run build
npx gh-pages -d build
```

## Quick Test - Static File Hosting

If you want to test quickly:

1. Build the frontend locally: `cd frontend && npm run build`
2. Use Python server: `cd build && python -m http.server 3000`
3. Visit `http://localhost:3000`

## Environment Variable Check

Make sure your frontend has the correct backend URL:

- File: `frontend/.env.production`
- Content: `REACT_APP_API_URL=https://web-production-b2868.up.railway.app`
