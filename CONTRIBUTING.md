# Contributing to DealGenome

Thank you for your interest in contributing to the DealGenome PE Sourcing Engine! This document outlines the development workflow and standards for this project.

---

## 📋 Table of Contents

1. [Development Environment](#development-environment)
2. [Development Workflow](#development-workflow)
3. [Code Standards](#code-standards)
4. [Commit Guidelines](#commit-guidelines)
5. [Testing](#testing)
6. [Git Workflow](#git-workflow)
7. [Important Notes](#important-notes)

---

## 🖥️ Development Environment

This project uses a **two-server architecture**:

### Source / Development Server (dg)
- **Purpose:** Primary development and testing
- **OS:** Fedora
- **Runtime:** systemd service (`pe-sourcing-gui.service`)
- **Database:** PostgreSQL on 10.55.55.55
- **Docker:** ❌ NOT used
- **Location:** `/opt/pe-sourcing-engine/`

**All development happens here first.**

### Docker Deployment Server (docker-dg)
- **Purpose:** Production-ready containerized deployment
- **Runtime:** Docker Compose
- **Docker:** ✅ Required
- **Update:** Only after validation on dg

---

## 🔄 Development Workflow

### 1. Making Changes
```bash
# Navigate to project
cd /opt/pe-sourcing-engine

# Edit files
nano <file>

# Restart service to test changes
sudo systemctl restart pe-sourcing-gui.service

# Check service status
sudo systemctl status pe-sourcing-gui.service

# View logs
sudo journalctl -u pe-sourcing-gui.service -f
```

### 2. Verification

Before committing, always verify:
```bash
# Check dashboard loads
curl http://10.55.55.55:8000/api/status

# Check for errors in logs
tail -f /opt/pe-sourcing-engine/logs/pipeline.log

# Test affected functionality
# (e.g., if you changed discovery, run discovery)
```

### 3. Commit and Push
```bash
# Check what changed
git status

# Stage your changes
git add <files>

# Commit with descriptive message
git commit -m "v5.5: Your descriptive message here"

# Push to GitHub
git push origin main
```

---

## 📝 Code Standards

### Python Style
- **Version:** Python 3.13+
- **Style Guide:** Follow PEP 8 guidelines
- **Type Hints:** Encouraged for public functions
- **Docstrings:** Required for modules, classes, and public functions

**Example:**
```python
def enrich_company(company: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich company data with external APIs.
    
    Args:
        company: Company dictionary with basic info
        
    Returns:
        Dictionary with enriched data fields
    """
    # Implementation
    pass
```

### File Organization
- Keep functions focused and small (< 50 lines when possible)
- Group related functionality into modules
- Use clear, descriptive names
- Comment complex logic

### Database Changes
- Always update `schema/current.sql`
- Document schema changes in `CHANGELOG.md`
- Test migrations on development server first
- Backup database before applying schema changes

---

## 💬 Commit Guidelines

### Commit Message Format
```
v[VERSION]: Brief description (50 chars or less)

- Detailed point 1
- Detailed point 2
- Detailed point 3
```

### Examples

**Good commits:**
```
v5.5: Add scoring history tracking

- Create scoring_history table
- Implement ScoringModel base class
- Add score component breakdown
- Enable A/B testing of scoring algorithms
```
```
v5.4: Fix PostgreSQL connection pool exhaustion

- Increase max_connections in docker-compose.yml
- Add connection cleanup in enrichment modules
- Log connection pool statistics
```

**Bad commits:**
```
fix stuff
update code
changes
wip
```

### Version Tagging
- Use semantic versioning: MAJOR.MINOR.PATCH
- Tag releases in git: `git tag v5.5.0`
- Update `CHANGELOG.md` with every version

---

## 🧪 Testing

### Manual Testing Checklist

Before committing changes:

- [ ] Service restarts without errors
- [ ] Dashboard loads at http://10.55.55.55:8000
- [ ] No errors in logs after 1 minute
- [ ] Affected features work as expected
- [ ] Database queries execute successfully

### Testing Pipeline Changes
```bash
# Test discovery
python3 scripts/run_pipeline.py discover

# Test enrichment
python3 scripts/run_pipeline.py enrich

# Test scoring
python3 scripts/run_pipeline.py score

# Test full pipeline
python3 scripts/run_pipeline.py full
```

### Testing API Changes
```bash
# Health check
curl http://10.55.55.55:8000/api/status

# Test specific endpoint
curl -X GET http://10.55.55.55:8000/api/companies

# Test with authentication (get token from browser)
curl -H "Cookie: access_token=Bearer_YOUR_TOKEN" \
  http://10.55.55.55:8000/dashboard
```

---

## 🔀 Git Workflow

### Standard Workflow
```bash
# 1. Start from clean state
cd /opt/pe-sourcing-engine
git status  # Should be clean

# 2. Make your changes
nano <files>

# 3. Test thoroughly
sudo systemctl restart pe-sourcing-gui.service
# ... verify everything works ...

# 4. Stage changes
git add <files>
# or to stage all:
git add -A

# 5. Commit
git commit -m "v5.5: Your message"

# 6. Push
git push origin main
```

### Viewing History
```bash
# Recent commits
git log --oneline -10

# Changes in a file
git log -p <file>

# Who changed what
git blame <file>
```

### Undoing Changes
```bash
# Discard uncommitted changes
git restore <file>

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes) - CAREFUL!
git reset --hard HEAD~1
```

---

## ⚠️ Important Notes

### DO ✅

- **Always test on dg server first** before deploying to docker-dg
- **Request full file contents** when asking for code help (not snippets)
- **Include file paths** and `nano` commands in documentation
- **Preserve backward compatibility** unless explicitly breaking it
- **Use descriptive variable names** and comments
- **Follow existing code patterns** in the project
- **Update documentation** when changing functionality
- **Commit frequently** with meaningful messages

### DON'T ❌

- **Refactor working code** without explicit request or discussion
- **Introduce new dependencies** without approval
- **Break backward compatibility** without versioning
- **Commit secrets, API keys, or credentials**
- **Make assumptions** about the environment
- **Push directly to production** (docker-dg) without testing on dg
- **Use print() statements** for logging (use proper logger)
- **Hardcode configuration** values (use config files)

---

## 🔐 Security

### Secrets Management
- **Never commit** files in `config/secrets.env`
- **Never commit** API keys or credentials
- **Always use** environment variables for sensitive data
- **Generate strong secrets** with `secrets.token_hex(32)`

### Password Handling
- **Always hash** passwords with bcrypt
- **Never log** passwords or tokens
- **Validate input** from users

---

## 📚 Resources

### Project Documentation
- **README.md** - Project overview and quick start
- **docker-README.md** - Docker deployment guide
- **schema/README.md** - Database schema documentation
- **CHANGELOG.md** - Version history

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Python Style Guide (PEP 8)](https://pep8.org/)

---

## 💡 Getting Help

### Common Issues

**Service won't start:**
```bash
sudo systemctl status pe-sourcing-gui.service
sudo journalctl -u pe-sourcing-gui.service -n 50
```

**Database connection errors:**
```bash
psql -U pe_sourcer -h 10.55.55.55 -d pe_sourcing_db
# Verify config/secrets.env has correct credentials
```

**Import errors:**
```bash
# Verify Python path
python3 -c "import sys; print('\n'.join(sys.path))"
```

### Contact

**Developer:** Gabriel Atkinson  
**Repository:** https://github.com/gpatkins/pe-sourcing-engine (Private)

---

## 📄 License

This is a private project. All rights reserved.

---

**Thank you for contributing to DealGenome!** 🚀
