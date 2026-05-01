# Quick Start Guide - Windows Scraper

## Step 1: Install Python

Python is not currently installed on your system. You have two options:

### Option A: Install from Python.org (Recommended)
1. Go to https://www.python.org/downloads/
2. Download Python 3.11 or 3.12 (latest stable version)
3. Run the installer
4. **IMPORTANT**: Check "Add Python to PATH" during installation
5. Restart PowerShell after installation

### Option B: Install from Microsoft Store
1. Open Microsoft Store
2. Search for "Python 3.11" or "Python 3.12"
3. Click Install
4. Restart PowerShell after installation

## Step 2: Verify Python Installation

Open a new PowerShell window and run:
```powershell
python --version
```

You should see something like: `Python 3.11.x` or `Python 3.12.x`

If you see "Python was not found", you need to add Python to your PATH or restart PowerShell.

## Step 3: Install Google Chrome

If you don't have Chrome installed:
1. Go to https://www.google.com/chrome/
2. Download and install Chrome
3. Chrome is required for the scraper to work

## Step 4: Setup Scraper

Once Python is installed, navigate to the scraper directory:
```powershell
cd C:\Users\029878866\EMEA-AI-SQUAD\RAG-with-Notebook\Part3-RAG-Sales-Manual\scraper-test
```

### Manual Setup (if setup script doesn't work)

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements-windows.txt

# Test scraper
python windows_scraper.py
```

You should see usage instructions if everything is working.

## Step 5: Test Scraping

Try scraping the E1180 Sales Manual:

```powershell
python windows_scraper.py "https://www.ibm.com/docs/en/announcements/family-908005-power-e1180-enterprise-server-9080-heu" --output e1180.json
```

This will:
1. Open Chrome in headless mode
2. Load the IBM Docs page
3. Wait for JavaScript to render
4. Extract all content
5. Save to `e1180.json`
6. Show quality score

Expected output:
```
Creating Chrome driver...
Loading URL: https://www.ibm.com/docs/...
Waiting for content to render...
Waiting 10 seconds for JavaScript...

✅ Scraping successful!
   Title: IBM Power E1180 Server
   Sections: 12
   Quality Score: 100%
   Recommendation: Excellent - Ready for RAG processing

✅ Saved to e1180.json
```

## Step 6: Check the Output

Open `e1180.json` in a text editor or VS Code to see the scraped content.

## Common Issues

### "Python was not found"
- Python is not installed or not in PATH
- Install Python from python.org
- Make sure to check "Add Python to PATH" during installation
- Restart PowerShell after installation

### "execution policy" error
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Chrome not found"
- Install Google Chrome from https://www.google.com/chrome/
- The scraper needs Chrome (not Edge or Firefox)

### "pip: command not found"
- Python installation might be incomplete
- Try: `python -m pip install -r requirements-windows.txt`

### Slow scraping or timeout
- Increase wait time: `--wait 20`
- Check your internet connection
- IBM Docs might be slow to load

## Next Steps

Once scraping works:

1. **Get backend URL**:
   ```powershell
   oc get route rag-backend -o jsonpath='{.spec.host}'
   ```

2. **Scrape and send to backend**:
   ```powershell
   python windows_scraper.py "URL" --backend http://BACKEND_URL
   ```

3. **Set up scheduled scraping** (see WINDOWS_SETUP.md for details)

## Need Help?

See the full documentation in `WINDOWS_SETUP.md` for:
- Detailed installation instructions
- Backend integration
- Batch scraping
- Scheduled scraping with Task Scheduler
- Troubleshooting guide