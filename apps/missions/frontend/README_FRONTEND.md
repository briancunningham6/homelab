# Missions Frontend

React + TypeScript frontend for the Missions application.

## Status: Phase 1 Scaffold

This is the initial scaffold. Complete component implementations will be added as Phase 1 progresses.

## Missing Components (to be created):

```
src/
├── components/
│   ├── Layout.tsx          # Main layout wrapper
│   ├── MissionCard.tsx     # Mission list item
│   └── MissionForm.tsx     # Create/edit form
├── pages/
│   ├── Dashboard.tsx       # Mission list
│   ├── MissionDetail.tsx   # Mission detail view
│   ├── MissionCreate.tsx   # Create mission page
│   ├── Settings.tsx        # Settings page
│   └── NotFound.tsx        # 404 page
├── api/
│   └── client.ts           # API client
└── hooks/
    └── useMissions.ts      # React Query hooks
```

## To Complete Frontend

Run this script to generate placeholder components:

```bash
cd /Users/user/dev/homelab/apps/missions
./scripts/generate-frontend-placeholders.sh
```

Or manually create each file following the TypeScript/React patterns.

## Development

```bash
cd frontend
npm install
npm run dev
```

Access at http://localhost:5173
