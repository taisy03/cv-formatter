# Deployment Guide for Hostinger

## Quick Start

### 1. Test Locally First

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py

# Open http://localhost:5000 in your browser
```

### 2. Prepare for Deployment

Ensure all files are uploaded:
- `server.py` (main Flask app)
- `frontend/` directory (HTML, CSS, JS)
- `template/template.docx` (Word template)
- `requirements.txt` (dependencies)

### 3. Hostinger Deployment Options

#### Option A: Hostinger VPS (Recommended)

If you have VPS access:

1. **Upload files via SFTP** to your server
2. **SSH into server** and navigate to project directory
3. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Create systemd service** (`/etc/systemd/system/cv-formatter.service`):
   ```ini
   [Unit]
   Description=CV Formatter Web App
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/path/to/max_formatter
   Environment="PATH=/path/to/max_formatter/venv/bin"
   ExecStart=/path/to/max_formatter/venv/bin/python server.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
5. **Start service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable cv-formatter
   sudo systemctl start cv-formatter
   ```
6. **Configure Nginx** (if not already configured):
   ```nginx
   server {
       listen 80;
       server_name formatter.taise.co.uk;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```

#### Option B: Hostinger Shared Hosting

1. **Upload files** via File Manager or FTP
2. **Use Hostinger's Python App** feature in cPanel:
   - Create new Python app
   - Set Python version (3.8+)
   - Point to `server.py`
   - Install dependencies via their interface
3. **Configure domain**: Point `formatter.taise.co.uk` to the app directory

#### Option C: Using Gunicorn (Production)

For better production performance:

1. **Install Gunicorn**:
   ```bash
   pip install gunicorn
   ```

2. **Update server.py** to remove debug mode:
   ```python
   if __name__ == '__main__':
       app.run(host='0.0.0.0', port=5000, debug=False)
   ```

3. **Run with Gunicorn**:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 server:app
   ```

### 4. Verify Deployment

1. Visit `http://formatter.taise.co.uk`
2. Test with a sample PDF
3. Check server logs for any errors

### 5. Troubleshooting

**Issue: Template not found**
- Verify `template/template.docx` exists
- Check file permissions (should be readable)

**Issue: Dependencies not installed**
- SSH into server
- Run `pip install -r requirements.txt`

**Issue: Port 5000 not accessible**
- Check firewall settings
- Verify Nginx/Apache proxy configuration
- Ensure Flask is binding to `0.0.0.0`, not `127.0.0.1`

**Issue: CORS errors**
- Verify `flask-cors` is installed
- Check browser console for specific errors

## Security Checklist

- [ ] Remove debug mode in production (`debug=False`)
- [ ] Use HTTPS (SSL certificate)
- [ ] Set up rate limiting (optional)
- [ ] Monitor file upload sizes
- [ ] Keep dependencies updated

## Maintenance

- Monitor server logs regularly
- Update dependencies: `pip install -r requirements.txt --upgrade`
- Backup template file
- Check OpenAI API usage/limits

