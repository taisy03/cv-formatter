# Step-by-Step Deployment Guide

## Prerequisites
- Hostinger account with subdomain `formatter.taise.co.uk` configured
- Access to cPanel or SSH (depending on your Hostinger plan)

## Step 1: Test Locally (IMPORTANT!)

Before deploying, make sure it works locally:

```bash
cd /Users/taise/code/PERSONAL/max_formatter
pip install -r requirements.txt
python server.py
```

Then visit `http://localhost:5000` and test with a PDF. If it works, proceed!

## Step 2: Prepare Files for Upload

All these files need to be uploaded:
- ✅ `server.py`
- ✅ `requirements.txt`
- ✅ `frontend/` folder (with index.html, style.css, app.js)
- ✅ `template/` folder (with template.docx)
- ✅ `.gitignore` (optional)

## Step 3: Choose Your Deployment Method

### Method A: Hostinger Shared Hosting (cPanel)

**If you have shared hosting with cPanel:**

1. **Log into Hostinger cPanel**

2. **Upload files via File Manager:**
   - Navigate to your subdomain directory (usually `public_html/formatter` or similar)
   - Upload all files maintaining the folder structure:
     ```
     formatter/
     ├── server.py
     ├── requirements.txt
     ├── frontend/
     │   ├── index.html
     │   ├── style.css
     │   └── app.js
     └── template/
         └── template.docx
     ```

3. **Set up Python App in cPanel:**
   - Look for "Python App" or "Python Selector" in cPanel
   - Create a new Python application
   - Set Python version to 3.8 or higher
   - Set application root to your subdomain directory
   - Set application URL to `/` or your subdomain path
   - Set application startup file to `server.py`
   - Set application entry point to `server:app`

4. **Install dependencies:**
   - In the Python App interface, there should be an option to install from `requirements.txt`
   - Or use SSH/terminal if available:
     ```bash
     pip install -r requirements.txt
     ```

5. **Start the application:**
   - Click "Start" or "Restart" in the Python App interface

6. **Test:**
   - Visit `http://formatter.taise.co.uk`
   - You should see the upload form!

### Method B: Hostinger VPS (SSH Access)

**If you have VPS with SSH access:**

1. **Connect via SSH:**
   ```bash
   ssh your_username@your_server_ip
   ```

2. **Upload files (choose one method):**

   **Option 1: Using SFTP (FileZilla, Cyberduck, etc.)**
   - Connect via SFTP
   - Upload all files to `/home/your_username/formatter/` or similar

   **Option 2: Using Git (if you have a repo)**
   ```bash
   git clone your_repo_url
   ```

   **Option 3: Using SCP from your local machine:**
   ```bash
   scp -r /Users/taise/code/PERSONAL/max_formatter/* user@server:/path/to/formatter/
   ```

3. **SSH into server and navigate:**
   ```bash
   cd /path/to/formatter
   ```

4. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

5. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

6. **Test run:**
   ```bash
   python server.py
   ```
   (Press Ctrl+C to stop)

7. **Set up as a service (systemd):**

   Create service file:
   ```bash
   sudo nano /etc/systemd/system/cv-formatter.service
   ```

   Add this content (adjust paths):
   ```ini
   [Unit]
   Description=CV Formatter Web App
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/path/to/formatter
   Environment="PATH=/path/to/formatter/venv/bin"
   ExecStart=/path/to/formatter/venv/bin/python server.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable cv-formatter
   sudo systemctl start cv-formatter
   ```

   Check status:
   ```bash
   sudo systemctl status cv-formatter
   ```

8. **Configure Nginx (if needed):**

   Create config file:
   ```bash
   sudo nano /etc/nginx/sites-available/formatter.taise.co.uk
   ```

   Add:
   ```nginx
   server {
       listen 80;
       server_name formatter.taise.co.uk;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

   Enable site:
   ```bash
   sudo ln -s /etc/nginx/sites-available/formatter.taise.co.uk /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

9. **Set up SSL (HTTPS):**
   ```bash
   sudo certbot --nginx -d formatter.taise.co.uk
   ```

## Step 4: Verify Deployment

1. Visit `http://formatter.taise.co.uk` (or `https://` if SSL is set up)
2. You should see the upload form
3. Test with a sample PDF resume
4. Check that the formatted document downloads correctly

## Step 5: Troubleshooting

### Can't access the site?
- Check if the app is running: `sudo systemctl status cv-formatter`
- Check firewall: `sudo ufw status`
- Check logs: `sudo journalctl -u cv-formatter -f`

### Template not found error?
- Verify `template/template.docx` exists
- Check file permissions: `chmod 644 template/template.docx`

### Dependencies not installing?
- Make sure you're using Python 3.8+: `python3 --version`
- Try: `pip3 install -r requirements.txt --user`

### Port 5000 already in use?
- Change port in `server.py` to something else (e.g., 5001)
- Update Nginx config if using reverse proxy

## Quick Checklist

- [ ] Tested locally
- [ ] All files uploaded to server
- [ ] Dependencies installed
- [ ] App is running
- [ ] Domain/subdomain configured
- [ ] SSL certificate installed (recommended)
- [ ] Tested with a real PDF

## Need Help?

Check the main `DEPLOYMENT.md` file for more detailed troubleshooting.

