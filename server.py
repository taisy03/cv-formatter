from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_cors import CORS
import pymupdf as fitz  # PyMuPDF
import json
import os
import io
from openai import OpenAI
from docxtpl import DocxTemplate

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)  # Enable CORS for all routes

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


@app.route('/')
def index():
    """Serve the frontend HTML page"""
    return send_from_directory('frontend', 'index.html')


@app.route('/api/process', methods=['POST'])
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
    
    # Serve CSS and JS files
    if path in ['style.css', 'app.js']:
        return send_from_directory('frontend', path)
    
    # Default to index.html for SPA routing
    return send_from_directory('frontend', 'index.html')


if __name__ == '__main__':
    # Get template path to verify it exists
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "template", "template.docx")
    
    if not os.path.exists(template_path):
        print(f"WARNING: Template file not found at {template_path}")
    
    # Run Flask app
    # Set debug=False for production
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)

