document.addEventListener('DOMContentLoaded', function() {
    // For the ingesting.html page
    const ingestingPage = document.getElementById('ingesting-page');
    if (ingestingPage) {
        const jobId = ingestingPage.dataset.jobId;
        const assignmentUnits = parseInt(ingestingPage.dataset.assignmentUnits, 10) || 5;
        const markSchemeUnits = parseInt(ingestingPage.dataset.markSchemeUnits, 10) || 5;

        const assProgressBarFill = document.getElementById('assignment-progress-fill');
        const msProgressBarFill = document.getElementById('mark-scheme-progress-fill');
        const overallStatusElem = document.getElementById('overall-status');
        const assStatusElem = document.getElementById('assignment-ingestion-status');
        const msStatusElem = document.getElementById('mark-scheme-ingestion-status');
        const matchStatusElem = document.getElementById('matching-status');

        const totalTimeEstimateAss = Math.max(1000, assignmentUnits * 500); // Min 1s, 0.5s per unit
        const totalTimeEstimateMs = Math.max(1000, markSchemeUnits * 500);  // Min 1s, 0.5s per unit

        let assProgress = 0;
        let msProgress = 0;
        let assInterval, msInterval;

        function updateFakeProgress(barFill, currentProgress, totalTime, processStatus) {
            // Only advance fake progress if the actual process is 'processing' or 'pending'
            if (processStatus === 'processing' || processStatus === 'pending' || processStatus === 'queued' || processStatus === 'starting') {
                if (currentProgress < 95) { // Stop fake progress at 95% to wait for actual completion
                    const increment = 100 / (totalTime / 100); // Increment per 100ms
                    currentProgress = Math.min(95, currentProgress + increment);
                }
            } else if (processStatus === 'completed') {
                currentProgress = 100;
            }
            // If error, progress might stop or be reset, handled by actual status update

            if (barFill) {
                barFill.style.width = currentProgress + '%';
                barFill.textContent = Math.round(currentProgress) + '%';
            }
            return currentProgress;
        }

        if (assProgressBarFill) {
            assInterval = setInterval(() => {
                // Get current actual status to decide if fake progress should continue
                const currentAssStatus = job_statuses[jobId]?.assignment_status || 'pending';
                assProgress = updateFakeProgress(assProgressBarFill, assProgress, totalTimeEstimateAss, currentAssStatus);
                if (assProgress >= 95 && currentAssStatus !== 'completed') {
                    // Paused fake progress, waiting for actual completion signal
                } else if (currentAssStatus === 'completed' || currentAssStatus.startsWith('error')) {
                     if (currentAssStatus === 'completed') assProgressBarFill.style.width = '100%';
                    clearInterval(assInterval);
                }
            }, 100);
        }
        if (msProgressBarFill) {
            msInterval = setInterval(() => {
                const currentMsStatus = job_statuses[jobId]?.mark_scheme_status || 'pending';
                msProgress = updateFakeProgress(msProgressBarFill, msProgress, totalTimeEstimateMs, currentMsStatus);
                 if (msProgress >= 95 && currentMsStatus !== 'completed') {
                    // Paused
                } else if (currentMsStatus === 'completed' || currentMsStatus.startsWith('error')) {
                    if (currentMsStatus === 'completed') msProgressBarFill.style.width = '100%';
                    clearInterval(msInterval);
                }
            }, 100);
        }

        // Polling for actual status
        const statusInterval = setInterval(() => {
            fetch(`/status/${jobId}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    // Update global job_statuses for fake progress logic
                    window.job_statuses = window.job_statuses || {};
                    window.job_statuses[jobId] = data;

                    if(assStatusElem) assStatusElem.textContent = `Status: ${data.assignment_status || 'pending'}`;
                    if(msStatusElem) msStatusElem.textContent = `Status: ${data.mark_scheme_status || 'pending'}`;
                    if(matchStatusElem) matchStatusElem.textContent = `Status: ${data.matching_status || 'pending'}`;

                    if (data.assignment_status === 'completed' && assProgressBarFill) {
                        clearInterval(assInterval); // Ensure interval is cleared
                        assProgressBarFill.style.width = '100%';
                        assProgressBarFill.textContent = '100%';
                    } else if (data.assignment_status?.startsWith('error') && assProgressBarFill) {
                        clearInterval(assInterval);
                        assProgressBarFill.style.backgroundColor = '#dc3545'; // Error color
                    }

                    if (data.mark_scheme_status === 'completed' && msProgressBarFill) {
                        clearInterval(msInterval); // Ensure interval is cleared
                        msProgressBarFill.style.width = '100%';
                        msProgressBarFill.textContent = '100%';
                    } else if (data.mark_scheme_status?.startsWith('error') && msProgressBarFill) {
                        clearInterval(msInterval);
                        msProgressBarFill.style.backgroundColor = '#dc3545'; // Error color
                    }

                    if (data.status === 'completed') {
                        clearInterval(statusInterval);
                        if (overallStatusElem) {
                            overallStatusElem.textContent = 'All processes completed! Redirecting...';
                            overallStatusElem.className = 'status-message completed';
                        }
                        // Add a small delay before redirecting to allow user to see message
                        setTimeout(() => {
                            window.location.href = `/assessment/${jobId}`;
                        }, 1500);
                    } else if (data.status === 'error' ||
                               data.assignment_status?.startsWith('error') ||
                               data.mark_scheme_status?.startsWith('error') ||
                               data.matching_status?.startsWith('error')) {
                        clearInterval(statusInterval);
                        if (overallStatusElem) {
                            overallStatusElem.textContent = 'An error occurred during processing. Please check server logs or try again.';
                            overallStatusElem.className = 'status-message error';
                        }
                    } else if (overallStatusElem) {
                        overallStatusElem.textContent = 'Processing... Please wait.';
                        overallStatusElem.className = 'status-message'; // Default class
                    }
                })
                .catch(error => {
                    console.error('Error fetching status:', error);
                    if (overallStatusElem) {
                        overallStatusElem.textContent = 'Error connecting to server for status updates.';
                        overallStatusElem.className = 'status-message error';
                    }
                    // clearInterval(statusInterval); // Optional: stop polling on fetch error
                });
        }, 2000); // Poll every 2 seconds
    }

    // PDF / Image choice on upload form (index.html)
    const assPdfRadio = document.getElementById('assignment_type_pdf');
    const assImagesRadio = document.getElementById('assignment_type_images');
    const assPdfUploadDiv = document.getElementById('assignment_pdf_upload');
    const assImagesUploadDiv = document.getElementById('assignment_images_upload');
    const assPdfInput = document.getElementById('assignment_pdf');
    const assImagesInput = document.getElementById('assignment_images');

    const msPdfRadio = document.getElementById('mark_scheme_type_pdf');
    const msImagesRadio = document.getElementById('mark_scheme_type_images');
    const msPdfUploadDiv = document.getElementById('mark_scheme_pdf_upload');
    const msImagesUploadDiv = document.getElementById('mark_scheme_images_upload');
    const msPdfInput = document.getElementById('mark_scheme_pdf');
    const msImagesInput = document.getElementById('mark_scheme_images');

    function toggleUploadFields(pdfRadio, imagesRadio, pdfUploadDiv, imagesUploadDiv, pdfInput, imagesInput) {
        if (!pdfRadio || !imagesRadio || !pdfUploadDiv || !imagesUploadDiv || !pdfInput || !imagesInput) return;

        function updateVisibility() {
            const isPdfChecked = pdfRadio.checked;
            pdfUploadDiv.style.display = isPdfChecked ? 'block' : 'none';
            pdfInput.required = isPdfChecked;

            imagesUploadDiv.style.display = imagesRadio.checked ? 'block' : 'none';
            imagesInput.required = imagesRadio.checked;

            // Clear the other input type to avoid accidental submission of both
            if (isPdfChecked) {
                imagesInput.value = ''; // Clear file selection for images
            } else {
                pdfInput.value = ''; // Clear file selection for PDF
            }
        }
        pdfRadio.addEventListener('change', updateVisibility);
        imagesRadio.addEventListener('change', updateVisibility);
        updateVisibility(); // Initial call to set correct state
    }

    toggleUploadFields(assPdfRadio, assImagesRadio, assPdfUploadDiv, assImagesUploadDiv, assPdfInput, assImagesInput);
    toggleUploadFields(msPdfRadio, msImagesRadio, msPdfUploadDiv, msImagesUploadDiv, msPdfInput, msImagesInput);
});
