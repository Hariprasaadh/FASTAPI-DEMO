document.addEventListener('DOMContentLoaded', function() {
    // API endpoint (change this to your actual API URL)
    const API_URL = 'http://localhost:8000';

    // DOM elements
    const resumeUpload = document.getElementById('resume-upload');
    const fileName = document.getElementById('file-name');
    const jobLink = document.getElementById('job-link');
    const analyzeBtn = document.getElementById('analyze-btn');
    const loadingSection = document.getElementById('loading');
    const resultsSection = document.getElementById('results');
    const analysisContent = document.getElementById('analysis-content');
    const emailContent = document.getElementById('email-content');
    const copyEmailBtn = document.getElementById('copy-email');
    const downloadEmailBtn = document.getElementById('download-email');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    // State variables
    let pdfFile = null;

    // Event listeners
    resumeUpload.addEventListener('change', handleFileUpload);
    analyzeBtn.addEventListener('click', handleAnalyze);
    copyEmailBtn.addEventListener('click', copyEmailToClipboard);
    downloadEmailBtn.addEventListener('click', downloadEmail);

    // Tab functionality
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked button
            button.classList.add('active');

            // Show corresponding content
            const tabId = button.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });

    // Handle file upload
    function handleFileUpload(event) {
        const file = event.target.files[0];

        if (file) {
            if (file.type !== 'application/pdf') {
                showNotification('Please upload a PDF file', 'error');
                resumeUpload.value = '';
                fileName.textContent = 'No file chosen';
                pdfFile = null;
                return;
            }

            pdfFile = file;
            fileName.textContent = file.name;
        } else {
            fileName.textContent = 'No file chosen';
            pdfFile = null;
        }
    }

    // Handle analyze button click
    async function handleAnalyze() {
        // Validate inputs
        if (!pdfFile) {
            showNotification('Please upload a resume PDF', 'error');
            return;
        }

        const jobLinkValue = jobLink.value.trim();
        if (!jobLinkValue) {
            showNotification('Please enter a job link', 'error');
            return;
        }

        // Valid URL check
        try {
            new URL(jobLinkValue);
        } catch (error) {
            showNotification('Please enter a valid URL', 'error');
            return;
        }

        // Show loading state
        loadingSection.classList.remove('hidden');
        resultsSection.classList.add('hidden');

        try {
            // Create form data
            const formData = new FormData();
            formData.append('resume', pdfFile);
            formData.append('job_link', jobLinkValue);

            // Send request to the API
            const response = await fetch(`${API_URL}/analyze`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error analyzing resume');
            }

            const data = await response.json();

            // Display results
            analysisContent.innerHTML = data.html_content;
            emailContent.textContent = data.email_content;

            // Show results
            loadingSection.classList.add('hidden');
            resultsSection.classList.remove('hidden');

            // Scroll to results
            resultsSection.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            console.error('Error:', error);
            loadingSection.classList.add('hidden');
            showNotification(error.message || 'An error occurred', 'error');
        }
    }

    // Copy email to clipboard
    function copyEmailToClipboard() {
        const emailText = emailContent.textContent;

        if (!emailText) {
            showNotification('No email content to copy', 'error');
            return;
        }

        navigator.clipboard.writeText(emailText)
            .then(() => {
                showNotification('Email copied to clipboard!', 'success');
            })
            .catch(err => {
                console.error('Could not copy text: ', err);
                showNotification('Failed to copy email', 'error');
            });
    }

    // Download email as text file
    function downloadEmail() {
        const emailText = emailContent.textContent;

        if (!emailText) {
            showNotification('No email content to download', 'error');
            return;
        }

        const blob = new Blob([emailText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');

        a.href = url;
        a.download = 'job_application_email.txt';
        document.body.appendChild(a);
        a.click();

        // Cleanup
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 100);

        showNotification('Email downloaded successfully', 'success');
    }

    // Show notification toast
    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
                <span>${message}</span>
            </div>
        `;

        // Add notification to the DOM
        document.body.appendChild(notification);

        // Trigger animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    // Add notification styles dynamically
    const notificationStyles = `
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            color: #333;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            z-index: 1000;
            opacity: 0;
            transform: translateY(-20px);
            transition: all 0.3s ease;
            max-width: 300px;
        }

        .notification.show {
            opacity: 1;
            transform: translateY(0);
        }

        .notification-content {
            display: flex;
            align-items: center;
        }

        .notification i {
            margin-right: 10px;
            font-size: 1.2rem;
        }

        .notification.success {
            background: linear-gradient(to right, #00b09b, #96c93d);
            color: white;
        }

        .notification.error {
            background: linear-gradient(to right, #ff5f6d, #ffc371);
            color: white;
        }
    `;

    const styleElement = document.createElement('style');
    styleElement.textContent = notificationStyles;
    document.head.appendChild(styleElement);
});