// Global variable to store current member data for editing
let currentMemberData = null;
const { currentUserRole, currentUserName, currentMember } = window.APP_CONFIG;

// --- Helper function for cache busting ---
function addCacheBuster(url) {
    if (!url) return '';
    const timestamp = new Date().getTime();
    // Check if URL already has query parameters
    if (url.includes('?')) {
        return `${url}&_=${timestamp}`;
    } else {
        return `${url}?_=${timestamp}`;
    }
}

// Status options for showFlashMessage: 'success', 'danger', 'warning', 'info', 'primary', 'secondary'
function showFlashMessage(message, status = 'danger') {
    const flashesContainer = document.querySelector('.flashes');
    if (!flashesContainer) return;

    const alert = document.createElement('div');
    alert.className = `alert alert-${status} alert-dismissible fade show`;
    alert.setAttribute('role', 'alert');
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    flashesContainer.appendChild(alert);

    setTimeout(() => {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        if (bsAlert) {
            bsAlert.close();
        }
    }, 5000);
}

function autoCloseFlashes() {
    const alerts = document.querySelectorAll('.flashes .alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });
}



const openCameraBtn = document.getElementById('openCameraBtn');
if (openCameraBtn) {
    openCameraBtn.addEventListener('click', async () => {
        const overlay = document.getElementById('cameraOverlay');
        const video = document.getElementById('cameraVideo');

        try {
            cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } });
            video.srcObject = cameraStream;
            overlay.classList.remove('d-none');
        } catch (err) {
            console.error("Error accessing camera:", err);
            showFlashMessage("Could not access camera. Please ensure permissions are granted.", "warning");
        }
    });
}

const closeCameraBtn = document.getElementById('closeCameraBtn');
if (closeCameraBtn) {
    closeCameraBtn.addEventListener('click', () => {
        closeCamera();
    });
}

const captureBtn = document.getElementById('captureBtn');
if (captureBtn) {
    captureBtn.addEventListener('click', () => {
        const video = document.getElementById('cameraVideo');
        const canvas = document.getElementById('cameraCanvas');

        // Match canvas dimensions to video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        // Draw video frame to canvas
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Get image data as base64
        const imageData = canvas.toDataURL('image/jpeg');

        // Store in hidden input and show preview
        document.getElementById('capturedPhotoData').value = imageData;
        const preview = document.getElementById('photoPreview');
        preview.src = imageData;
        preview.style.display = 'block';

        // Clear file input if a photo is captured
        document.getElementById('photo').value = '';

        closeCamera();
    });
}

// Also preview if a file is chosen via the normal file input
const photoInput = document.getElementById('photo');
if (photoInput) {
    photoInput.addEventListener('change', function(e) {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            const maxSize = 1 * 1024 * 1024; // 1 MB

            if (file.size > maxSize) {
                showFlashMessage('The selected file is too large. Please choose a file smaller than 1 MB.', 'warning');
                e.target.value = ''; // Clear the file input
                const preview = document.getElementById('photoPreview');
                preview.src = '';
                preview.style.display = 'none';
                return;
            }

            const reader = new FileReader();
            reader.onload = function(evt) {
                const preview = document.getElementById('photoPreview');
                preview.src = evt.target.result;
                preview.style.display = 'block';
                // Clear captured data if a file is selected
                document.getElementById('capturedPhotoData').value = '';
            };
            reader.readAsDataURL(file);
        }
    });
}

function closeCamera() {
    const overlay = document.getElementById('cameraOverlay');
    overlay.classList.add('d-none');

    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
}
// --- End camera logic ---

function closeOffcanvas() {
    const offcanvasEl = document.getElementById('mobileSidebar');
    if (offcanvasEl) {
        const offcanvas = bootstrap.Offcanvas.getInstance(offcanvasEl);
        if (offcanvas) {
            offcanvas.hide();
        }
    }
}

function calculateDatePlusMonths(startDateStr, monthsStr) {
    if (!startDateStr || !monthsStr) return '';
    const date = new Date(startDateStr);
    if (isNaN(date.getTime())) return '';

    const months = parseInt(monthsStr.split(' ')[0]);
    if (isNaN(months)) return '';

    date.setMonth(date.getMonth() + months);
    return date.toISOString().split('T')[0];
}

function calculateRenewEndDate() {
    const startDate = document.getElementById('renewSubscriptionStartDate').value;
    const plan = document.getElementById('renewSubscriptionPlan').value;
    const endDateField = document.getElementById('renewSubscriptionEndDate');

    if (startDate && plan) {
        const newEnd = calculateDatePlusMonths(startDate, plan);
        if (newEnd) {
            endDateField.value = newEnd;
        }
    }
}

function showSection(sectionId, event) {
    if (event) event.preventDefault();

    // If navigating away from register, clear it (unless editing)
    const mobileNumField = document.getElementById('mobile_number');
    if (sectionId !== 'register' && mobileNumField && mobileNumField.hasAttribute('readonly')) {
        resetForm();
    }

    // Hide all sections
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => {
        section.classList.remove('active');
    });

    // Remove active class from all buttons
    const buttons = document.querySelectorAll('.sidebar-btn');
    buttons.forEach(btn => {
        btn.classList.remove('active');
    });

    // Show the selected section
    document.getElementById(sectionId).classList.add('active');

    // Add active class to corresponding buttons (both desktop and mobile menus)
    document.querySelectorAll(`.sidebar-btn[onclick*="showSection('${sectionId}'"]`).forEach(b => b.classList.add('active'));

    // Set joining date to today if we are opening the register section and not editing
    if (sectionId === 'register' && mobileNumField && !mobileNumField.hasAttribute('readonly')) {
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('joining_date').value = today;
    }
}

function filterMembers(status) {
    // Switch to the members section
    showSection('members');

    // Update the radio button selection
    if (status === 'active') {
        document.getElementById('filterActive').checked = true;
    } else if (status === 'expired') {
        document.getElementById('filterExpired').checked = true;
    } else {
        document.getElementById('filterAll').checked = true;
    }

    // Apply the filter
    applyMemberFilter();
}

function applyMemberFilter() {
    const mobileSearchInput = document.getElementById('mobileSearch');
    if (!mobileSearchInput) return; // members filter not shown to members
    const textFilter = mobileSearchInput.value.toUpperCase();

    let statusFilter = '';
    if (document.getElementById('filterActive') && document.getElementById('filterActive').checked) {
        statusFilter = 'active';
    } else if (document.getElementById('filterExpired') && document.getElementById('filterExpired').checked) {
        statusFilter = 'expired';
    }

    const table = document.getElementById('membersTable');
    const tr = table.getElementsByTagName('tr');

    for (let i = 1; i < tr.length; i++) {
        const mobileTd = tr[i].getElementsByTagName('td')[1];
        const statusTd = tr[i].querySelector('.status-cell');

        if (mobileTd && statusTd) {
            const mobileValue = mobileTd.textContent || mobileTd.innerText;
            const statusValue = statusTd.getAttribute('data-status') || '';

            const matchesText = mobileValue.toUpperCase().indexOf(textFilter) > -1;
            const matchesStatus = (statusFilter === '') || (statusFilter === statusValue);

            if (matchesText && matchesStatus) {
                tr[i].style.display = "";
            } else {
                tr[i].style.display = "none";
            }
        }
    }
}

function searchByMobile() {
    applyMemberFilter();
}

function filterTransactions() {
    const searchInput = document.getElementById('transactionSearch');
    const textFilter = searchInput ? searchInput.value.toUpperCase() : '';
    const fromDateStr = document.getElementById('transactionFromDate').value;
    const toDateStr = document.getElementById('transactionToDate').value;

    let fromDate = null;
    let toDate = null;

    if (fromDateStr) fromDate = new Date(fromDateStr);
    if (toDateStr) toDate = new Date(toDateStr);

    const table = document.getElementById('transactionsTable');
    const tr = table.getElementsByTagName('tr');

    for (let i = 1; i < tr.length; i++) {
        const mobileTd = tr[i].querySelector('.txn-mobile-cell');
        const dateTd = tr[i].querySelector('.txn-date-cell');

        if (mobileTd && dateTd) {
            const mobileValue = mobileTd.textContent || mobileTd.innerText;
            const dateValueStr = dateTd.textContent || dateTd.innerText;

            const matchesText = currentUserRole === 'admin' ? mobileValue.toUpperCase().indexOf(textFilter) > -1 : true;
            let matchesDate = true;

            if (fromDate || toDate) {
                const txnDate = new Date(dateValueStr);
                if (!isNaN(txnDate.getTime())) {
                    if (fromDate && txnDate < fromDate) {
                        matchesDate = false;
                    }
                    if (toDate && txnDate > toDate) {
                        matchesDate = false;
                    }
                }
            }

            if (matchesText && matchesDate) {
                tr[i].style.display = "";
            } else {
                tr[i].style.display = "none";
            }
        }
    }
}

function searchTransactionsByMobile() {
    filterTransactions();
}

function clearTransactionFilters() {
    const searchInput = document.getElementById('transactionSearch');
    if (searchInput) searchInput.value = '';
    document.getElementById('transactionFromDate').value = '';
    document.getElementById('transactionToDate').value = '';
    filterTransactions();
}

function showLoading() {
    document.getElementById('loadingOverlay').classList.remove('d-none');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('d-none');
}

function populateMemberView(data) {
    currentMemberData = data; // Save for editing

    // Populate data in the view section
    document.getElementById('viewFirstName').innerText = data.first_name || 'N/A';
    document.getElementById('viewLastName').innerText = data.last_name || 'N/A';
    document.getElementById('viewMobileNumber').innerText = data.mobile_number || 'N/A';
    document.getElementById('viewEmail').innerText = data.email || 'N/A';
    document.getElementById('viewGender').innerText = data.gender || 'N/A';
    document.getElementById('viewAddress').innerText = data.address || 'N/A';
    document.getElementById('viewDob').innerText = data.dob || 'N/A';
    document.getElementById('viewJoiningDate').innerText = data.joining_date || 'N/A';
    document.getElementById('viewSubscription').innerText = data.subscription || 'N/A';
    document.getElementById('viewSubscriptionStart').innerText = data.subscription_start_date || 'N/A';
    document.getElementById('viewSubscriptionEnd').innerText = data.subscription_end_date || 'N/A';

    const badgeEl = document.getElementById('viewStatusBadge');
    badgeEl.className = 'badge';
    if (data.status === 'active') {
        badgeEl.innerText = 'Active';
        badgeEl.classList.add('bg-success');
    } else {
        badgeEl.innerText = data.status || 'Unknown';
        badgeEl.classList.add('bg-secondary');
    }

    document.getElementById('vitalHeight').value = data.height || '';
    document.getElementById('vitalWeight').value = data.weight || '';
    document.getElementById('vitalBmi').value = data.bmi || '';

    // Populate Renew Subscription form defaults
    if (document.getElementById('renewSubscriptionPlan')) {
        document.getElementById('renewSubscriptionPlan').value = data.subscription || '1 Month';
    }

    // Set default renew start date to today, or the end date if it's in the future
    if (document.getElementById('renewSubscriptionStartDate')) {
        let defaultRenewDate = new Date().toISOString().split('T')[0];
        if (data.subscription_end_date) {
            const endDate = new Date(data.subscription_end_date);
            if (endDate > new Date()) {
                defaultRenewDate = data.subscription_end_date;
            }
        }
        document.getElementById('renewSubscriptionStartDate').value = defaultRenewDate;
        calculateRenewEndDate();

        // clear out the amount field for a fresh renewal
        document.getElementById('renewAmount').value = '';
        document.getElementById('renewDiscount').value = '';
        document.getElementById('renewPaymentMethod').value = 'Credit Card';
    }

    // Handle Photo display
    const photoEl = document.getElementById('viewPhoto');
    const noPhotoEl = document.getElementById('noPhoto');
    if (data.photo) {
        photoEl.src = addCacheBuster(data.photo); // Apply cache busting
        photoEl.classList.remove('d-none');
        noPhotoEl.classList.add('d-none');
    } else {
        photoEl.classList.add('d-none');
        noPhotoEl.classList.remove('d-none');
    }

    // Setup Edit Button
    const editBtn = document.getElementById('editMemberBtn');
    if (editBtn) {
        editBtn.onclick = () => editMember();
    }
}

async function viewMember(mobileNumber) {
    if (currentMember && currentMember.mobile_number === mobileNumber) {
        populateMemberView(currentMember);
        showSection('viewMemberDetails');
        return;
    }
    showLoading();
    try {
        const response = await fetch(`/api/member/${mobileNumber}`);
        if (!response.ok) {
            showFlashMessage('Member not found', 'danger');
            return;
        }
        const data = await response.json();
        populateMemberView(data);
        showSection('viewMemberDetails');
    } catch (error) {
        console.error('Error fetching member details:', error);
        showFlashMessage('Error loading member details.', 'danger');
    } finally {
        hideLoading();
    }
}

function calculateBMI() {
    const height = parseFloat(document.getElementById('vitalHeight').value);
    const weight = parseFloat(document.getElementById('vitalWeight').value);
    if (height && weight && height > 0) {
        // BMI = weight(kg) / (height(m) * height(m))
        const heightInMeters = height / 100;
        const bmi = weight / (heightInMeters * heightInMeters);
        document.getElementById('vitalBmi').value = bmi.toFixed(2);
    } else {
        document.getElementById('vitalBmi').value = '';
    }
}

async function updateVitals(event) {
    event.preventDefault();
    if (!currentMemberData) return;

    const height = document.getElementById('vitalHeight').value;
    const weight = document.getElementById('vitalWeight').value;
    const bmi = document.getElementById('vitalBmi').value;
    const mobileNumber = currentMemberData.mobile_number;

    showLoading();
    try {
        const formData = new FormData();
        formData.append('mobile_number', mobileNumber);
        formData.append('height', height);
        formData.append('weight', weight);
        formData.append('bmi', bmi);

        const response = await fetch('/update_vitals', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            showFlashMessage('Vitals updated successfully!', 'success');
            viewMember(mobileNumber); // Reload to get updated data
        } else {
            showFlashMessage('Failed to update vitals.', 'danger');
        }
    } catch (error) {
        console.error('Error updating vitals:', error);
        showFlashMessage('An error occurred while updating vitals.', 'danger');
    } finally {
        hideLoading();
    }
}

async function renewSubscription(event) {
    event.preventDefault();
    if (!currentMemberData) return;

    const plan = document.getElementById('renewSubscriptionPlan').value;
    const startDate = document.getElementById('renewSubscriptionStartDate').value;
    const endDate = document.getElementById('renewSubscriptionEndDate').value;
    const amount = document.getElementById('renewAmount').value;
    const discount = document.getElementById('renewDiscount').value;
    const paymentMethod = document.getElementById('renewPaymentMethod').value;
    const mobileNumber = currentMemberData.mobile_number;

    showLoading();
    try {
        const formData = new FormData();
        formData.append('mobile_number', mobileNumber);
        formData.append('subscription', plan);
        formData.append('subscription_start_date', startDate);
        formData.append('subscription_end_date', endDate);
        formData.append('amount', amount);
        formData.append('discount', discount);
        formData.append('payment_method', paymentMethod);

        const response = await fetch('/renew_subscription', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            showFlashMessage('Subscription renewed successfully! A new transaction has been recorded.', 'success');
            viewMember(mobileNumber); // Reload to get updated data
            // Also trigger a background reload of transactions just in case the user switches tabs
            fetch('/fitmafia').then(() => {});
        } else {
            showFlashMessage('Failed to renew subscription.', 'danger');
        }
    } catch (error) {
        console.error('Error renewing subscription:', error);
        showFlashMessage('An error occurred while renewing subscription.', 'danger');
    } finally {
        hideLoading();
    }
}

function editMember() {
    if (!currentMemberData) return;

    // Populate the form with currentMemberData
    document.getElementById('memberForm').action = '/update_member';
    document.getElementById('firstName').value = currentMemberData.first_name || '';
    document.getElementById('lastName').value = currentMemberData.last_name || '';
    document.getElementById('mobile_number').value = currentMemberData.mobile_number || '';
    document.getElementById('mobile_number').setAttribute('readonly', true); // Prevent PK change
    document.getElementById('email').value = currentMemberData.email || '';
    if (currentUserRole === 'member') {
         document.getElementById('email').setAttribute('readonly', true);
    }

    // Set password to the actual password and make it not required for submission
    const passwordField = document.getElementById('password');
    passwordField.value = currentMemberData.password || '';
    passwordField.removeAttribute('required');

    document.getElementById('gender').value = currentMemberData.gender || '';
    document.getElementById('address').value = currentMemberData.address || '';
    document.getElementById('dob').value = currentMemberData.dob || '';
    document.getElementById('joining_date').value = currentMemberData.joining_date || '';

    // If editing, hide the terms block since they've already accepted
    document.getElementById('termsContainer').style.display = 'none';
    document.getElementById('termsAccepted').removeAttribute('required');

    // Handle Photo Preview when editing
    const preview = document.getElementById('photoPreview');
    if (currentMemberData.photo) {
        preview.src = addCacheBuster(currentMemberData.photo); // Apply cache busting
        preview.style.display = 'block';
    } else {
        preview.style.display = 'none';
    }
    document.getElementById('capturedPhotoData').value = '';

    // Change Title & Buttons
    document.getElementById('registerFormTitle').innerText = "Edit Member Details";
    document.getElementById('submitBtn').innerText = "Update Member";
    document.getElementById('cancelEditBtn').classList.remove('d-none');

    // Show the registration form
    showSection('register');
}

function resetForm() {
    // Reset form fields
    document.getElementById('memberForm').reset();
    document.getElementById('memberForm').action = '/register_member';

    // Remove readonly from mobile number
    document.getElementById('mobile_number').removeAttribute('readonly');
    document.getElementById('email').removeAttribute('readonly');
    document.getElementById('password').setAttribute('required', 'true');

    // Reset password visibility
    const passwordField = document.getElementById('password');
    passwordField.setAttribute('type', 'password');
    const toggleIcon = document.getElementById('togglePassword').querySelector('i');
    toggleIcon.classList.remove('bi-eye');
    toggleIcon.classList.add('bi-eye-slash');

    // Show terms block for new registrations
    document.getElementById('termsContainer').style.display = 'block';
    document.getElementById('termsAccepted').setAttribute('required', 'true');

    // Hide preview and clear hidden input
    document.getElementById('photoPreview').style.display = 'none';
    document.getElementById('capturedPhotoData').value = '';

    // Reset UI labels and buttons
    document.getElementById('registerFormTitle').innerText = "New Member Registration";
    document.getElementById('submitBtn').innerText = "Register Member";
    document.getElementById('cancelEditBtn').classList.add('d-none');
    currentMemberData = null;

    // Reset joining date to today when canceling
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('joining_date').value = today;

    // If called explicitly via Cancel button, go back to Member list or Dashboard
    if(event && event.target.id === 'cancelEditBtn') {
        if (currentUserRole === 'admin') {
            showSection('members');
        } else {
            showSection('viewMemberDetails');
        }
    }
}

function viewMemberTransactions() {
    if (!currentMemberData) return;
    showSection('transactions');

    const searchInput = document.getElementById('transactionSearch');
    if (searchInput) {
        searchInput.value = currentMemberData.mobile_number;
    }
    document.getElementById('transactionFromDate').value = '';
    document.getElementById('transactionToDate').value = '';

    filterTransactions();
}

function validateAndHighlight(field, condition) {
    if (condition) {
        field.classList.remove('is-invalid');
        return true;
    } else {
        field.classList.add('is-invalid');
        return false;
    }
}

async function handleMemberFormSubmit(event) {
    event.preventDefault();

    const memberForm = document.getElementById('memberForm');
    const url = memberForm.action;
    let isValid = true;

    // --- Validation for new member registration ---
    if (url.endsWith('register_member')) {
        const firstNameField = document.getElementById('firstName');
        const lastNameField = document.getElementById('lastName');
        const mobileNumberField = document.getElementById('mobile_number');
        const passwordField = document.getElementById('password');
        const genderField = document.getElementById('gender');
        const dobField = document.getElementById('dob');
        const termsAcceptedField = document.getElementById('termsAccepted');

        isValid &= validateAndHighlight(firstNameField, firstNameField.value.trim() !== '');
        isValid &= validateAndHighlight(lastNameField, lastNameField.value.trim() !== '');
        isValid &= validateAndHighlight(mobileNumberField, /^\d{10}$/.test(mobileNumberField.value));
        isValid &= validateAndHighlight(passwordField, passwordField.value.length >= 4);
        isValid &= validateAndHighlight(genderField, genderField.value !== '');
        isValid &= validateAndHighlight(dobField, dobField.value !== '');
        if (termsAcceptedField && termsAcceptedField.hasAttribute('required')) {
            isValid &= validateAndHighlight(termsAcceptedField, termsAcceptedField.checked);
        }

        if (!isValid) {
            showFlashMessage('fill in all required fields', 'danger');
            return;
        }
    }
    // --- End of validation ---

    const formData = new FormData(memberForm);
    showLoading();

    try {
        const response = await fetch(url, { method: 'POST', body: formData });
        const result = await response.json();
        if (result.redirect) {
            window.location.href = result.redirect;
            return;
        }

        showFlashMessage(result.message, result.status);

        if (result.status === 'success') {
            if (url.endsWith('register_member')) {
                const mobileNumber = formData.get('mobile_number');
                viewMember(mobileNumber);
                resetForm();
            } else {
                const mobileNumber = formData.get('mobile_number');
                viewMember(mobileNumber);
            }
        }

    } catch (error) {
        console.error('Error:', error);
        showFlashMessage('An error occurred. Please try again.', 'danger');
    } finally {
        hideLoading();
    }
}

function togglePasswordVisibility() {
    const password = document.getElementById('password');
    const toggleBtn = document.getElementById('togglePassword');
    if (!password || !toggleBtn) return;
    const icon = toggleBtn.querySelector('i');
    const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
    password.setAttribute('type', type);
    icon.classList.toggle('bi-eye');
    icon.classList.toggle('bi-eye-slash');
}

//on load function
document.addEventListener('DOMContentLoaded', () => {
    const togglePassword = document.getElementById('togglePassword');
    if (togglePassword) {togglePassword.addEventListener('click', togglePasswordVisibility);}

    if (currentUserRole === 'member' && currentUserName) {
        if (currentMember) { populateMemberView(currentMember); }
        else { viewMember(currentUserName); }
        filterTransactions();}

    else {
        const currentActive = document.querySelector('.section.active');
        if (currentActive && currentActive.id === 'register') {
            const joiningDateField = document.getElementById('joining_date');
            if (joiningDateField) {
                const today = new Date().toISOString().split('T')[0];
                joiningDateField.value = today;
            } } }

    document.getElementById('submitBtn').addEventListener('click', handleMemberFormSubmit);
    autoCloseFlashes();
});
