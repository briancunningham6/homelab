---
name: homelab-immich
description: Interact with the Immich photo & video management server — search, browse, upload, albums, statistics.
metadata:
  openclaw:
    requires:
      - exec
      - web_fetch
---

# Homelab — Immich Photo Management

You can manage the family photo library through the **Immich** server running on the homelab.

## Connection Details

| Key           | Value                                         |
| ------------- | --------------------------------------------- |
| Base URL      | `http://immich.home`                          |
| Internal URL  | `http://immich-server:2283` (from Docker net) |
| API Docs      | `http://immich.home/api`                      |
| Auth          | API key in header `x-api-key`                 |

The API key is stored in the environment variable `IMMICH_API_KEY`.
Always include it: `curl -sH "x-api-key: $IMMICH_API_KEY"`.

## Common Operations

### Search photos by text (CLIP / smart search)

```bash
curl -s http://immich.home/api/search/smart \
  -H "x-api-key: $IMMICH_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "beach sunset", "page": 1, "size": 5}'
```

Response contains `.assets.items[]` with `id`, `originalFileName`, `exifInfo.dateTimeOriginal`, `thumbhash`.

### Get recent photos

```bash
curl -s "http://immich.home/api/timeline/buckets?size=MONTH&isArchived=false" \
  -H "x-api-key: $IMMICH_API_KEY"
```

### Get server statistics

```bash
curl -s http://immich.home/api/server/statistics \
  -H "x-api-key: $IMMICH_API_KEY"
```

Returns `photos`, `videos`, `usage` (bytes) per user and totals.

### List albums

```bash
curl -s http://immich.home/api/albums \
  -H "x-api-key: $IMMICH_API_KEY"
```

### Create album

```bash
curl -s http://immich.home/api/albums \
  -H "x-api-key: $IMMICH_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"albumName": "Vacation 2025", "description": "Summer trip"}'
```

### Add assets to album

```bash
curl -s http://immich.home/api/albums/{albumId}/assets \
  -H "x-api-key: $IMMICH_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"ids": ["asset-id-1", "asset-id-2"]}'
```

### Get a single asset's detail

```bash
curl -s http://immich.home/api/assets/{assetId} \
  -H "x-api-key: $IMMICH_API_KEY"
```

### Download / share a photo thumbnail

```bash
curl -s "http://immich.home/api/assets/{assetId}/thumbnail?size=preview" \
  -H "x-api-key: $IMMICH_API_KEY" -o /tmp/photo.jpg
```

## Guidelines

- Never delete photos without explicit confirmation. Immich has a trash/recycle bin but deletions can be permanent.
- When sharing photo counts or stats, round storage to human-readable units (GB/TB).
- Smart search uses CLIP embeddings — natural-language queries work well ("kids playing in the snow").
- Immich processes uploads asynchronously. After uploading, check job status before confirming completion.
- The Immich web UI is at `http://immich.home` — you can direct users there for browsing.
