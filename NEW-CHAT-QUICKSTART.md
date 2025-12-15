## 🔍 How Claude Accesses Code

**IMPORTANT:** Claude can use the `view` tool to read files from `/opt/pe-sourcing-engine/`

### Example New Chat Opening:
```
Hi! I'm continuing work on PE Sourcing Engine v5.1.

Step 1: Please read CONTEXT-v5.1.md for project overview.

Step 2: I want to modify the authentication system. Please use the view tool to read:
- /opt/pe-sourcing-engine/api/auth.py
- /opt/pe-sourcing-engine/api/dependencies.py

Then we can discuss the changes.
```

### Why This Works Better Than Pasting Code:
✅ Claude reads current code (not outdated snapshots)
✅ More token-efficient
✅ You don't have to copy-paste large files
✅ Claude can re-read files if needed
