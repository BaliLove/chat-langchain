# Prompt Management Workflow

## Overview

Your prompts are now managed through LangSmith with full version control integration. Here's how to use the system:

## 🚀 Quick Start

### 1. Deploy Current Prompts
```bash
# Deploy all prompts to LangSmith
cd backend
python manage_prompts.py push

# Or use the deployment script
python scripts/deploy_prompts.py --env production
```

### 2. Enable LangSmith Prompts in Production
Update your environment variables:
```env
USE_LANGSMITH_PROMPTS=true
LANGSMITH_API_KEY=your-api-key
```

### 3. Edit Prompts in LangSmith UI
- Go to [LangSmith](https://smith.langchain.com)
- Navigate to "Prompts" section
- Edit any of your `bali-love-*` prompts
- Test changes directly in the UI

### 4. Pull Changes Back to Code
```bash
# Pull all prompts from LangSmith
python manage_prompts.py pull

# Compare local vs remote
python manage_prompts.py compare

# Sync local files with LangSmith
python manage_prompts.py sync-local
```

## 📋 Available Commands

### Basic Operations
```bash
# Push all prompts to LangSmith
python manage_prompts.py push

# Pull all prompts from LangSmith
python manage_prompts.py pull

# List prompts in LangSmith
python manage_prompts.py list

# Compare local vs remote
python manage_prompts.py compare
```

### Single Prompt Operations
```bash
# Push single prompt
python manage_prompts.py push-single bali-love-router-prompt

# Pull single prompt
python manage_prompts.py pull-single bali-love-router-prompt
```

### Sync Operations
```bash
# Update local custom_prompts.py with LangSmith versions
python manage_prompts.py sync-local
```

## 🔄 Deployment Workflow

### Development Workflow
1. **Edit prompts locally** in `backend/retrieval_graph/custom_prompts.py`
2. **Test locally** with `USE_LANGSMITH_PROMPTS=false`
3. **Push to LangSmith** with `python manage_prompts.py push`
4. **Test in LangSmith** environment
5. **Deploy to production** by setting `USE_LANGSMITH_PROMPTS=true`

### Production Workflow
1. **Edit in LangSmith UI** for quick iterations
2. **Test immediately** (changes are live)
3. **Pull back to code** with `python manage_prompts.py sync-local`
4. **Commit changes** to git for version control

## 🏷️ Current Prompts

| LangSmith Name | Purpose | Local Variable |
|---|---|---|
| `bali-love-router-prompt` | Route queries to research/general/more-info | `ROUTER_SYSTEM_PROMPT` |
| `bali-love-generate-queries-prompt` | Generate search queries | `GENERATE_QUERIES_SYSTEM_PROMPT` |
| `bali-love-more-info-prompt` | Ask for clarification | `MORE_INFO_SYSTEM_PROMPT` |
| `bali-love-research-plan-prompt` | Create research plans | `RESEARCH_PLAN_SYSTEM_PROMPT` |
| `bali-love-general-prompt` | Handle general conversation | `GENERAL_SYSTEM_PROMPT` |
| `bali-love-response-prompt` | Generate final responses | `RESPONSE_SYSTEM_PROMPT` |

## 🔧 Configuration

### Environment Variables
```env
# Required for LangSmith integration
LANGSMITH_API_KEY=your-api-key
LANGCHAIN_API_KEY=your-api-key  # Same as LANGSMITH_API_KEY
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_PROJECT=your-project-name

# Enable LangSmith prompts (default: false)
USE_LANGSMITH_PROMPTS=true
```

### File Structure
```
backend/
├── manage_prompts.py           # Main prompt management CLI
├── .env                        # Environment variables
└── retrieval_graph/
    ├── prompts.py              # LangSmith prompt loader
    ├── prompts_updated.py      # Updated version (defaults to LangSmith)
    └── custom_prompts.py       # Local fallback prompts

scripts/
└── deploy_prompts.py           # Deployment script with versioning
```

## 🚨 Best Practices

### 1. Always Test Before Production
```bash
# Test locally first
USE_LANGSMITH_PROMPTS=false python your_test_script.py

# Then test with LangSmith
USE_LANGSMITH_PROMPTS=true python your_test_script.py
```

### 2. Version Control Integration
```bash
# After editing prompts in LangSmith UI
python manage_prompts.py sync-local
git add backend/retrieval_graph/custom_prompts.py
git commit -m "Update prompts from LangSmith"
```

### 3. Use Tags for Versions
```bash
# Deploy with custom tags
python scripts/deploy_prompts.py --env production --tag "v2.1.0"
```

### 4. Monitor Prompt Performance
- Use LangSmith's built-in analytics
- Track prompt performance metrics
- A/B test different prompt versions

## 🐛 Troubleshooting

### Common Issues

**1. "API key must be provided"**
```bash
# Check environment variables
echo $LANGSMITH_API_KEY
# Set if missing
export LANGSMITH_API_KEY=your-api-key
```

**2. "Prompt not found in LangSmith"**
```bash
# Push prompts first
python manage_prompts.py push
```

**3. "Failed to load LangSmith prompts"**
- Check network connectivity
- Verify API key is correct
- Ensure LangSmith service is available
- System will fall back to local prompts automatically

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python manage_prompts.py push
```

## 🚀 Advanced Features

### Automated Deployment
Add to your CI/CD pipeline:
```yaml
# .github/workflows/deploy.yml
- name: Deploy Prompts
  run: |
    python scripts/deploy_prompts.py --env production --tag ${{ github.sha }}
  env:
    LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}
```

### Custom Prompt Templates
Extend the system by adding new prompts:
```python
# In manage_prompts.py
self.prompt_mapping["bali-love-new-prompt"] = NEW_PROMPT_TEXT
```

### Team Collaboration
- Use LangSmith's sharing features
- Set up different environments (dev/staging/prod)
- Use git branches for prompt experiments

This system gives you the best of both worlds: the power of LangSmith's prompt management UI with the reliability of version-controlled fallbacks!