# PE Sourcing Engine v5.1 - Code Snapshot
**Created:** December 15, 2025  
**Purpose:** Quick reference for key files when starting new chat

**Note:** This is a snapshot. Always check actual files for most recent version!

---

## Critical File Paths

When asking Claude to modify code, reference these paths and ask Claude to use the `view` tool to read them first.

### Authentication System
```
/opt/pe-sourcing-engine/api/auth.py
/opt/pe-sourcing-engine/api/dependencies.py
/opt/pe-sourcing-engine/api/models.py
```

### Main Application
```
/opt/pe-sourcing-engine/api/main.py (LARGE - 1000+ lines)
```

### Templates (most important)
```
/opt/pe-sourcing-engine/api/templates/base.html
/opt/pe-sourcing-engine/api/templates/dashboard.html
/opt/pe-sourcing-engine/api/templates/companies.html
/opt/pe-sourcing-engine/api/templates/admin_users.html
```

### Database
```
/opt/pe-sourcing-engine/schema.sql
/opt/pe-sourcing-engine/schema_v5.1.sql
/opt/pe-sourcing-engine/etl/utils/db.py
```

### Docker
```
/opt/pe-sourcing-engine/Dockerfile
/opt/pe-sourcing-engine/docker-compose.yml
/opt/pe-sourcing-engine/.env.example
```

### Pipeline
```
/opt/pe-sourcing-engine/run_pipeline.py
/opt/pe-sourcing-engine/enrich_companies.py
/opt/pe-sourcing-engine/etl/score/calculate_scores.py
```

---

## How to Use This in New Chat

### Example 1: Modifying Authentication
```
I need to add 2FA to the authentication system.

First, please read:
1. CONTEXT-v5.1.md (for project overview)
2. Use view tool to read /opt/pe-sourcing-engine/api/auth.py
3. Use view tool to read /opt/pe-sourcing-engine/api/dependencies.py

Then let's discuss implementation.
```

### Example 2: Adding New Route
```
I want to add a new admin route for viewing activity logs.

Please read:
1. CONTEXT-v5.1.md (for project context)
2. Use view tool to read /opt/pe-sourcing-engine/api/main.py (focus on admin routes section)
3. Use view tool to read /opt/pe-sourcing-engine/api/templates/base.html (for template structure)

Then help me implement it.
```

### Example 3: Docker Issues
```
Docker build is failing.

Please read:
1. Use view tool to read /opt/pe-sourcing-engine/Dockerfile
2. Use view tool to read /opt/pe-sourcing-engine/docker-compose.yml
3. Use view tool to read /opt/pe-sourcing-engine/requirements.txt

Here's the error: [PASTE ERROR]
```

---

## File Size Warnings

**Large files** (may hit token limits if reading all at once):
- `api/main.py` - ~1000 lines (can use view_range to read sections)
- `CONTEXT-v5.1.md` - ~1500 lines (comprehensive context)

**Strategy for large files:**
Ask Claude to read specific sections:
```
Use view tool to read /opt/pe-sourcing-engine/api/main.py with view_range [1, 100]
(First 100 lines - imports and setup)

Then read lines [600, 700] (admin routes section)
```

---

## Quick Git Snapshot Commands

If you need to show Claude recent changes:
```bash
# Show last 5 commits
git log --oneline -5

# Show what changed in a specific file
git log -p --follow api/main.py | head -100

# Show diff of uncommitted changes
git diff api/main.py

# Show specific commit
git show <commit-hash>
```

Paste these outputs into chat to give Claude recent context.

---

## File Tree for Reference
```
/opt/pe-sourcing-engine/
├── api/
│   ├── __init__.py
│   ├── auth.py           ← JWT, passwords (200 lines)
│   ├── dependencies.py   ← Auth checks (100 lines)
│   ├── models.py         ← SQLAlchemy (150 lines)
│   ├── main.py          ← Main app (1000 lines) ⚠️
│   └── templates/       ← 10 HTML files
├── etl/
│   ├── discover/        ← Google Places
│   ├── score/          ← Scoring algorithm
│   └── utils/
│       └── db.py       ← Database utils (100 lines)
├── enrich/             ← 11 enricher modules
├── config/
│   ├── settings.yaml   ← Pipeline config
│   └── secrets.env     ← API keys (NOT in git)
├── Dockerfile          ← Docker image (50 lines)
├── docker-compose.yml  ← Services (150 lines)
├── requirements.txt    ← Dependencies (50 lines)
├── schema.sql         ← Base schema (100 lines)
└── schema_v5.1.sql    ← v5.1 migration (130 lines)
```

---

## Best Practice Workflow

### Starting New Chat - Recommended Approach

1. **Start with context:**
```
Hi! I'm working on PE Sourcing Engine v5.1.
Please read CONTEXT-v5.1.md to understand the project.
```

2. **Then specify what you're working on:**
```
I want to modify [FEATURE].
Please use the view tool to read:
- /opt/pe-sourcing-engine/[relevant file 1]
- /opt/pe-sourcing-engine/[relevant file 2]
```

3. **Claude reads the files and is ready to help!**

---

## Why This Approach Works

✅ **Always current** - Claude reads live files, not snapshots  
✅ **Selective** - Only read files you're actually working on  
✅ **Token efficient** - Don't load entire codebase  
✅ **Accurate** - No risk of outdated snapshot  

---

**Do NOT paste entire files into chat unless:**
- File is small (<100 lines)
- You're debugging specific code
- Claude specifically asks for it

**Instead:** Tell Claude to use the `view` tool!
