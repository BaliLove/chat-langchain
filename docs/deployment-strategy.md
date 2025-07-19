# Deployment Strategy

## Branch Structure

- `master` - Deploys both frontend (Vercel) and backend (LangSmith)
- `frontend` - Deploys only frontend to Vercel
- `backend` - Deploys only backend to LangSmith

## How to Use

### Frontend-Only Changes
```bash
# Create and switch to frontend branch
git checkout -b frontend

# Make your changes
git add .
git commit -m "Frontend: Fix thread visibility"
git push origin frontend

# This triggers ONLY Vercel deployment
```

### Backend-Only Changes
```bash
# Create and switch to backend branch
git checkout -b backend

# Make your changes
git add .
git commit -m "Backend: Update graph logic"
git push origin backend

# This triggers ONLY LangSmith deployment
```

### Full Stack Changes
```bash
# Work on master branch
git checkout master

# Make your changes
git add .
git commit -m "Full stack: Add new feature"
git push origin master

# This triggers BOTH deployments
```

## Setting Up Branch Deployments

### Vercel Configuration
1. Go to Vercel Dashboard → Your Project → Settings → Git
2. Add a new deployment rule:
   - Branch: `frontend`
   - Production: Yes (or Preview if you prefer)
3. The `master` branch remains as is

### LangSmith Configuration
1. In your LangSmith deployment settings
2. Change the trigger branch from `master` to `backend`
3. Or keep `master` if you want both to deploy

## Merging Strategy

When ready to sync everything:
```bash
# Merge frontend changes to master
git checkout master
git merge frontend

# Merge backend changes to master
git merge backend

# Push to update production
git push origin master
```