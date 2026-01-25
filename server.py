from flask import Flask, request, send_file, jsonify, send_from_directory, session, redirect
from flask_cors import CORS
from dotenv import load_dotenv
import pymupdf as fitz  # PyMuPDF
import json
import os
import io
import secrets
import hashlib
import time
from functools import wraps
from collections import defaultdict
from threading import Lock
from openai import OpenAI
from docxtpl import DocxTemplate

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app, supports_credentials=True)

# Secure session configuration
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

# Password configuration - MUST be set via environment variable
# Generate a hash: python -c "import hashlib; print(hashlib.sha256('your_password'.encode()).hexdigest())"
APP_PASSWORD_HASH = os.getenv('APP_PASSWORD_HASH')

# ============================================
# Rate Limiting for Brute Force Protection
# ============================================
# Configuration
MAX_LOGIN_ATTEMPTS = 5  # Max attempts before lockout
LOCKOUT_DURATION = 900  # 15 minutes lockout (in seconds)
FAILED_LOGIN_DELAY = 2  # 2 second delay after failed login

# Track failed login attempts per IP
login_attempts = defaultdict(list)  # IP -> list of timestamps
login_locks = defaultdict(Lock)  # IP -> lock for thread safety

def get_client_ip():
    """Get the client's IP address, accounting for proxies"""
    # Check for forwarded IP (if behind proxy/load balancer)
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr

def is_ip_locked(ip):
    """Check if an IP is currently locked out"""
    with login_locks[ip]:
        current_time = time.time()
        # Remove attempts older than lockout duration
        login_attempts[ip] = [
            t for t in login_attempts[ip] 
            if current_time - t < LOCKOUT_DURATION
        ]
        # Check if too many recent attempts
        return len(login_attempts[ip]) >= MAX_LOGIN_ATTEMPTS

def record_failed_attempt(ip):
    """Record a failed login attempt for an IP"""
    with login_locks[ip]:
        login_attempts[ip].append(time.time())

def clear_failed_attempts(ip):
    """Clear failed attempts after successful login"""
    with login_locks[ip]:
        login_attempts[ip] = []

def get_lockout_remaining(ip):
    """Get remaining lockout time in seconds"""
    with login_locks[ip]:
        if not login_attempts[ip]:
            return 0
        oldest_attempt = min(login_attempts[ip])
        remaining = LOCKOUT_DURATION - (time.time() - oldest_attempt)
        return max(0, int(remaining))

# ============================================
# Authentication Functions
# ============================================

def get_password_hash():
    """Get the password hash from environment variable"""
    if not APP_PASSWORD_HASH:
        raise RuntimeError("APP_PASSWORD_HASH environment variable is not set!")
    return APP_PASSWORD_HASH

def verify_password(password):
    """Securely verify the password using constant-time comparison"""
    provided_hash = hashlib.sha256(password.encode()).hexdigest()
    expected_hash = get_password_hash()
    return secrets.compare_digest(provided_hash, expected_hash)

def login_required(f):
    """Decorator to protect routes that require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

SYSTEM_PROMPT = """
You are a professional resume parser. Your goal is to extract information from a PDF and return a structured JSON object that matches a specific document template.

### EXTRACTION RULES:
1. PERSONAL INFO: Extract 'first_name' and 'last_name'.
2. EDUCATION: Create a list of objects. Split the university name from the degree. Graduation year should be just the year (e.g., 2017). For each education entry, include 'extra_bullets' as a list of strings for honors, activities, awards, or any additional information (can be null or empty list if none).
3. JOB DATES: For every job, split the date range (e.g., 'Jul 2021 – Present') into 'job_start' (Jul 2021) and 'job_end' (Present). If there is only one date, put it in 'job_start' and leave 'job_end' as null.
4. JOB DESCRIPTION: Extract standard responsibilities as a list of strings. CRITICAL: Each bullet point must be preserved as a COMPLETE, SINGLE string in the list. Do NOT split bullet points that contain commas - commas within bullet points are part of the content and should be preserved. For example, "Managed team of 5 analysts, including hiring and training" should be ONE complete string, not split at the comma.
5. TRANSACTIONS: Look for a section often titled 'Select Transaction Experience' or bullet points describing specific deals/dollar amounts. Move these into a 'transactions' list of objects. Each object must have a 'deal_description'.
6. ADDITIONAL: Group all Skills, Software, Certifications, Languages, and Interests into a single list of strings called 'additional_bullets'.

### JSON STRUCTURE:
{
  "first_name": "",
  "last_name": "",
  "education": [
    {
      "university_name": "",
      "university_location": "",
      "degree_name": "",
      "graduation_year": "",
      "extra_bullets": null,
      "relevant_courses": null
    }
  ],
  "jobs": [
    {
      "company_name": "",
      "job_location": "",
      "job_start": "",
      "job_end": "",
      "job_title": "",
      "job_description": ["bullet 1", "bullet 2"],
      "transactions": [
        { "deal_description": "" }
      ]
    }
  ],
  "additional_bullets": ["bullet 1", "bullet 2"]
}

Example output:
{
  "first_name": "Adam",
  "last_name": "Weiss",
  "education": [
    {
      "university_name": "University of California, Berkeley",
      "university_location": "Berkeley, CA",
      "degree_name": "Bachelor of Science in Business Administration",
      "graduation_year": "2017",
      "extra_bullets": ["Magna Cum Laude", "Dean's List"],
      "relevant_courses": null
    }
  ],
  "jobs": [
    {
      "company_name": "Ladder Capital",
      "job_location": "New York, NY",
      "job_start": "Jul 2021",
      "job_end": "Present",
      "job_title": "Director",
      "job_description": ["Sourced $500mm in debt investments", "Managed team of 5 junior associates, including hiring and performance reviews", "Led cross-functional initiatives across sales, operations, and finance"],
      "transactions": [
        { "deal_description": "NYC Office Workout: $50mm senior loan." }
      ]
    }
  ],
  "additional_bullets": ["Proficient in Python & SQL", "Interests: Real Estate Tech"]
}  

### CRITICAL INSTRUCTIONS:
- BULLET POINT PRESERVATION: When extracting bullet points (for job_description, extra_bullets, transactions, or additional_bullets), each bullet point must be kept as a COMPLETE, SINGLE string. Do NOT split bullet points at commas, semicolons, or other punctuation - these are part of the content. Each array element should represent ONE complete bullet point from the source document.
- COMMA HANDLING: Commas within bullet points are part of the content and MUST be preserved. For example, "Led cross-functional team of 10, including engineers and designers" is ONE bullet point, not two separate ones. Only split at actual bullet point markers (•, -, *, etc.) or line breaks that clearly indicate a new bullet point.
- BULLET POINT GROUPING: Keep related bullet points together. If multiple bullet points describe the same job or education entry, include ALL of them in the respective list. Do not omit or truncate bullet points to be concise - preserve the complete information.
- If extra_bullets or relevant_courses are not found, return null (or empty list [] for extra_bullets).
- extra_bullets should be a list of strings (like job_description) - can contain honors, activities, awards, etc. If none exist, use null or empty list [].
- If a job has no transactions, return an empty list [].
- Maintain professional, high-finance terminology.
- do not use ALL CAPS for anything.
- Date should be in the format of 'Jan 2021' or 'Jul 2021' or 'Present' 
"""


def extract_text_from_pdf_bytes(pdf_bytes):
    """Extract text from PDF bytes (in-memory) with improved bullet point preservation"""
    pdf_stream = io.BytesIO(pdf_bytes)
    with fitz.open(stream=pdf_stream, filetype="pdf") as doc:
        pages_text = []
        for page in doc:
            # Use get_text with layout preservation to maintain structure
            text = page.get_text("text", sort=True)
            
            # Post-process to better preserve bullet points
            # Common bullet point markers (including filled circle ●)
            bullet_markers = ['•', '▪', '▫', '◦', '‣', '-', '*', '·', '●']
            
            lines = text.split('\n')
            processed_lines = []
            
            for i, line in enumerate(lines):
                original_line = line
                # Remove zero-width spaces and other invisible characters that might interfere
                line_cleaned = line.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
                line_stripped = line_cleaned.strip()
                
                if not line_stripped:
                    processed_lines.append('')
                    continue
                
                # Check if line starts with a bullet marker (check original for leading whitespace)
                is_bullet = any(line_stripped.startswith(marker) for marker in bullet_markers)
                
                # Also check for indented lines that might be continuation of bullets
                # (common pattern: bullet on first line, continuation on next)
                is_continuation = False
                if i > 0 and processed_lines:
                    prev_line_stripped = processed_lines[-1].strip()
                    # If previous line was a bullet and this line is indented or starts lowercase
                    if any(prev_line_stripped.startswith(marker) for marker in bullet_markers):
                        # Check if this looks like a continuation (starts with lowercase or is indented)
                        # Check original line for indentation before stripping
                        is_indented = original_line.startswith('  ') or original_line.startswith('\t')
                        if line_stripped and (line_stripped[0].islower() or is_indented):
                            is_continuation = True
                
                if is_bullet:
                    # Ensure bullet point is on its own line (use stripped version)
                    processed_lines.append(line_stripped)
                elif is_continuation:
                    # Append continuation to previous bullet point
                    if processed_lines:
                        processed_lines[-1] += " " + line_stripped
                    else:
                        processed_lines.append(line_stripped)
                else:
                    processed_lines.append(line_stripped)
            
            pages_text.append('\n'.join(processed_lines))
        
        return '\n\n'.join(pages_text)


def get_structured_data(api_key, raw_text):
    """Call OpenAI API to get structured JSON data"""
    if not api_key or not api_key.strip():
        raise ValueError("OpenAI API key is required")
    
    client = OpenAI(api_key=api_key.strip())
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw_text}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


def clean_none_values(obj):
    """Recursively replace None values with empty strings for template compatibility"""
    if isinstance(obj, dict):
        return {k: clean_none_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_none_values(item) for item in obj]
    elif obj is None:
        return ''
    else:
        return obj


def create_word_doc_bytes(data, template_path):
    """Create Word document in memory and return as bytes"""
    doc = DocxTemplate(template_path)
    
    # Clean None values to prevent template rendering issues
    cleaned_data = clean_none_values(data)
    
    # Prepare context for template
    context = {
        'first_name': cleaned_data.get('first_name', ''),
        'last_name': cleaned_data.get('last_name', ''),
        'education': cleaned_data.get('education', []),
        'jobs': cleaned_data.get('jobs', []),
        'additional_bullets': cleaned_data.get('additional_bullets', []),
        'data': cleaned_data
    }
    
    doc.render(context)
    
    # Save to bytes buffer
    output_buffer = io.BytesIO()
    doc.save(output_buffer)
    output_buffer.seek(0)
    
    return output_buffer


# Authentication endpoints
@app.route('/api/auth/login', methods=['POST'])
def login():
    """Handle login requests with brute force protection"""
    client_ip = get_client_ip()
    
    # Check if IP is locked out
    if is_ip_locked(client_ip):
        remaining = get_lockout_remaining(client_ip)
        minutes = remaining // 60
        seconds = remaining % 60
        print(f"SECURITY: Blocked login attempt from locked IP: {client_ip}")
        return jsonify({
            'error': f'Too many failed attempts. Try again in {minutes}m {seconds}s',
            'locked': True,
            'remaining_seconds': remaining
        }), 429
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        password = data.get('password', '')
        
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        if verify_password(password):
            # Successful login - clear failed attempts
            clear_failed_attempts(client_ip)
            session.permanent = True
            session['authenticated'] = True
            session['session_token'] = secrets.token_hex(16)
            print(f"SECURITY: Successful login from IP: {client_ip}")
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            # Failed login - record attempt and add delay
            record_failed_attempt(client_ip)
            attempts_left = MAX_LOGIN_ATTEMPTS - len(login_attempts[client_ip])
            print(f"SECURITY: Failed login attempt from IP: {client_ip} ({attempts_left} attempts remaining)")
            
            # Add delay to slow down brute force attacks
            time.sleep(FAILED_LOGIN_DELAY)
            
            if attempts_left <= 0:
                remaining = get_lockout_remaining(client_ip)
                return jsonify({
                    'error': f'Too many failed attempts. Locked for {remaining // 60} minutes.',
                    'locked': True,
                    'remaining_seconds': remaining
                }), 429
            
            return jsonify({
                'error': f'Invalid password. {attempts_left} attempts remaining.',
                'attempts_left': attempts_left
            }), 401
            
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Handle logout requests"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})


@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    if session.get('authenticated'):
        return jsonify({'authenticated': True})
    return jsonify({'authenticated': False}), 401


@app.route('/login')
def login_page():
    """Serve the login page"""
    # If already authenticated, redirect to main app
    if session.get('authenticated'):
        return redirect('/')
    return send_from_directory('frontend', 'login.html')


@app.route('/')
def index():
    """Serve the frontend HTML page - PROTECTED"""
    # Redirect to login if not authenticated
    if not session.get('authenticated'):
        return redirect('/login')
    return send_from_directory('frontend', 'index.html')


@app.route('/api/process', methods=['POST'])
@login_required
def process_resume():
    """Process PDF resume and return formatted Word document"""
    try:
        # Validate request
        if 'pdf_file' not in request.files:
            return jsonify({'error': 'No PDF file provided'}), 400
        
        if 'api_key' not in request.form:
            return jsonify({'error': 'OpenAI API key is required'}), 400
        
        pdf_file = request.files['pdf_file']
        api_key = request.form.get('api_key', '').strip()
        
        # Validate file
        if pdf_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not pdf_file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'File must be a PDF'}), 400
        
        # Read PDF into memory
        pdf_bytes = pdf_file.read()
        
        # Check file size
        if len(pdf_bytes) > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB'}), 400
        
        # Validate PDF can be opened
        try:
            pdf_stream = io.BytesIO(pdf_bytes)
            test_doc = fitz.open(stream=pdf_stream, filetype="pdf")
            test_doc.close()
        except Exception as e:
            return jsonify({'error': f'Invalid PDF file: {str(e)}'}), 400
        
        # Process PDF
        print("Step 1: Extracting text from PDF...")
        text = extract_text_from_pdf_bytes(pdf_bytes)
        
        if not text or len(text.strip()) < 10:
            return jsonify({'error': 'Could not extract text from PDF. Please ensure the PDF contains readable text.'}), 400
        
        print("Step 2: Calling OpenAI API...")
        json_data = get_structured_data(api_key, text)
        
        print("Step 3: Generating Word document...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(script_dir, "template", "template.docx")
        
        if not os.path.exists(template_path):
            return jsonify({'error': 'Template file not found'}), 500
        
        doc_buffer = create_word_doc_bytes(json_data, template_path)
        
        # Generate filename
        first_name = json_data.get('first_name', 'Resume')
        last_name = json_data.get('last_name', '')
        filename = f"{first_name}_{last_name}_Formatted_Resume.docx".replace(' ', '_') if last_name else "Formatted_Resume.docx"
        
        print("Step 4: Returning document...")
        return send_file(
            doc_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=filename
        )
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error processing resume: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Processing error: {str(e)}'}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})


# Serve static files (CSS, JS) - must be last route
@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from frontend directory"""
    # Don't intercept API routes
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
    
    # Serve CSS and JS files (public - needed for login page styling)
    if path in ['style.css', 'app.js', 'login.html']:
        return send_from_directory('frontend', path)
    
    # All other routes require authentication
    if not session.get('authenticated'):
        return redirect('/login')
    
    # Default to index.html for SPA routing
    return send_from_directory('frontend', 'index.html')


if __name__ == '__main__':
    # Get template path to verify it exists
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "template", "template.docx")
    
    if not os.path.exists(template_path):
        print(f"WARNING: Template file not found at {template_path}")
    
    # Print security notice
    if not APP_PASSWORD_HASH:
        print("\n" + "="*60)
        print("ERROR: APP_PASSWORD_HASH environment variable is not set!")
        print("")
        print("To set a password, run:")
        print("  export APP_PASSWORD_HASH=$(python -c \"import hashlib; print(hashlib.sha256('YOUR_PASSWORD'.encode()).hexdigest())\")")
        print("")
        print("Or create a .env file with:")
        print("  APP_PASSWORD_HASH=your_hash_here")
        print("="*60 + "\n")
        exit(1)
    
    # Run Flask app
    # Set debug=False for production
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
