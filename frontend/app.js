// DOM Elements
const form = document.getElementById('resumeForm');
const apiKeyInput = document.getElementById('apiKey');
const pdfFileInput = document.getElementById('pdfFile');
const fileUploadArea = document.getElementById('fileUploadArea');
const fileName = document.getElementById('fileName');
const submitBtn = document.getElementById('submitBtn');
const btnLoader = document.getElementById('btnLoader');
const btnText = submitBtn.querySelector('.btn-text');
const errorMessage = document.getElementById('errorMessage');
const successMessage = document.getElementById('successMessage');
const downloadBtn = document.getElementById('downloadBtn');
const autoDownloadCheckbox = document.getElementById('autoDownload');
const rememberApiKeyCheckbox = document.getElementById('rememberApiKey');
const clearApiKeyBtn = document.getElementById('clearApiKey');
const logoutBtn = document.getElementById('logoutBtn');

// API Key Storage
const API_KEY_STORAGE_KEY = 'cv_formatter_api_key';

// ============================================
// API Key Management
// ============================================

function loadSavedApiKey() {
    try {
        const savedKey = localStorage.getItem(API_KEY_STORAGE_KEY);
        if (savedKey) {
            apiKeyInput.value = savedKey;
            rememberApiKeyCheckbox.checked = true;
            clearApiKeyBtn.style.display = 'inline-block';
        } else {
            clearApiKeyBtn.style.display = 'none';
        }
    } catch (e) {
        console.warn('Could not load saved API key:', e);
        clearApiKeyBtn.style.display = 'none';
    }
}

function saveApiKey(key) {
    try {
        if (rememberApiKeyCheckbox.checked && key && key.length > 0) {
            localStorage.setItem(API_KEY_STORAGE_KEY, key);
            clearApiKeyBtn.style.display = 'inline-block';
        } else {
            localStorage.removeItem(API_KEY_STORAGE_KEY);
            if (!rememberApiKeyCheckbox.checked || !key || key.length === 0) {
                clearApiKeyBtn.style.display = 'none';
            }
        }
    } catch (e) {
        console.warn('Could not save API key:', e);
    }
}

function clearSavedApiKey() {
    try {
        localStorage.removeItem(API_KEY_STORAGE_KEY);
        apiKeyInput.value = '';
        rememberApiKeyCheckbox.checked = false;
        clearApiKeyBtn.style.display = 'none';
    } catch (e) {
        console.warn('Could not clear API key:', e);
    }
}

// ============================================
// Authentication
// ============================================

async function handleLogout() {
    try {
        await fetch('/api/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });
    } catch (error) {
        console.error('Logout error:', error);
    }
    // Redirect to login page
    window.location.href = '/login';
}

// ============================================
// Event Listeners
// ============================================

// Logout button
logoutBtn.addEventListener('click', handleLogout);

// Handle remember checkbox change
rememberApiKeyCheckbox.addEventListener('change', () => {
    if (!rememberApiKeyCheckbox.checked) {
        clearSavedApiKey();
    } else if (apiKeyInput.value.trim()) {
        saveApiKey(apiKeyInput.value.trim());
    }
});

// Handle clear button click
clearApiKeyBtn.addEventListener('click', (e) => {
    e.preventDefault();
    clearSavedApiKey();
});

// Save API key when user types (debounced)
let saveTimeout;
apiKeyInput.addEventListener('input', () => {
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(() => {
        if (rememberApiKeyCheckbox.checked) {
            saveApiKey(apiKeyInput.value.trim());
        }
    }, 500);
});

// File handling
fileUploadArea.addEventListener('click', () => {
    pdfFileInput.click();
});

pdfFileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        fileName.textContent = file.name;
        fileName.style.display = 'block';
        fileUploadArea.classList.add('has-file');
    }
});

// Drag and drop
fileUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileUploadArea.classList.add('dragover');
});

fileUploadArea.addEventListener('dragleave', () => {
    fileUploadArea.classList.remove('dragover');
});

fileUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    fileUploadArea.classList.remove('dragover');
    
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
        pdfFileInput.files = e.dataTransfer.files;
        fileName.textContent = file.name;
        fileName.style.display = 'block';
        fileUploadArea.classList.add('has-file');
    } else {
        showError('Please upload a PDF file');
    }
});

// Form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Hide previous messages
    hideMessages();
    
    // Validate inputs
    const apiKey = apiKeyInput.value.trim();
    const pdfFile = pdfFileInput.files[0];
    
    if (!apiKey) {
        showError('Please enter your OpenAI API key');
        return;
    }
    
    if (!pdfFile) {
        showError('Please select a PDF file');
        return;
    }
    
    // Validate file type
    if (pdfFile.type !== 'application/pdf' && !pdfFile.name.toLowerCase().endsWith('.pdf')) {
        showError('Please upload a valid PDF file');
        return;
    }
    
    // Validate file size (10MB)
    const maxSize = 10 * 1024 * 1024;
    if (pdfFile.size > maxSize) {
        showError('File size exceeds 10MB limit');
        return;
    }
    
    // Show loading state
    setLoadingState(true);
    
    try {
        // Save API key if remember checkbox is checked
        if (rememberApiKeyCheckbox.checked) {
            saveApiKey(apiKey);
        }
        
        // Prepare form data
        const formData = new FormData();
        formData.append('api_key', apiKey);
        formData.append('pdf_file', pdfFile);
        
        // Make API request
        const response = await fetch('/api/process', {
            method: 'POST',
            credentials: 'include',
            body: formData
        });
        
        // Handle authentication errors - redirect to login
        if (response.status === 401) {
            window.location.href = '/login';
            return;
        }
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error occurred' }));
            throw new Error(errorData.error || `Server error: ${response.status}`);
        }
        
        // Get the blob
        const blob = await response.blob();
        
        // Get filename from response headers or use default
        const contentDisposition = response.headers.get('content-disposition');
        let filename = 'formatted_resume.docx';
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        
        // Auto-download or show download button
        if (autoDownloadCheckbox.checked) {
            a.click();
            showSuccess('Resume formatted and downloaded successfully!');
        } else {
            downloadBtn.onclick = () => {
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            };
            downloadBtn.style.display = 'block';
            showSuccess('Resume formatted successfully!');
        }
        
        // Clean up after a delay if auto-downloaded
        if (autoDownloadCheckbox.checked) {
            setTimeout(() => {
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            }, 100);
        }
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'An error occurred while processing your resume');
    } finally {
        setLoadingState(false);
    }
});

// ============================================
// UI Helper Functions
// ============================================

function setLoadingState(loading) {
    if (loading) {
        submitBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'flex';
        fileUploadArea.style.pointerEvents = 'none';
        apiKeyInput.disabled = true;
    } else {
        submitBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
        fileUploadArea.style.pointerEvents = 'auto';
        apiKeyInput.disabled = false;
    }
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    successMessage.style.display = 'none';
    downloadBtn.style.display = 'none';
}

function showSuccess(message) {
    successMessage.querySelector('p').textContent = message;
    successMessage.style.display = 'block';
    errorMessage.style.display = 'none';
}

function hideMessages() {
    errorMessage.style.display = 'none';
    successMessage.style.display = 'none';
    downloadBtn.style.display = 'none';
}

// ============================================
// Initialize
// ============================================

// Load saved API key on page load
loadSavedApiKey();
