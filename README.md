# CV Formatter Web App

A web application that transforms PDF resumes into professionally formatted Word documents using OpenAI GPT-4o-mini.

## Features

- 📄 Upload PDF resumes
- 🤖 AI-powered resume parsing and formatting
- 📥 Download formatted Word documents
- 🔒 Secure - API keys never stored server-side
- 💾 In-memory processing - files never saved to disk
- 🎨 Modern, responsive UI

## Local Development

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository:
```bash
cd max_formatter
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
python server.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

## Deployment to Hostinger

### Option 1: Shared Hosting (cPanel)

1. **Upload files** to your subdomain directory (`formatter.taise.co.uk`)

2. **Install Python dependencies**:
   - Use cPanel's Python app installer, or
   - SSH into your account and run: `pip install -r requirements.txt`

3. **Configure Python app**:
   - Point to `server.py` as the entry point
   - Set Python version (3.8+)
   - Configure startup command: `python server.py`

4. **Set environment variables** (if needed):
   - In cPanel, add any required environment variables

### Option 2: VPS Hosting

1. **SSH into your server**

2. **Install dependencies**:
```bash
cd /path/to/max_formatter
pip3 install -r requirements.txt
```

3. **Run with systemd** (create `/etc/systemd/system/cv-formatter.service`):
```ini
[Unit]
Description=CV Formatter Web App
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/max_formatter
ExecStart=/usr/bin/python3 server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

4. **Start the service**:
```bash
sudo systemctl enable cv-formatter
sudo systemctl start cv-formatter
```

5. **Configure Nginx** (reverse proxy):
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

### Option 3: Using Hostinger's Python Hosting

1. Follow Hostinger's Python app deployment guide
2. Upload files via FTP/SFTP
3. Set `server.py` as the entry point
4. Install dependencies via their interface

## Configuration

### Environment Variables (Optional)

The app can run without environment variables since the API key is provided by the user. However, you can set:

- `FLASK_ENV`: Set to `production` for production mode
- `MAX_UPLOAD_SIZE`: Maximum file size in bytes (default: 10MB)

### File Limits

- Maximum PDF size: 10MB
- Supported format: PDF only

## Project Structure

```
max_formatter/
├── server.py              # Flask backend API
├── app.py                 # Original CLI script (kept for reference)
├── frontend/
│   ├── index.html        # Main UI page
│   ├── style.css         # Styling
│   └── app.js            # Frontend JavaScript
├── template/
│   └── template.docx     # Word document template
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## API Endpoints

### `GET /`
Serves the frontend HTML page.

### `POST /api/process`
Processes a PDF resume and returns a formatted Word document.

**Request:**
- `api_key` (form field): OpenAI API key
- `pdf_file` (file): PDF resume file

**Response:**
- Success (200): Word document (.docx) as download
- Error (400/500): JSON error message

### `GET /health`
Health check endpoint.

## Security Notes

- API keys are never stored on the server
- PDF files are processed in memory and never saved to disk
- File uploads are validated (type and size)
- CORS is enabled for cross-origin requests

## Troubleshooting

### Template file not found
Ensure `template/template.docx` exists in the project directory.

### PDF extraction fails
Make sure the PDF contains readable text (not just images). OCR is not supported.

### OpenAI API errors
- Verify your API key is correct
- Check your OpenAI account has sufficient credits
- Ensure the API key has access to GPT-4o-mini

## License

Private project - All rights reserved
