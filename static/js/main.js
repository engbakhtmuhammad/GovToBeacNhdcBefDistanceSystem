// ============================================
// Index Page - File Upload Handler
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const govFileInput = document.getElementById('govFile');
    const specialFileInput = document.getElementById('specialFile');
    const govFileName = document.getElementById('govFileName');
    const specialFileName = document.getElementById('specialFileName');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resetBtn = document.getElementById('resetBtn');
    const progressSection = document.getElementById('progressSection');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');

    // File input change handlers
    govFileInput.addEventListener('change', function(e) {
        if (this.files.length > 0) {
            govFileName.textContent = `✓ ${this.files[0].name}`;
            govFileName.classList.add('active');
        }
    });

    specialFileInput.addEventListener('change', function(e) {
        if (this.files.length > 0) {
            specialFileName.textContent = `✓ ${this.files[0].name}`;
            specialFileName.classList.add('active');
        }
    });

    // Form submission
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Validate files
        if (!govFileInput.files.length || !specialFileInput.files.length) {
            showError('Please select both files before analyzing.');
            return;
        }

        // Hide error if shown
        hideError();

        // Show progress
        progressSection.style.display = 'block';
        progressBar.style.width = '30%';
        progressText.textContent = 'Uploading files...';
        
        // Disable button
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<span class="loading"></span> Processing...';

        try {
            const formData = new FormData();
            formData.append('gov_file', govFileInput.files[0]);
            formData.append('special_file', specialFileInput.files[0]);

            progressBar.style.width = '60%';
            progressText.textContent = 'Starting analysis...';

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'An error occurred during analysis');
            }

            progressBar.style.width = '100%';
            progressText.textContent = 'Redirecting to results...';

            // Navigate immediately to results page with session_id
            setTimeout(() => {
                window.location.href = `/results/${data.session_id}`;
            }, 500);

        } catch (error) {
            console.error('Error:', error);
            showError(error.message || 'An error occurred. Please try again.');
            progressSection.style.display = 'none';
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<i class="fas fa-chart-line"></i> Analyze Distances';
        }
    });

    // Reset button
    resetBtn.addEventListener('click', function() {
        govFileName.textContent = '';
        govFileName.classList.remove('active');
        specialFileName.textContent = '';
        specialFileName.classList.remove('active');
        hideError();
        progressSection.style.display = 'none';
        progressBar.style.width = '0%';
    });

    // Error handling functions
    function showError(message) {
        errorText.textContent = message;
        errorMessage.style.display = 'flex';
        errorMessage.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function hideError() {
        errorMessage.style.display = 'none';
    }

    // Drag and drop support
    const fileLabels = document.querySelectorAll('.file-label');
    
    fileLabels.forEach(label => {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            label.addEventListener(eventName, preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            label.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            label.addEventListener(eventName, unhighlight, false);
        });

        label.addEventListener('drop', handleDrop, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        this.style.borderColor = '#2563eb';
        this.style.background = '#eff6ff';
    }

    function unhighlight(e) {
        this.style.borderColor = '#e2e8f0';
        this.style.background = '#f8fafc';
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        // Find the corresponding input
        const inputId = this.getAttribute('for');
        const input = document.getElementById(inputId);
        
        if (input && files.length > 0) {
            input.files = files;
            // Trigger change event
            const event = new Event('change', { bubbles: true });
            input.dispatchEvent(event);
        }
    }
});
