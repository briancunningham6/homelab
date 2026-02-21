# Content Directory

This directory contains content that is published to the DMZ Raspberry Pi for public access.

## Directory Structure

```
content/
├── blog/           # Hugo blog source
│   ├── content/    # Blog posts (markdown)
│   ├── public/     # Generated static site (after hugo build)
│   └── hugo.toml   # Hugo configuration
└── files/          # Files for public sharing
```

## Publishing Content

Use the `dmz-publish` script to push content to the DMZ Pi:

```bash
# Publish everything
scripts/dmz-publish

# Publish blog only
scripts/dmz-publish blog

# Publish files only
scripts/dmz-publish files

# Check DMZ status
scripts/dmz-publish status
```

## Setting Up Hugo Blog

```bash
# Install Hugo (macOS)
brew install hugo

# Initialize blog
cd content/blog
hugo new site .

# Add a theme (example: PaperMod)
git clone https://github.com/adityatelange/hugo-PaperMod themes/PaperMod
echo "theme = 'PaperMod'" >> hugo.toml

# Create a post
hugo new posts/hello-world.md
# Edit content/posts/hello-world.md

# Preview locally
hugo server -D
# Open http://localhost:1313

# Build for production
hugo build

# Publish to DMZ
cd ../..
scripts/dmz-publish blog
```

## Adding Files to Share

```bash
# Add files to content/files/
cp ~/Documents/shared-file.pdf content/files/

# Publish
scripts/dmz-publish files
```

Files are served via FileBrowser at `https://dmz-pi5.tail*****.ts.net/files/` and require authentication.

## Notes

- The `content/` directory is gitignored (contains personal content)
- Only `content/blog/public/` (generated static files) is synced to DMZ
- The DMZ cannot pull from Mac mini (firewall blocks outbound LAN)
- All syncing happens via Tailscale (encrypted)
