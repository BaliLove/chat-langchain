# Pre-deployment Checklist

Before committing and deploying, run these checks locally:

## Frontend Checks

```bash
cd frontend

# 1. Check TypeScript types
yarn check

# 2. Run ESLint
yarn lint

# 3. Test the build locally
yarn build

# Or run all checks at once:
yarn pre-deploy
```

## Common Issues to Check

1. **TypeScript Errors**
   - Missing imports
   - Type mismatches
   - Undefined properties

2. **ESLint Warnings**
   - Missing dependencies in useEffect
   - Unused variables
   - Import order

3. **Build Errors**
   - Dynamic imports
   - Missing environment variables
   - Client/Server component mismatches

## Quick Fixes

- For missing useEffect dependencies: Add them or use `// eslint-disable-next-line`
- For type errors: Check the actual interface/type definition
- For build errors: Ensure all components that use browser APIs have `'use client'`

## Environment Variables

Ensure all required env vars are set in Vercel:
- NEXT_PUBLIC_SUPABASE_URL
- NEXT_PUBLIC_SUPABASE_ANON_KEY
- NEXT_PUBLIC_API_URL
- SUPABASE_SERVICE_ROLE_KEY (for API routes)