// Global state
let currentTab = 'dashboard';
let currentPage = 1;
let editingItem = null;
let editingType = null;
let currentEmailSearch = '';
let currentSortBy = 'user_id';
let currentSortOrder = 'asc';
let jobsSortBy = 'created_at';
let jobsSortOrder = 'desc';
let currentTimeframe = 'day';
let charts = {};
let currentTheme = 'light';

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {

    initializeTheme();
    
    // Check authentication
    if (!checkAuth()) {
        window.location.href = '/login';
        return;
    }

    syncAdminPermissions().finally(loadDashboard);
});

// Re-derives permission flags from the server (self-heals sessions that logged
// in before permission flags like isSuperAdmin existed in localStorage).
async function syncAdminPermissions() {
    try {
        const response = await makeAuthenticatedRequest('/api/auth/verify');
        if (!response.ok) return;
        const { user } = await response.json();
        localStorage.setItem('adminIsSuperAdmin', user?.isSuperAdmin ? 'true' : 'false');
    } catch (error) {
        console.error('Error syncing admin permissions:', error);
    }

    const adminsTabButton = document.getElementById('nav-tab-admins');
    if (adminsTabButton) {
        adminsTabButton.style.display = isSuperAdmin() ? '' : 'none';
    }

    const jobsTabButton = document.getElementById('nav-tab-jobs');
    if (jobsTabButton) {
        jobsTabButton.style.display = isSuperAdmin() ? '' : 'none';
    }

}

function isSuperAdmin() {
    return localStorage.getItem('adminIsSuperAdmin') === 'true';
}

// Authentication functions
function checkAuth() {
    const token = localStorage.getItem('adminToken');
    if (!token) {
        return false;
    }
    
    // Verify token is valid (basic check)
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const now = Date.now() / 1000;
        
        if (payload.exp < now) {
            // Token expired
            localStorage.removeItem('adminToken');
            return false;
        }
        
        return true;
    } catch (error) {
        // Invalid token
        localStorage.removeItem('adminToken');
        return false;
    }
}

function logout() {
    localStorage.removeItem('adminToken');
    localStorage.removeItem('adminIsSuperAdmin');
    window.location.href = '/login';
}

// Add authorization header to all API requests
function makeAuthenticatedRequest(url, options = {}) {
    const token = localStorage.getItem('adminToken');
    
    const defaultOptions = {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...options.headers
        }
    };
    
    return fetch(url, { ...options, ...defaultOptions });
}

// Theme management functions
function initializeTheme() {
    // Load saved theme or default to light
    const savedTheme = localStorage.getItem('adminTheme') || 'light';
    currentTheme = savedTheme;
    applyTheme(savedTheme);
}

function toggleTheme() {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(currentTheme);
    localStorage.setItem('adminTheme', currentTheme);
    
    // Update charts with new theme colors
    updateChartsTheme();
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    
    // Update toggle button
    const themeIcon = document.querySelector('.theme-icon');
    const themeText = document.querySelector('.theme-text');
    
    if (theme === 'dark') {
        themeIcon.textContent = '◐';
        themeText.textContent = 'Light';
    } else {
        themeIcon.textContent = '◑';
        themeText.textContent = 'Dark';
    }
}

function updateChartsTheme() {
    // Get current theme colors
    const isDark = currentTheme === 'dark';
    const gridColor = isDark ? '#404040' : '#f0f0f0';
    const textColor = isDark ? '#e0e0e0' : '#333';
    
    // Update all existing charts
    Object.keys(charts).forEach(chartId => {
        if (charts[chartId]) {
            const chart = charts[chartId];
            
            // Update grid colors
            if (chart.options.scales) {
                if (chart.options.scales.x && chart.options.scales.x.grid) {
                    chart.options.scales.x.grid.color = gridColor;
                }
                if (chart.options.scales.y && chart.options.scales.y.grid) {
                    chart.options.scales.y.grid.color = gridColor;
                }
                
                // Update tick colors
                if (chart.options.scales.x && chart.options.scales.x.ticks) {
                    chart.options.scales.x.ticks.color = textColor;
                }
                if (chart.options.scales.y && chart.options.scales.y.ticks) {
                    chart.options.scales.y.ticks.color = textColor;
                }
            }
            
            // Update legend colors for doughnut charts
            if (chart.options.plugins && chart.options.plugins.legend && chart.options.plugins.legend.labels) {
                chart.options.plugins.legend.labels.color = textColor;
            }
            
            chart.update();
        }
    });
}

// Tab management
function showTab(tabName) {

    
    // Update nav tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');

    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });

    // Show selected tab
    document.getElementById(tabName + '-tab').classList.remove('hidden');
    currentTab = tabName;

    // Load data for the tab
    switch(tabName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'profiles':
            loadProfiles(1, currentEmailSearch);
            break;
        case 'admins':
            loadAdminUsers();
            break;
        case 'activity':
            // Default to today's range the first time the tab opens; later visits keep whatever range is set
            if (!activityDefaultApplied) {
                activityDefaultApplied = true;
                applyActivityPreset('day'); // also loads the activity
            } else {
                loadActivity();
            }
            break;
        case 'jobs':
            loadJobs(1, '', jobsSortBy, jobsSortOrder);
            break;
        case 'analytics':
            loadAnalytics();
            break;
    }
}

// Timeframe functions
function setTimeframe(timeframe) {
    currentTimeframe = timeframe;
    
    // Update active button
    document.querySelectorAll('.timeframe-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Reload dashboard with new timeframe
    loadDashboard();
}

// Chart creation functions
function createLineChart(canvasId, data, label, color = '#007bff') {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Get theme-aware colors
    const isDark = currentTheme === 'dark';
    const gridColor = isDark ? '#404040' : '#f0f0f0';
    const textColor = isDark ? '#e0e0e0' : '#333';
    
    // Adjust color for dark mode
    const chartColor = isDark ? getThemeColor(color) : color;
    
    // Destroy existing chart if it exists
    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }
    
    charts[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: label,
                data: data.values,
                borderColor: chartColor,
                backgroundColor: chartColor + '20',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxTicksLimit: 6,
                        font: {
                            size: 10
                        },
                        color: textColor
                    }
                },
                y: {
                    display: true,
                    grid: {
                        color: gridColor
                    },
                    ticks: {
                        font: {
                            size: 10
                        },
                        color: textColor
                    }
                }
            }
        }
    });
}

function getThemeColor(lightColor) {
    // Map light theme colors to dark theme equivalents
    const colorMap = {
        '#007bff': '#4a9eff',
        '#28a745': '#4caf50',
        '#ffc107': '#ff9800',
        '#dc3545': '#f44336'
    };
    return colorMap[lightColor] || lightColor;
}

function createDoughnutChart(canvasId, data, colors = ['#007bff', '#28a745', '#ffc107', '#dc3545']) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Get theme-aware colors
    const isDark = currentTheme === 'dark';
    const textColor = isDark ? '#e0e0e0' : '#333';
    const themeColors = isDark ? colors.map(color => getThemeColor(color)) : colors;
    
    // Destroy existing chart if it exists
    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }
    
    charts[canvasId] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: themeColors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        font: {
                            size: 10
                        },
                        padding: 10,
                        color: textColor
                    }
                }
            }
        }
    });
}

// Dashboard functions
async function loadDashboard() {
    try {
        // Show loading spinner
        document.getElementById('dashboard-loading').style.display = 'inline-block';
        
        const response = await makeAuthenticatedRequest(`/api/analytics?timeframe=${currentTimeframe}`);
        const data = await response.json();
        
        // Update totals
        document.getElementById('total-profiles').textContent = data.totals.profiles;
        document.getElementById('total-jobs').textContent = data.totals.jobs;
        document.getElementById('job-status-count').textContent = Object.values(data.jobsByStatus).reduce((a, b) => a + b, 0);
        document.getElementById('user-activity').textContent = data.totals.activeUsers;
        
        // Create charts
        if (data.timeSeries && data.timeSeries.length > 0) {
            const labels = data.timeSeries.map(item => item.label);
            
            // Profiles chart
            createLineChart('profiles-chart', {
                labels: labels,
                values: data.timeSeries.map(item => item.profiles)
            }, 'New Profiles', '#007bff');
            
            // Jobs chart
            createLineChart('jobs-chart', {
                labels: labels,
                values: data.timeSeries.map(item => item.jobs)
            }, 'New Jobs', '#28a745');
            
            // Activity chart (combination of profiles and jobs)
            createLineChart('activity-chart', {
                labels: labels,
                values: data.timeSeries.map(item => item.profiles + item.jobs)
            }, 'Total Activity', '#ffc107');
        }
        
        // Job status chart
        if (data.jobsByStatus && Object.keys(data.jobsByStatus).length > 0) {
            createDoughnutChart('job-status-chart', {
                labels: Object.keys(data.jobsByStatus),
                values: Object.values(data.jobsByStatus)
            });
        }
        

        
        // Hide loading spinner
        document.getElementById('dashboard-loading').style.display = 'none';
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError('Failed to load dashboard data');
        document.getElementById('dashboard-loading').style.display = 'none';
    }
}

// Profiles functions
async function loadProfiles(page = 1, emailSearch = '', sortBy = currentSortBy, sortOrder = currentSortOrder) {
    try {

        
        let url = `/api/profiles?page=${page}&limit=20&sortBy=${sortBy}&sortOrder=${sortOrder}`;
        if (emailSearch) {
            url += `&email=${encodeURIComponent(emailSearch)}`;
        }
        
        const response = await makeAuthenticatedRequest(url);

        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();

        
        const content = document.getElementById('profiles-content');
        const pagination = document.getElementById('profiles-pagination');
        
        if (data.data && data.data.length > 0) {
            content.innerHTML = `
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Actions</th>
                                <th>Status</th>
                                <th class="sortable" onclick="sortProfiles('email')" style="cursor: pointer; user-select: none;">
                                    Email<span class="sort-icon">${getSortIcon('email', sortBy, sortOrder)}</span>
                                </th>
                                <th class="sortable" onclick="sortProfiles('activePlan')" style="cursor: pointer; user-select: none;">
                                    Active Plan<span class="sort-icon">${getSortIcon('activePlan', sortBy, sortOrder)}</span>
                                </th>
                                <th class="sortable" onclick="sortProfiles('generations_left')" style="cursor: pointer; user-select: none;">
                                    Generations Left<span class="sort-icon">${getSortIcon('generations_left', sortBy, sortOrder)}</span>
                                </th>
                                <th class="sortable" onclick="sortProfiles('created_at')" style="cursor: pointer; user-select: none;">
                                    Created<span class="sort-icon">${getSortIcon('created_at', sortBy, sortOrder)}</span>
                                </th>
                                <th class="sortable" onclick="sortProfiles('last_sign_in_at')" style="cursor: pointer; user-select: none;">
                                    Last Sign In<span class="sort-icon">${getSortIcon('last_sign_in_at', sortBy, sortOrder)}</span>
                                </th>
                                <th class="sortable" onclick="sortProfiles('auto_delete_enabled')" style="cursor: pointer; user-select: none;">
                                    Auto Delete<span class="sort-icon">${getSortIcon('auto_delete_enabled', sortBy, sortOrder)}</span>
                                </th>
                                <th class="sortable" onclick="sortProfiles('user_id')" style="cursor: pointer; user-select: none;">
                                    User ID<span class="sort-icon">${getSortIcon('user_id', sortBy, sortOrder)}</span>
                                </th>
                                <th>Secret Key</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.data.map(profile => `
                                <tr>
                                    <td>
                                        <button class="btn btn-small" onclick="editProfile('${profile.user_id}')">Edit</button>
                                        <button class="btn btn-small" style="background: ${profile.banned ? '#28a745' : '#dc3545'};" onclick="toggleBanProfile('${profile.user_id}', ${profile.banned ? 'true' : 'false'})">${profile.banned ? 'Unban' : 'Ban'}</button>
                                        ${isSuperAdmin() ? `<button class="btn btn-small btn-danger" onclick="deleteProfile('${profile.user_id}')">Delete</button>` : ''}
                                    </td>
                                    <td>${profile.banned ? '<span style="color: #dc3545; font-weight: 600;" title="' + escapeHtml(profile.ban_reason || '') + '">Banned</span>' : '<span style="color: #28a745;">Active</span>'}</td>
                                    <td>${escapeHtml(profile.email) || 'No email'}</td>
                                    <td>${getPlanBadge(profile.activePlan)}</td>
                                    <td>${profile.generations_left || 0}</td>
                                    <td>${profile.created_at ? new Date(profile.created_at).toLocaleDateString() : 'N/A'}</td>
                                    <td>${profile.last_sign_in_at ? new Date(profile.last_sign_in_at).toLocaleDateString() : 'Never'}</td>
                                    <td>${profile.auto_delete_enabled ? 'Yes (' + profile.auto_delete_days + 'd)' : 'No'}</td>
                                    <td>${profile.user_id ? profile.user_id.substring(0, 8) + '...' : 'N/A'}</td>
                                    <td>${profile.secret_key ? escapeHtml(profile.secret_key.substring(0, 12)) + '...' : '—'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
            
            // Show pagination
            pagination.classList.remove('hidden');
            // Search text is typed by the admin: escape it for display, and pass it to
            // the paging buttons via currentEmailSearch rather than splicing it into onclick
            pagination.innerHTML = `
                <div>Page ${data.pagination.page} of ${data.pagination.totalPages} (${data.pagination.total} total)${emailSearch ? ` - Search: "${escapeHtml(emailSearch)}"` : ''}</div>
                <div>
                    ${data.pagination.page > 1 ? `<button class="btn" onclick="loadProfiles(${data.pagination.page - 1}, currentEmailSearch, '${sortBy}', '${sortOrder}')">Previous</button>` : ''}
                    ${data.pagination.page < data.pagination.totalPages ? `<button class="btn" onclick="loadProfiles(${data.pagination.page + 1}, currentEmailSearch, '${sortBy}', '${sortOrder}')">Next</button>` : ''}
                </div>
            `;
        } else {
            content.innerHTML = '<div style="padding: 2rem; text-align: center; color: #666;">No profiles found</div>';
            pagination.classList.add('hidden');
        }
    } catch (error) {
        console.error('Error loading profiles:', error);
        showError('Failed to load profiles');
    }
}

// Jobs functions
async function loadJobs(page = 1, status = '', sortBy = jobsSortBy, sortOrder = jobsSortOrder) {
    try {
        let url = `/api/jobs?page=${page}&limit=20&sortBy=${sortBy}&sortOrder=${sortOrder}`;
        if (status) url += `&status=${status}`;
        
        const response = await makeAuthenticatedRequest(url);
        const data = await response.json();
        
        const content = document.getElementById('jobs-content');
        const pagination = document.getElementById('jobs-pagination');
        
        if (data.data && data.data.length > 0) {
            content.innerHTML = `
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Actions</th>
                                <th class="sortable" onclick="sortJobs('id')" style="cursor: pointer; user-select: none;">
                                    ID<span class="sort-icon">${getSortIcon('id', sortBy, sortOrder)}</span>
                                </th>
                                <th class="sortable" onclick="sortJobs('status')" style="cursor: pointer; user-select: none;">
                                    Status<span class="sort-icon">${getSortIcon('status', sortBy, sortOrder)}</span>
                                </th>
                                <th class="sortable" onclick="sortJobs('document_type')" style="cursor: pointer; user-select: none;">
                                    Document Type<span class="sort-icon">${getSortIcon('document_type', sortBy, sortOrder)}</span>
                                </th>
                                <th class="sortable" onclick="sortJobs('country')" style="cursor: pointer; user-select: none;">
                                    Country<span class="sort-icon">${getSortIcon('country', sortBy, sortOrder)}</span>
                                </th>
                                <th class="sortable" onclick="sortJobs('created_at')" style="cursor: pointer; user-select: none;">
                                    Created<span class="sort-icon">${getSortIcon('created_at', sortBy, sortOrder)}</span>
                                </th>
                                <th class="sortable" onclick="sortJobs('user_id')" style="cursor: pointer; user-select: none;">
                                    User ID<span class="sort-icon">${getSortIcon('user_id', sortBy, sortOrder)}</span>
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.data.map(job => `
                                <tr>
                                    <td>
                                        <button class="btn btn-small" onclick="editJob('${job.id}')">Edit</button>
                                        <button class="btn btn-small btn-danger" onclick="deleteJob('${job.id}')">Delete</button>
                                    </td>
                                    <td>${job.id.substring(0, 8)}...</td>
                                    <td><span class="status-${escapeHtml(job.status)}">${escapeHtml(job.status)}</span></td>
                                    <td>${escapeHtml(job.document_type) || 'N/A'}</td>
                                    <td>${escapeHtml(job.country) || 'N/A'}</td>
                                    <td>${new Date(job.created_at).toLocaleDateString()}</td>
                                    <td>${job.user_id ? job.user_id.substring(0, 8) + '...' : 'N/A'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
            
            // Show pagination
            pagination.classList.remove('hidden');
            pagination.innerHTML = `
                <div>Page ${data.pagination.page} of ${data.pagination.totalPages} (${data.pagination.total} total)</div>
                <div>
                    ${data.pagination.page > 1 ? `<button class="btn" onclick="loadJobs(${data.pagination.page - 1}, '${status}', '${sortBy}', '${sortOrder}')">Previous</button>` : ''}
                    ${data.pagination.page < data.pagination.totalPages ? `<button class="btn" onclick="loadJobs(${data.pagination.page + 1}, '${status}', '${sortBy}', '${sortOrder}')">Next</button>` : ''}
                </div>
            `;
        } else {
            content.innerHTML = '<div style="padding: 2rem; text-align: center; color: #666;">No jobs found</div>';
            pagination.classList.add('hidden');
        }
    } catch (error) {
        console.error('Error loading jobs:', error);
        showError('Failed to load jobs');
    }
}

// Filter and refresh functions
function filterJobs() {
    const status = document.getElementById('job-status-filter').value;
    loadJobs(1, status, jobsSortBy, jobsSortOrder);
}

function refreshProfiles() {
    loadProfiles(currentPage, currentEmailSearch, currentSortBy, currentSortOrder);
}

// Email search functions
function searchProfiles() {
    const emailInput = document.getElementById('email-search');
    const emailSearch = emailInput.value.trim();
    currentEmailSearch = emailSearch;
    currentPage = 1; // Reset to first page when searching
    loadProfiles(1, emailSearch, currentSortBy, currentSortOrder);
}

function clearSearch() {
    const emailInput = document.getElementById('email-search');
    emailInput.value = '';
    currentEmailSearch = '';
    currentPage = 1;
    loadProfiles(1, '', currentSortBy, currentSortOrder);
}

// Sorting functions
function sortProfiles(column) {
    if (currentSortBy === column) {
        // Toggle sort order if same column
        currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        // New column, default to ascending
        currentSortBy = column;
        currentSortOrder = 'asc';
    }
    currentPage = 1; // Reset to first page when sorting
    loadProfiles(1, currentEmailSearch, currentSortBy, currentSortOrder);
}

function sortJobs(column) {
    if (jobsSortBy === column) {
        // Toggle sort order if same column
        jobsSortOrder = jobsSortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        // New column, default to ascending
        jobsSortBy = column;
        jobsSortOrder = 'asc';
    }
    currentPage = 1; // Reset to first page when sorting
    const status = document.getElementById('job-status-filter').value;
    loadJobs(1, status, jobsSortBy, jobsSortOrder);
}

function getSortIcon(column, currentSortBy, currentSortOrder) {
    if (column === currentSortBy) {
        return currentSortOrder === 'asc' ? '↑' : '↓';
    }
    return '↕';
}

function getPlanBadge(plan) {
    // No Plan is stored as '-'
    if (!plan || plan === '-') {
        return '<span class="plan-badge plan-none">None</span>';
    }
    
    if (isCustomPlan(plan)) {
        return `<span class="plan-badge plan-custom" title="Custom plan">${escapeHtml(plan)}</span>`;
    }
    
    const planClass = `plan-${plan.toLowerCase()}`;
    const planName = plan.charAt(0).toUpperCase() + plan.slice(1);
    const generations = getPlanGenerations(plan);
    
    return `<span class="plan-badge ${planClass}" title="${generations} generations">${planName}</span>`;
}

function getPlanGenerations(plan) {
    const planGenerations = {
        'try': 1,
        'light': 10,
        'medium': 50,
        'pro': 150,
        'ultimate': 1000
    };
    return planGenerations[plan] || 0;
}

function isCustomPlan(plan) {
    const standardPlans = ['', '-', 'try', 'light', 'medium', 'pro', 'ultimate'];
    return plan && !standardPlans.includes(plan);
}

// Called when the plan dropdown changes: toggles the custom-plan name field
// and switches "Credits to Add" between a fixed plan readout and a free entry.
function updatePlanCreditPreview() {
    const planSelect = document.getElementById('edit-activePlan');
    const addInput = document.getElementById('edit-credits-add');
    const addHelp = document.getElementById('credits-add-help');
    const minusBtn = document.getElementById('credit-stepper-minus');
    const plusBtn = document.getElementById('credit-stepper-plus');
    if (!planSelect || !addInput) return;

    const selectedPlan = planSelect.value;
    const isCustom = selectedPlan === 'custom';

    if (minusBtn) minusBtn.style.display = isCustom ? '' : 'none';
    if (plusBtn) plusBtn.style.display = isCustom ? '' : 'none';

    if (isCustom) {
        addInput.removeAttribute('readonly');
        addInput.value = 0; // always start custom entry from 0, not whatever the last plan left behind
        addHelp.textContent = 'Enter a positive number to add credits, or a negative number to remove some - or use the − / + buttons.';
        setTimeout(() => addInput.focus(), 100);
    } else {
        addHelp.textContent = selectedPlan ? 'Set automatically by the selected plan above.' : 'Select a plan above to add credits.';
        addInput.setAttribute('readonly', 'readonly');
        addInput.value = getPlanGenerations(selectedPlan); // '' (no selection) -> 0
    }

    updateFinalCreditsPreview();
}

// The − / + stepper buttons shown next to Credits to Add while Custom Plan is
// selected; a no-op when the field is readonly (any other plan selected).
function adjustCreditsToAdd(delta) {
    const addInput = document.getElementById('edit-credits-add');
    if (!addInput || addInput.hasAttribute('readonly')) return;

    const current = parseInt(addInput.value, 10) || 0;
    addInput.value = current + delta;
    updateFinalCreditsPreview();
}

// Recomputes "Final Credits" = current credits + whatever is in "Credits to Add",
// and updates the +/- badge shown on the arrow between the current and final boxes.
function updateFinalCreditsPreview() {
    const currentEl = document.getElementById('current-credits-value');
    const addInput = document.getElementById('edit-credits-add');
    const finalDisplay = document.getElementById('final-credits-display');
    const finalValueEl = document.getElementById('final-credits-value');
    const deltaEl = document.getElementById('credit-flow-delta');
    const noteEl = document.getElementById('final-credits-note');
    if (!currentEl || !addInput || !finalValueEl) return;

    const current = parseInt(currentEl.dataset.value, 10) || 0;
    const addAmount = parseInt(addInput.value, 10) || 0;
    const rawFinal = current + addAmount;
    const final = Math.max(0, rawFinal);

    finalValueEl.textContent = final;
    if (finalDisplay) finalDisplay.classList.toggle('is-negative', rawFinal < 0);

    if (deltaEl) {
        deltaEl.textContent = addAmount > 0 ? `+${addAmount}` : addAmount < 0 ? `−${Math.abs(addAmount)}` : '+0';
        deltaEl.classList.toggle('is-positive', addAmount > 0);
        deltaEl.classList.toggle('is-negative', addAmount < 0);
    }

    if (noteEl) {
        const planSelect = document.getElementById('edit-activePlan');
        const assignedPlan = planSelect ? planSelect.value : '';
        const currentPlanForCustom = editingItem ? (editingItem.activePlan || '-') : '';
        if (rawFinal < 0) {
            noteEl.textContent = `${current} ${addAmount >= 0 ? '+' : ''}${addAmount} would go below 0 - clamped to 0`;
        } else if (assignedPlan === 'custom' && addAmount > 0 && editingItem
                   && (currentPlanForCustom === '-' || PLAN_ORDER.includes(String(currentPlanForCustom).toLowerCase()))) {
            // Custom credits count as the plan the amount matches and can only move the plan up
            const matchedPlan = planForCustomCredits(addAmount);
            const resultPlan = resolveAssignedPlan(currentPlanForCustom, matchedPlan);
            noteEl.textContent = resultPlan !== currentPlanForCustom
                ? `Plan changes to ${planDisplayName(resultPlan)} (+${addAmount} counts as ${planDisplayName(matchedPlan)}).`
                : `Plan stays ${planDisplayName(currentPlanForCustom)} (+${addAmount} counts as ${planDisplayName(matchedPlan)}, which isn't higher).`;
        } else if (assignedPlan && assignedPlan !== 'custom' && editingItem) {
            const currentPlan = editingItem.activePlan || '-';
            const resultPlan = resolveAssignedPlan(currentPlan, assignedPlan);
            if (resultPlan !== currentPlan) {
                noteEl.textContent = PLAN_ORDER.includes(String(currentPlan).toLowerCase())
                    ? `Plan upgrades from ${planDisplayName(currentPlan)} to ${planDisplayName(assignedPlan)}.`
                    : `Plan changes to ${planDisplayName(assignedPlan)}.`;
            } else if (assignedPlan === String(currentPlan).toLowerCase()) {
                noteEl.textContent = `Plan stays ${planDisplayName(currentPlan)}.`;
            } else {
                noteEl.textContent = `Plan stays ${planDisplayName(currentPlan)} (${planDisplayName(assignedPlan)} is a lower plan - plans only move up).`;
            }
        } else {
            noteEl.textContent = '';
        }
    }
}

// Standard plans from lowest to highest
const PLAN_ORDER = ['try', 'light', 'medium', 'pro', 'ultimate'];

// Same as planForCustomCredits in routes/profiles-admin.js: the highest plan a
// custom amount covers (+1 to +9 Try, +10 to +49 Light, +50 Medium, +150 Pro,
// +1000 Ultimate)
function planForCustomCredits(credits) {
    for (let i = PLAN_ORDER.length - 1; i >= 0; i--) {
        if (credits >= getPlanGenerations(PLAN_ORDER[i])) return PLAN_ORDER[i];
    }
    return null;
}

// Same rule as resolveAssignedPlan in routes/profiles-admin.js (the server decides;
// this is only for the preview): plans only move up. A higher plan replaces the
// current one, the same or a lower one keeps it, and No Plan or a custom-named
// plan takes the standard plan picked.
function resolveAssignedPlan(currentPlan, assignedPlan) {
    const currentRank = PLAN_ORDER.indexOf(String(currentPlan || '').toLowerCase());
    if (currentRank === -1 || PLAN_ORDER.indexOf(assignedPlan) > currentRank) {
        return assignedPlan;
    }
    return currentPlan;
}

function planDisplayName(plan) {
    if (!plan || plan === '-') return 'No Plan';
    return plan.charAt(0).toUpperCase() + plan.slice(1);
}

// Add Enter key support for search
document.addEventListener('DOMContentLoaded', function() {
    const emailInput = document.getElementById('email-search');
    if (emailInput) {
        emailInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchProfiles();
            }
        });
    }
});

function refreshJobs() {
    const status = document.getElementById('job-status-filter').value;
    loadJobs(currentPage, status, jobsSortBy, jobsSortOrder);
}

// Edit functions
async function editProfile(userId) {
    try {
        const response = await makeAuthenticatedRequest(`/api/profiles/${userId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const profile = await response.json();
        
        editingItem = profile;
        editingType = 'profile';

        // The dropdown always opens on "No Plan" rather than the profile's actual
        // plan, so Credits to Add starts at 0 and opening+saving is a no-op -
        // the admin has to deliberately pick a plan to change anything.
        const initialCreditsToAdd = 0;
        const initialFinalCredits = profile.generations_left || 0;

        document.getElementById('modal-title').textContent = 'Edit Profile';
        document.getElementById('modal-body').innerHTML = `
            <div class="form-group">
                <label>User ID</label>
                <input type="text" value="${profile.user_id || ''}" disabled style="background: #f5f5f5;" />
            </div>
            <div class="form-group">
                <label>Email</label>
                <input type="email" value="${escapeHtml(profile.email) || 'No email'}" disabled style="background: #f5f5f5;" />
            </div>
            <div class="form-group">
                <label>Assign Plan</label>
                <select id="edit-activePlan" onchange="updatePlanCreditPreview()">
                    <option value="" selected>Select a plan to assign...</option>
                    <option value="try">Try (+1)</option>
                    <option value="light">Light (+10)</option>
                    <option value="medium">Medium (+50)</option>
                    <option value="pro">Pro (+150)</option>
                    <option value="ultimate">Ultimate (+1000)</option>
                    <option disabled>──────────</option>
                    <option value="custom">Custom Plan</option>
                </select>
                <small style="color: #6c757d; font-size: 0.8rem;">
                    Currently on: ${profile.activePlan && profile.activePlan !== '-' ? escapeHtml(profile.activePlan) : 'No Plan'}. "No Plan" isn't something you assign - it's the state of a new signup who hasn't bought anything yet. Plans only move up, and a user keeps their plan even at 0 credits.
                </small>
            </div>
            <div class="form-group">
                <label id="credits-add-label">Credits to Add</label>
                <div class="credit-stepper">
                    <button type="button" class="stepper-btn stepper-minus" id="credit-stepper-minus" onclick="adjustCreditsToAdd(-1)" style="display: none;" aria-label="Decrease">&minus;</button>
                    <input type="number" id="edit-credits-add" value="${initialCreditsToAdd}" oninput="updateFinalCreditsPreview()" readonly />
                    <button type="button" class="stepper-btn stepper-plus" id="credit-stepper-plus" onclick="adjustCreditsToAdd(1)" style="display: none;" aria-label="Increase">&plus;</button>
                </div>
                <small style="color: #6c757d; font-size: 0.8rem;" id="credits-add-help">
                    Select a plan above to add credits.
                </small>
            </div>
            <div class="form-group">
                <label>Credit Change</label>
                <div class="credit-flow">
                    <div class="credit-flow-box">
                        <span class="credit-flow-box-label">Current</span>
                        <div class="credit-display">
                            <span class="credit-icon">🔥</span>
                            <span id="current-credits-value" data-value="${profile.generations_left || 0}">${profile.generations_left || 0}</span>
                        </div>
                    </div>
                    <div class="credit-flow-arrow">
                        <span class="credit-flow-delta${initialCreditsToAdd > 0 ? ' is-positive' : initialCreditsToAdd < 0 ? ' is-negative' : ''}" id="credit-flow-delta">${initialCreditsToAdd > 0 ? '+' : initialCreditsToAdd < 0 ? '−' : '+'}${Math.abs(initialCreditsToAdd)}</span>
                        <span class="credit-flow-arrow-icon">&#8594;</span>
                    </div>
                    <div class="credit-flow-box">
                        <span class="credit-flow-box-label">Final</span>
                        <div class="credit-display final" id="final-credits-display">
                            <span class="credit-icon">🔥</span>
                            <span id="final-credits-value">${initialFinalCredits}</span>
                        </div>
                    </div>
                </div>
                <div class="credit-add-preview" id="final-credits-note"></div>
            </div>
            <div class="form-group">
                <label>Auto Delete Enabled</label>
                <select id="edit-auto_delete_enabled">
                    <option value="true" ${profile.auto_delete_enabled ? 'selected' : ''}>Yes</option>
                    <option value="false" ${!profile.auto_delete_enabled ? 'selected' : ''}>No</option>
                </select>
            </div>
            <div class="form-group">
                <label>Auto Delete Days</label>
                <input type="number" id="edit-auto_delete_days" value="${profile.auto_delete_days || 30}" />
            </div>
            <div class="form-group">
                <label>Secret Key</label>
                <input type="text" id="edit-secret_key" value="${escapeHtml(profile.secret_key) || ''}" placeholder="Leave blank to clear" />
                <small style="color: #6c757d; font-size: 0.8rem;">Must be unique across all users</small>
            </div>
            <div class="form-group">
                <label>Remarks</label>
                <textarea id="edit-remarks" rows="3" placeholder="Internal notes about this profile...">${escapeHtml(profile.remarks) || ''}</textarea>
                <small style="color: #6c757d; font-size: 0.8rem;">Visible only to admins</small>
            </div>
        `;
        
        const modal = document.getElementById('edit-modal');
        modal.classList.remove('hidden');
        modal.style.display = 'flex';
    } catch (error) {
        console.error('Error loading profile:', error);
        showError('Failed to load profile data: ' + error.message);
    }
}

async function editJob(jobId) {
    try {
        const response = await fetch(`/api/jobs/${jobId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const job = await response.json();
        
        editingItem = job;
        editingType = 'job';
        
        document.getElementById('modal-title').textContent = 'Edit Job';
        document.getElementById('modal-body').innerHTML = `
            <div class="form-group">
                <label>Job ID</label>
                <input type="text" value="${escapeHtml(job.id) || ''}" disabled style="background: #f5f5f5;" />
            </div>
            <div class="form-group">
                <label>Status</label>
                <select id="edit-status">
                    <option value="pending" ${job.status === 'pending' ? 'selected' : ''}>Pending</option>
                    <option value="processing" ${job.status === 'processing' ? 'selected' : ''}>Processing</option>
                    <option value="completed" ${job.status === 'completed' ? 'selected' : ''}>Completed</option>
                    <option value="failed" ${job.status === 'failed' ? 'selected' : ''}>Failed</option>
                </select>
            </div>
            <div class="form-group">
                <label>Document Type</label>
                <input type="text" id="edit-document_type" value="${escapeHtml(job.document_type) || ''}" />
            </div>
            <div class="form-group">
                <label>Country</label>
                <input type="text" id="edit-country" value="${escapeHtml(job.country) || ''}" />
            </div>
        `;
        
        const modal = document.getElementById('edit-modal');
        modal.classList.remove('hidden');
        modal.style.display = 'flex';
    } catch (error) {
        console.error('Error loading job:', error);
        showError('Failed to load job data: ' + error.message);
    }
}

async function saveEdit() {
    try {
        let updateData = {};
        let url = '';
        
        if (editingType === 'profile') {
            const planSelect = document.getElementById('edit-activePlan');

            let activePlan = planSelect.value;

            // The dropdown opens on the placeholder ("" - no selection made) and
            // "Custom Plan" only adjusts credits, not the plan name - in both
            // cases keep whatever plan the profile already had (may itself be a
            // legacy custom name) instead of overwriting it.
            if (activePlan === '' || activePlan === 'custom') {
                activePlan = editingItem.activePlan || '';
            }

            const currentCredits = parseInt(document.getElementById('current-credits-value').dataset.value, 10) || 0;
            const creditsToAdd = parseInt(document.getElementById('edit-credits-add').value, 10) || 0;
            const finalCredits = Math.max(0, currentCredits + creditsToAdd);

            const secretKeyValue = document.getElementById('edit-secret_key').value.trim();
            updateData = {
                activePlan: activePlan,
                generations_left: finalCredits,
                // The server adds these to the user's live balance (see profiles-admin.js)
                assigned_plan: planSelect.value,
                credits_to_add: creditsToAdd,
                auto_delete_enabled: document.getElementById('edit-auto_delete_enabled').value === 'true',
                auto_delete_days: parseInt(document.getElementById('edit-auto_delete_days').value),
                secret_key: secretKeyValue || null,
                remarks: document.getElementById('edit-remarks').value.trim() || null
            };
            url = `/api/profiles/${editingItem.user_id}`;
        } else if (editingType === 'job') {
            updateData = {
                status: document.getElementById('edit-status').value,
                document_type: document.getElementById('edit-document_type').value,
                country: document.getElementById('edit-country').value
            };
            url = `/api/jobs/${editingItem.id}`;
        }
        
        const response = await makeAuthenticatedRequest(url, {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
        
        if (response.ok) {
            closeModal();
            // Refresh the current tab
            if (currentTab === 'profiles') {
                refreshProfiles();
            } else if (currentTab === 'jobs') {
                refreshJobs();
            }
        } else {
            // Surface the server's actual reason (e.g. a validation message)
            // instead of a generic failure with no way to tell what went wrong.
            const errorBody = await response.json().catch(() => ({}));
            throw new Error(errorBody.error || `Failed to save changes (HTTP ${response.status})`);
        }
    } catch (error) {
        console.error('Error saving:', error);
        showError(error.message || 'Failed to save changes');
    }
}

// Admin user management functions
function getCurrentAdminId() {
    const token = localStorage.getItem('adminToken');
    if (!token) return null;
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.sub || null;
    } catch (error) {
        return null;
    }
}

async function loadAdminUsers() {
    try {
        const response = await makeAuthenticatedRequest('/api/admin-users');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const { data } = await response.json();
        const content = document.getElementById('admins-content');
        const currentAdminId = getCurrentAdminId();

        if (data && data.length > 0) {
            content.innerHTML = `
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Actions</th>
                                <th>Email</th>
                                <th>Added</th>
                                <th>Last Sign In</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.map(admin => `
                                <tr>
                                    <td>
                                        <button class="btn btn-small" data-user-id="${admin.user_id}" data-email="${escapeHtml(admin.email)}" onclick="openApiKeyModal(this.dataset.userId, this.dataset.email)">API Key</button>
                                        ${admin.user_id === currentAdminId
                                            ? '<span style="color: #999;">(you)</span>'
                                            : `<button class="btn btn-small btn-danger" onclick="revokeAdmin('${admin.user_id}')">Revoke</button>`}
                                    </td>
                                    <td>${escapeHtml(admin.email) || 'No email'}</td>
                                    <td>${admin.created_at ? new Date(admin.created_at).toLocaleDateString() : 'N/A'}</td>
                                    <td>${admin.last_sign_in_at ? new Date(admin.last_sign_in_at).toLocaleDateString() : 'Never'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            content.innerHTML = '<div style="padding: 2rem; text-align: center; color: #666;">No admins found</div>';
        }
    } catch (error) {
        console.error('Error loading admin users:', error);
        showError('Failed to load admin users');
    }
}

function openAddAdminModal() {
    document.getElementById('new-admin-email').value = '';
    document.getElementById('new-admin-password').value = '';
    const modal = document.getElementById('add-admin-modal');
    modal.classList.remove('hidden');
    modal.style.display = 'flex';
}

function closeAddAdminModal() {
    const modal = document.getElementById('add-admin-modal');
    modal.classList.add('hidden');
    modal.style.display = 'none';
}

async function submitAddAdmin() {
    const email = document.getElementById('new-admin-email').value.trim();
    const password = document.getElementById('new-admin-password').value;

    if (!email || !password) {
        alert('Email and password are required');
        return;
    }

    try {
        const response = await makeAuthenticatedRequest('/api/admin-users', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });

        if (response.ok) {
            closeAddAdminModal();
            loadAdminUsers();
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create admin');
        }
    } catch (error) {
        console.error('Error creating admin:', error);
        showError(error.message || 'Failed to create admin');
    }
}

async function revokeAdmin(userId) {
    if (!confirm('Revoke admin access for this user?')) return;

    try {
        const response = await makeAuthenticatedRequest(`/api/admin-users/${userId}/revoke`, {
            method: 'PUT'
        });

        if (response.ok) {
            loadAdminUsers();
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Failed to revoke admin access');
        }
    } catch (error) {
        console.error('Error revoking admin:', error);
        showError(error.message || 'Failed to revoke admin access');
    }
}

// API key management (per-admin keys used to credit users from outside the dashboard)
let currentApiKeyAdminId = null;

function openApiKeyModal(adminUserId, adminEmail) {
    currentApiKeyAdminId = adminUserId;
    document.getElementById('api-key-admin-email').textContent = adminEmail;
    document.getElementById('api-key-new-key-box').classList.add('hidden');
    const modal = document.getElementById('api-key-modal');
    modal.classList.remove('hidden');
    modal.style.display = 'flex';
    loadApiKeys();
}

function closeApiKeyModal() {
    currentApiKeyAdminId = null;
    const modal = document.getElementById('api-key-modal');
    modal.classList.add('hidden');
    modal.style.display = 'none';
}

async function loadApiKeys() {
    const body = document.getElementById('api-key-list-body');
    body.innerHTML = 'Loading...';
    try {
        const response = await makeAuthenticatedRequest(`/api/admin-api-keys?adminUserId=${encodeURIComponent(currentApiKeyAdminId)}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const { data } = await response.json();

        if (!data || data.length === 0) {
            body.innerHTML = '<div style="color: #666;">No API keys yet</div>';
            return;
        }

        body.innerHTML = `
            <table>
                <thead>
                    <tr><th>Key</th><th>Created</th><th>Last Used</th><th>Status</th><th></th></tr>
                </thead>
                <tbody>
                    ${data.map(key => `
                        <tr>
                            <td><code>${escapeHtml(key.key_prefix)}&hellip;</code></td>
                            <td>${new Date(key.created_at).toLocaleDateString()}</td>
                            <td>${key.last_used_at ? new Date(key.last_used_at).toLocaleDateString() : 'Never'}</td>
                            <td>${key.revoked_at ? 'Revoked' : 'Active'}</td>
                            <td>${key.revoked_at ? '' : `<button class="btn btn-small btn-danger" onclick="revokeApiKey('${key.id}')">Revoke</button>`}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (error) {
        console.error('Error loading API keys:', error);
        body.innerHTML = '<div style="color: #666;">Failed to load API keys</div>';
    }
}

async function generateApiKey() {
    if (!currentApiKeyAdminId) return;
    try {
        const response = await makeAuthenticatedRequest('/api/admin-api-keys', {
            method: 'POST',
            body: JSON.stringify({ adminUserId: currentApiKeyAdminId })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to generate API key');
        }

        const { key } = await response.json();
        document.getElementById('api-key-new-key-value').value = key;
        document.getElementById('api-key-new-key-box').classList.remove('hidden');
        loadApiKeys();
    } catch (error) {
        console.error('Error generating API key:', error);
        showError(error.message || 'Failed to generate API key');
    }
}

function copyNewApiKey() {
    const input = document.getElementById('api-key-new-key-value');
    input.select();
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(input.value).catch(() => document.execCommand('copy'));
    } else {
        document.execCommand('copy');
    }
}

async function revokeApiKey(keyId) {
    if (!confirm('Revoke this API key? Anything using it will stop working immediately.')) return;
    try {
        const response = await makeAuthenticatedRequest(`/api/admin-api-keys/${keyId}/revoke`, {
            method: 'PUT'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to revoke API key');
        }
        loadApiKeys();
    } catch (error) {
        console.error('Error revoking API key:', error);
        showError(error.message || 'Failed to revoke API key');
    }
}

// Admin activity (credit/plan assignment audit trail) functions
const knownActivityAdmins = new Set();

function formatSignedCredits(value) {
    if (value > 0) return `+${value}`;
    if (value < 0) return `&minus;${Math.abs(value)}`;
    return '0';
}

// "(+40)" / "(−10)" beside the old → new credit values; empty when unchanged or unrecorded
function formatCreditDelta(log) {
    if (log.old_generations_left == null || log.new_generations_left == null) return '';
    const delta = log.new_generations_left - log.old_generations_left;
    if (delta === 0) return '';
    const color = delta > 0 ? 'var(--success)' : 'var(--danger)';
    return ` <span style="color: ${color}; font-weight: 600;">(${formatSignedCredits(delta)})</span>`;
}

let activityDefaultApplied = false;

async function loadActivity() {
    try {
        const filterSelect = document.getElementById('activity-admin-filter');
        const selectedAdmin = filterSelect ? filterSelect.value : '';
        const startDateInput = document.getElementById('activity-start-date');
        const endDateInput = document.getElementById('activity-end-date');
        const startDate = startDateInput ? startDateInput.value : '';
        const endDate = endDateInput ? endDateInput.value : '';

        const params = new URLSearchParams();
        if (selectedAdmin) params.set('adminEmail', selectedAdmin);
        if (startDate) params.set('startDate', startDate);
        if (endDate) params.set('endDate', endDate);
        const query = params.toString();

        const url = '/api/analytics/admin-activity' + (query ? `?${query}` : '');
        const response = await makeAuthenticatedRequest(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        const summary = document.getElementById('admin-credits-summary');
        if (data.leaderboard && data.leaderboard.length > 0) {
            summary.innerHTML = data.leaderboard.map(row => `
                <div class="stat-card">
                    <h3>${escapeHtml(row.admin_email)}${row.isSuperAdmin ? ' ⭐' : ''}</h3>
                    <div class="value">${formatSignedCredits(row.net_credits)}</div>
                    <div style="color: #6c757d; font-size: 0.85rem;">net credits</div>
                    <div style="font-size: 0.85rem; margin-top: 0.25rem;">
                        <span style="color: var(--success);">+${row.total_credits_added} added</span> &middot;
                        <span style="color: var(--danger);">&minus;${row.total_credits_removed} removed</span>
                    </div>
                    <div style="color: #6c757d; font-size: 0.85rem; margin-top: 0.25rem;">${row.total_actions} actions</div>
                    <div style="color: #6c757d; font-size: 0.85rem; margin-top: 0.25rem;">${PLAN_ORDER.map(plan => `${planDisplayName(plan)}: ${(row.plans_added && row.plans_added[plan]) || 0}`).join(' &middot; ')}</div>
                </div>
            `).join('');

        } else {
            summary.innerHTML = '<div class="empty">No assignments yet</div>';
        }

        // Remember every admin seen so the dropdown keeps them all
        data.leaderboard.forEach(row => knownActivityAdmins.add(row.admin_email));
        if (selectedAdmin) knownActivityAdmins.add(selectedAdmin);
        if (filterSelect) {
            filterSelect.innerHTML = '<option value="">All Admins</option>' +
                [...knownActivityAdmins].sort().map(email => `<option value="${escapeHtml(email)}" ${email === selectedAdmin ? 'selected' : ''}>${escapeHtml(email)}</option>`).join('');
        }

        const content = document.getElementById('activity-content');
        const entryCount = data.recentActivity ? data.recentActivity.length : 0;
        document.getElementById('activity-count-label').textContent =
            `${entryCount} ${entryCount === 1 ? 'entry' : 'entries'}${entryCount === 30 ? ' (latest 30)' : ''}`;
        if (entryCount > 0) {
            content.innerHTML = `
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Admin</th>
                                <th>Target User</th>
                                <th>Plan Change</th>
                                <th>Credit Change</th>
                                <th>When</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.recentActivity.map(log => `
                                <tr>
                                    <td>${escapeHtml(log.admin_email) || 'Unknown'}</td>
                                    <td>${escapeHtml(log.target_email) || log.target_user_id}</td>
                                    <td>${escapeHtml(planDisplayName(log.old_plan))} &rarr; ${escapeHtml(planDisplayName(log.new_plan))}</td>
                                    <td>${log.old_generations_left ?? '-'} &rarr; ${log.new_generations_left ?? '-'}${formatCreditDelta(log)}</td>
                                    <td>${log.created_at ? new Date(log.created_at).toLocaleString() : 'N/A'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            content.innerHTML = '<div style="padding: 2rem; text-align: center; color: #666;">No activity recorded yet</div>';
        }
    } catch (error) {
        console.error('Error loading admin activity:', error);
        showError('Failed to load admin activity');
    }
}

function clearActivityFilters() {
    const filterSelect = document.getElementById('activity-admin-filter');
    if (filterSelect) filterSelect.value = '';
    // Reset goes back to the default range, today
    applyActivityPreset('day');
}

// Highlights the preset button matching `preset` (or clears highlighting when null,
// e.g. after the admin edits the date fields by hand and no preset applies anymore)
function setActiveActivityPreset(preset) {
    document.querySelectorAll('.activity-preset-btn').forEach(btn => {
        btn.classList.toggle('active', preset !== null && btn.dataset.preset === preset);
    });
}

// Manual edits to the date fields no longer match any preset's exact range
function onActivityDateInputChange() {
    setActiveActivityPreset(null);
    loadActivity();
}

// Quick date-range chips (1 Day / 1 Week / 1 Month / 3 Months / 1 Year), all ending today
function applyActivityPreset(preset) {
    const end = new Date();
    const start = new Date();

    switch (preset) {
        case 'day':
            break;
        case 'week':
            start.setDate(start.getDate() - 7);
            break;
        case 'month':
            start.setMonth(start.getMonth() - 1);
            break;
        case '3months':
            start.setMonth(start.getMonth() - 3);
            break;
        case 'year':
            start.setFullYear(start.getFullYear() - 1);
            break;
        default:
            return;
    }

    const toDateInputValue = (d) => {
        // Local calendar date, not UTC - toISOString() would shift near midnight
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    const startDateInput = document.getElementById('activity-start-date');
    const endDateInput = document.getElementById('activity-end-date');
    if (startDateInput) startDateInput.value = toDateInputValue(start);
    if (endDateInput) endDateInput.value = toDateInputValue(end);

    setActiveActivityPreset(preset);
    loadActivity();
}

// Ban/unban a profile - any admin can do this, unlike delete which is super-admin only
async function toggleBanProfile(userId, currentlyBanned) {
    let reason = '';
    if (!currentlyBanned) {
        const input = prompt('Reason for banning this profile (optional):');
        if (input === null) return; // cancelled
        reason = input.trim();
    } else if (!confirm('Unban this profile? They will regain access immediately.')) {
        return;
    }

    try {
        const response = await makeAuthenticatedRequest(`/api/profiles/${userId}/ban`, {
            method: 'PUT',
            body: JSON.stringify({ banned: !currentlyBanned, reason })
        });

        if (response.ok) {
            // Also reachable from the Analytics tab's Top Users table
            if (currentTab === 'analytics') {
                loadAnalytics(true);
            } else {
                refreshProfiles();
            }
        } else {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.error || `Failed to ${currentlyBanned ? 'unban' : 'ban'} profile`);
        }
    } catch (error) {
        console.error('Error updating ban status:', error);
        showError(error.message || 'Failed to update ban status');
    }
}

// Delete functions
async function deleteProfile(userId) {
    if (!confirm('Are you sure you want to delete this profile?')) return;
    
    try {
        const response = await makeAuthenticatedRequest(`/api/profiles/${userId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            refreshProfiles();
        } else {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.error || 'Failed to delete profile');
        }
    } catch (error) {
        console.error('Error deleting profile:', error);
        showError(error.message || 'Failed to delete profile');
    }
}

async function deleteJob(jobId) {
    if (!confirm('Are you sure you want to delete this job?')) return;
    
    try {
        const response = await makeAuthenticatedRequest(`/api/jobs/${jobId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            refreshJobs();
        } else {
            throw new Error('Failed to delete job');
        }
    } catch (error) {
        console.error('Error deleting job:', error);
        showError('Failed to delete job');
    }
}

// Modal functions
function closeModal() {

    const modal = document.getElementById('edit-modal');
    modal.classList.add('hidden');
    modal.style.display = 'none';
    editingItem = null;
    editingType = null;
}

// Close modal when clicking outside
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('edit-modal');
    
    // Ensure modal is properly hidden on page load
    modal.classList.add('hidden');
    modal.style.display = 'none';
    
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            closeModal();
        }
    });

    const addAdminModal = document.getElementById('add-admin-modal');
    addAdminModal.classList.add('hidden');
    addAdminModal.style.display = 'none';

    addAdminModal.addEventListener('click', function(e) {
        if (e.target === addAdminModal) {
            closeAddAdminModal();
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !addAdminModal.classList.contains('hidden')) {
            closeAddAdminModal();
        }
    });
});

// Analytics functions
let analyticsDays = 30;
const ANALYTICS_TOP_COUNTRIES = 12;
const ANALYTICS_TOP_COMBOS = 8;
const ANALYTICS_COMBO_COLORS = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1', '#17a2b8', '#fd7e14', '#e83e8c'];
const ANALYTICS_OTHER_COLOR = '#adb5bd';

function setAnalyticsRange(days) {
    analyticsDays = days;
    document.querySelectorAll('.analytics-range-btn').forEach(btn => {
        btn.classList.toggle('active', Number(btn.dataset.days) === days);
    });
    loadAnalytics();
}

async function loadAnalytics(forceRefresh = false) {
    const spinner = document.getElementById('analytics-loading');
    spinner.style.display = 'inline-block';
    try {
        const params = new URLSearchParams({ days: analyticsDays });
        const admin = document.getElementById('analytics-admin-filter').value;
        if (admin) params.set('admin', admin);
        if (forceRefresh) params.set('refresh', '1');
        const response = await makeAuthenticatedRequest(`/api/jobs/stats?${params}`);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `Request failed (${response.status})`);
        }
        renderAnalytics(await response.json());
    } catch (error) {
        console.error('Error loading analytics:', error);
        showError('Failed to load analytics: ' + error.message);
    } finally {
        spinner.style.display = 'none';
    }
}

function formatDocumentType(documentType) {
    return String(documentType || 'unknown')
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

function sumBy(rows, keyFn) {
    const totals = new Map();
    rows.forEach(row => {
        const key = keyFn(row);
        totals.set(key, (totals.get(key) || 0) + row.count);
    });
    return totals;
}

const NO_ADMIN_FILTER = '__none__';

function adminFilterLabel(admin) {
    return admin === NO_ADMIN_FILTER ? 'No Admin (self-serve)' : admin;
}

// Fills the Admin dropdown from the admins found in the credit logs, keeping the current choice
function populateAnalyticsAdminFilter(admins, selected) {
    const select = document.getElementById('analytics-admin-filter');
    select.innerHTML = [
        '<option value="">All Admins</option>',
        ...admins.map(admin => `<option value="${escapeHtml(admin)}">${escapeHtml(admin)}</option>`),
        `<option value="${NO_ADMIN_FILTER}">${adminFilterLabel(NO_ADMIN_FILTER)}</option>`
    ].join('');
    select.value = selected || '';
}

function filterAnalyticsByAdmin(admin) {
    const select = document.getElementById('analytics-admin-filter');
    select.value = select.value === admin ? '' : admin; // clicking the active row clears the filter
    loadAnalytics();
}

function renderAdminBreakdown(breakdown, selected) {
    const container = document.getElementById('analytics-admin-breakdown');
    if (!breakdown.length) {
        container.innerHTML = '<div class="loading">No admin credit logs</div>';
        return;
    }

    container.innerHTML = `
        <table>
            <thead>
                <tr><th>Admin</th><th>Active Users</th><th>Jobs</th><th>Completed</th><th>Failed</th><th>Success Rate</th><th>No-Watermark</th><th>Attempts / No-WM</th></tr>
            </thead>
            <tbody>
                ${breakdown.map(entry => {
                    const finished = entry.completed + entry.failed;
                    const ratio = entry.unwatermarked > 0 ? `${(entry.jobs / entry.unwatermarked).toFixed(1)} : 1` : (entry.jobs ? '∞ (none)' : '-');
                    const active = entry.admin === selected;
                    return `
                    <tr data-admin="${escapeHtml(entry.admin)}" onclick="filterAnalyticsByAdmin(this.dataset.admin)" style="cursor: pointer;${active ? ' background: var(--bg-tertiary); font-weight: 600;' : ''}">
                        <td>${escapeHtml(adminFilterLabel(entry.admin))}${active ? ' ✓' : ''}</td>
                        <td>${entry.users.toLocaleString()}</td>
                        <td>${entry.jobs.toLocaleString()}</td>
                        <td>${entry.completed.toLocaleString()}</td>
                        <td>${entry.failed.toLocaleString()}</td>
                        <td>${finished ? `${((entry.completed / finished) * 100).toFixed(1)}%` : '-'}</td>
                        <td>${entry.unwatermarked.toLocaleString()}</td>
                        <td>${ratio}</td>
                    </tr>`;
                }).join('')}
            </tbody>
        </table>`;
}

function renderAnalytics(data) {
    const rows = data.rows || [];

    // Regular admins get only their own users: no admin picker or cross-admin comparison
    document.querySelectorAll('.analytics-super-only').forEach(el => {
        el.style.display = data.restricted ? 'none' : '';
    });
    const scopeLabel = document.getElementById('analytics-scope-label');
    scopeLabel.style.display = data.restricted ? '' : 'none';
    scopeLabel.textContent = data.restricted ? `Showing users you gave credits to (${data.admin})` : '';
    populateAnalyticsAdminFilter(data.admins || [], data.admin);
    renderAdminBreakdown(data.adminBreakdown || [], data.admin);
    const statusTotals = sumBy(rows, row => row.status);
    const completed = statusTotals.get('completed') || 0;
    const failed = statusTotals.get('failed') || 0;

    document.getElementById('analytics-total').textContent = (data.totalJobs || 0).toLocaleString();
    document.getElementById('analytics-completed').textContent = completed.toLocaleString();
    document.getElementById('analytics-failed').textContent = failed.toLocaleString();
    document.getElementById('analytics-success-rate').textContent =
        completed + failed > 0 ? `${((completed / (completed + failed)) * 100).toFixed(1)}%` : '-';
    document.getElementById('analytics-countries').textContent = new Set(rows.map(row => row.country)).size.toLocaleString();

    // Quadrant: all document types first, then the 3 busiest document types in this range
    const topDocumentTypes = [...sumBy(rows, row => row.document_type).entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([documentType]) => documentType);

    createCountryStatusChart('analytics-quad-0', rows);
    for (let i = 0; i < 3; i++) {
        const documentType = topDocumentTypes[i];
        const card = document.getElementById(`analytics-quad-${i + 1}`).closest('.stat-card');
        card.style.display = documentType ? '' : 'none';
        if (!documentType) continue;
        document.getElementById(`analytics-quad-title-${i + 1}`).textContent = formatDocumentType(documentType);
        createCountryStatusChart(`analytics-quad-${i + 1}`, rows.filter(row => row.document_type === documentType));
    }

    renderJobsByDate(data, rows);
    renderUserSplit(data);
    renderPeakHours(data.hourly || []);
    renderFailureRate(data, rows);

    analyticsUsers = data.users || [];
    analyticsTotalUsers = data.totalUsers || 0;
    analyticsTotalUnwatermarked = data.totalUnwatermarked || 0;
    analyticsTotalJobs = data.totalJobs || 0;
    renderTopUsers();
}

function getAnalyticsThemeColors() {
    const isDark = currentTheme === 'dark';
    return {
        gridColor: isDark ? '#404040' : '#f0f0f0',
        textColor: isDark ? '#e0e0e0' : '#333',
        tint: color => (isDark ? getThemeColor(color) : color)
    };
}

// Horizontal stacked bars: completed + failed per country, busiest countries on top
function createCountryStatusChart(canvasId, rows) {
    const countries = new Map();
    rows.forEach(row => {
        if (row.status !== 'completed' && row.status !== 'failed') return;
        const entry = countries.get(row.country) || { completed: 0, failed: 0 };
        entry[row.status] += row.count;
        countries.set(row.country, entry);
    });

    const top = [...countries.entries()]
        .sort((a, b) => (b[1].completed + b[1].failed) - (a[1].completed + a[1].failed))
        .slice(0, ANALYTICS_TOP_COUNTRIES);

    const { gridColor, textColor, tint } = getAnalyticsThemeColors();

    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }

    charts[canvasId] = new Chart(document.getElementById(canvasId).getContext('2d'), {
        type: 'bar',
        data: {
            labels: top.map(([country]) => country),
            datasets: [
                { label: 'Completed', data: top.map(([, c]) => c.completed), backgroundColor: tint('#28a745') },
                { label: 'Failed', data: top.map(([, c]) => c.failed), backgroundColor: tint('#dc3545') }
            ]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true, position: 'bottom', labels: { font: { size: 10 }, color: textColor } },
                tooltip: {
                    callbacks: {
                        footer: items => {
                            const c = top[items[0].dataIndex][1];
                            const total = c.completed + c.failed;
                            return `Success rate: ${total ? ((c.completed / total) * 100).toFixed(1) : 0}%`;
                        }
                    }
                }
            },
            scales: {
                x: { stacked: true, beginAtZero: true, grid: { color: gridColor }, ticks: { precision: 0, font: { size: 10 }, color: textColor } },
                y: { stacked: true, grid: { display: false }, ticks: { font: { size: 11 }, color: textColor } }
            }
        }
    });
}

// Builds the date buckets for the range: one per day, or one per month for ranges over 90 days
function getAnalyticsBuckets(startDate, days) {
    const byMonth = days > 90;
    const buckets = [];
    const seen = new Set();
    const start = new Date(`${startDate}T00:00:00Z`);
    for (let i = 0; i < days; i++) {
        const date = new Date(start.getTime() + i * 24 * 60 * 60 * 1000);
        const iso = date.toISOString().split('T')[0];
        const key = byMonth ? iso.slice(0, 7) : iso;
        if (seen.has(key)) continue;
        seen.add(key);
        buckets.push({
            key,
            label: date.toLocaleDateString('en-US', byMonth ? { month: 'short', year: 'numeric', timeZone: 'UTC' } : { month: 'short', day: 'numeric', timeZone: 'UTC' })
        });
    }
    return { buckets, bucketOf: date => (byMonth ? date.slice(0, 7) : date) };
}

function renderJobsByDate(data, rows) {
    const { buckets, bucketOf } = getAnalyticsBuckets(data.startDate, data.days);
    const comboOf = row => `${row.country} · ${formatDocumentType(row.document_type)}`;

    const topCombos = [...sumBy(rows, comboOf).entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, ANALYTICS_TOP_COMBOS)
        .map(([combo]) => combo);
    const topComboSet = new Set(topCombos);

    // counts[bucket][combo], plus per-bucket totals for every combo (not just the top ones)
    const counts = new Map(buckets.map(bucket => [bucket.key, new Map()]));
    rows.forEach(row => {
        const bucket = counts.get(bucketOf(row.date));
        if (!bucket) return;
        const combo = comboOf(row);
        bucket.set(combo, (bucket.get(combo) || 0) + row.count);
    });

    const { gridColor, textColor, tint } = getAnalyticsThemeColors();
    const datasets = topCombos.map((combo, i) => ({
        label: combo,
        data: buckets.map(bucket => counts.get(bucket.key).get(combo) || 0),
        backgroundColor: tint(ANALYTICS_COMBO_COLORS[i % ANALYTICS_COMBO_COLORS.length])
    }));
    const otherData = buckets.map(bucket => {
        let other = 0;
        counts.get(bucket.key).forEach((count, combo) => {
            if (!topComboSet.has(combo)) other += count;
        });
        return other;
    });
    if (otherData.some(value => value > 0)) {
        datasets.push({ label: 'Other', data: otherData, backgroundColor: ANALYTICS_OTHER_COLOR });
    }

    const canvasId = 'analytics-by-date';
    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }

    charts[canvasId] = new Chart(document.getElementById(canvasId).getContext('2d'), {
        type: 'bar',
        data: { labels: buckets.map(bucket => bucket.label), datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: true, position: 'bottom', labels: { font: { size: 10 }, color: textColor, boxWidth: 12 } },
                tooltip: {
                    filter: item => item.raw > 0,
                    itemSort: (a, b) => b.raw - a.raw,
                    callbacks: {
                        footer: items => `Total: ${items.reduce((sum, item) => sum + item.raw, 0)}`
                    }
                }
            },
            scales: {
                x: { stacked: true, grid: { display: false }, ticks: { maxTicksLimit: 15, font: { size: 10 }, color: textColor } },
                y: { stacked: true, beginAtZero: true, grid: { color: gridColor }, ticks: { precision: 0, font: { size: 10 }, color: textColor } }
            }
        }
    });

    // Most processed country + document type per date, newest first
    const topRows = buckets.slice().reverse().map(bucket => {
        const bucketCounts = [...counts.get(bucket.key).entries()];
        if (bucketCounts.length === 0) return '';
        const total = bucketCounts.reduce((sum, [, count]) => sum + count, 0);
        const [topCombo, topCount] = bucketCounts.sort((a, b) => b[1] - a[1])[0];
        return `
            <tr>
                <td>${escapeHtml(bucket.label)}</td>
                <td>${escapeHtml(topCombo)}</td>
                <td>${topCount.toLocaleString()}</td>
                <td>${total.toLocaleString()}</td>
                <td>${((topCount / total) * 100).toFixed(0)}%</td>
            </tr>`;
    }).join('');

    document.getElementById('analytics-top-by-date').innerHTML = topRows
        ? `<table>
                <thead><tr><th>Date</th><th>Most Processed</th><th>Jobs</th><th>Total That ${data.days > 90 ? 'Month' : 'Day'}</th><th>Share</th></tr></thead>
                <tbody>${topRows}</tbody>
           </table>`
        : '<div class="loading">No jobs in this range</div>';
}

// Stacked bars of active users per date. Daily distinct users can't be summed into a month
// (one user active on 5 days would count 5 times), so month buckets show the daily average.
function renderUserSplit(data) {
    const { buckets, bucketOf } = getAnalyticsBuckets(data.startDate, data.days);
    const byMonth = data.days > 90;
    const totals = new Map(buckets.map(bucket => [bucket.key, { newUsers: 0, returningUsers: 0 }]));
    (data.dailyUsers || []).forEach(day => {
        const bucket = totals.get(bucketOf(day.date));
        if (!bucket) return;
        bucket.newUsers += day.newUsers;
        bucket.returningUsers += day.returningUsers;
    });

    const daysInBucket = new Map();
    for (let i = 0; i < data.days; i++) {
        const iso = new Date(new Date(`${data.startDate}T00:00:00Z`).getTime() + i * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        daysInBucket.set(bucketOf(iso), (daysInBucket.get(bucketOf(iso)) || 0) + 1);
    }
    const perBucket = (bucket, field) => {
        const value = totals.get(bucket.key)[field];
        return byMonth ? Number((value / daysInBucket.get(bucket.key)).toFixed(1)) : value;
    };

    const newTotal = (data.dailyUsers || []).reduce((sum, day) => sum + day.newUsers, 0);
    document.getElementById('analytics-users-split-subtitle').textContent =
        `${byMonth ? 'Average active users per day, by month' : 'Active users per day'}. New = account created in this range and this is their first job day. ` +
        `${newTotal.toLocaleString()} new users in this range.`;

    const { gridColor, textColor, tint } = getAnalyticsThemeColors();
    const canvasId = 'analytics-users-split';
    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }

    charts[canvasId] = new Chart(document.getElementById(canvasId).getContext('2d'), {
        type: 'bar',
        data: {
            labels: buckets.map(bucket => bucket.label),
            datasets: [
                { label: 'New', data: buckets.map(bucket => perBucket(bucket, 'newUsers')), backgroundColor: tint('#28a745') },
                { label: 'Returning', data: buckets.map(bucket => perBucket(bucket, 'returningUsers')), backgroundColor: tint('#007bff') }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: true, position: 'bottom', labels: { font: { size: 10 }, color: textColor, boxWidth: 12 } },
                tooltip: {
                    callbacks: {
                        footer: items => {
                            const total = items.reduce((sum, item) => sum + item.raw, 0);
                            const newShare = total ? Math.round((items[0].raw / total) * 100) : 0;
                            return `Total: ${byMonth ? total.toFixed(1) : total} (${newShare}% new)`;
                        }
                    }
                }
            },
            scales: {
                x: { stacked: true, grid: { display: false }, ticks: { maxTicksLimit: 15, font: { size: 10 }, color: textColor } },
                y: { stacked: true, beginAtZero: true, grid: { color: gridColor }, ticks: { precision: byMonth ? undefined : 0, font: { size: 10 }, color: textColor } }
            }
        }
    });
}

const HEATMAP_WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const HEATMAP_NUMBERS_KEY = 'adminHeatmapShowNumbers';

// Shows or hides the counts inside the heatmap cells; the choice is remembered per browser
function toggleHeatmapNumbers(show) {
    document.getElementById('analytics-heatmap').classList.toggle('hide-numbers', !show);
    try {
        localStorage.setItem(HEATMAP_NUMBERS_KEY, show ? 'true' : 'false');
    } catch (error) {
        // Storage can be blocked (private mode); the toggle still works for this visit
    }
}

function applySavedHeatmapNumbers() {
    let show = true;
    try {
        show = localStorage.getItem(HEATMAP_NUMBERS_KEY) !== 'false';
    } catch (error) {
        // Fall back to showing numbers
    }
    document.getElementById('analytics-heatmap-numbers').checked = show;
    document.getElementById('analytics-heatmap').classList.toggle('hide-numbers', !show);
}
// Blue -> cyan -> green -> yellow -> orange -> red: quiet hours are cool, busy hours are hot
const HEATMAP_COLOR_STOPS = ['#2c7bb6', '#00a6ca', '#00ccbc', '#90eb9d', '#ffff8c', '#f9d057', '#f29e2e', '#e76818', '#d7191c'];

// Colour for a 0..1 position along HEATMAP_COLOR_STOPS, blending between neighbouring stops
function heatmapColor(position) {
    const scaled = Math.min(Math.max(position, 0), 1) * (HEATMAP_COLOR_STOPS.length - 1);
    const index = Math.min(Math.floor(scaled), HEATMAP_COLOR_STOPS.length - 2);
    const mix = scaled - index;
    const [from, to] = [HEATMAP_COLOR_STOPS[index], HEATMAP_COLOR_STOPS[index + 1]]
        .map(hex => [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16)));
    return `rgb(${from.map((channel, i) => Math.round(channel + (to[i] - channel) * mix)).join(', ')})`;
}

// Weekday x hour grid in the viewer's local time; darker = more jobs
function renderPeakHours(hourly) {
    const grid = Array.from({ length: 7 }, () => new Array(24).fill(0));
    hourly.forEach(({ hour, count }) => {
        const date = new Date(`${hour}:00:00Z`);
        const weekday = (date.getDay() + 6) % 7; // Monday first
        grid[weekday][date.getHours()] += count;
    });

    const max = Math.max(0, ...grid.flat());
    const hourLabel = h => `${String(h).padStart(2, '0')}:00`;

    // One row per hour, one column per weekday, so the grid fills the square card
    const cells = ['<div></div>', ...HEATMAP_WEEKDAYS.map(day => `<div class="hm-label">${day}</div>`)];
    for (let h = 0; h < 24; h++) {
        cells.push(`<div class="hm-label">${hourLabel(h)}</div>`);
        grid.forEach((row, weekday) => {
            const count = row[h];
            // sqrt keeps quieter hours distinguishable next to one very busy peak; empty hours stay grey
            const position = max > 0 ? Math.sqrt(count / max) : 0;
            // White text on the dark blue and red ends; dark text on the light cyan/green/yellow middle
            const textColor = position < 0.12 || position > 0.85 ? '#fff' : '#333';
            const style = count > 0 ? ` style="background: ${heatmapColor(position)}; color: ${textColor};"` : '';
            const label = count === 0 ? '' : count >= 1000 ? `${(count / 1000).toFixed(1)}k` : count;
            cells.push(`<div class="hm-cell" title="${HEATMAP_WEEKDAYS[weekday]} ${hourLabel(h)}–${hourLabel((h + 1) % 24)}: ${count} jobs"${style}>${label}</div>`);
        });
    }
    document.getElementById('analytics-heatmap').innerHTML = cells.join('');
    applySavedHeatmapNumbers();

    document.getElementById('analytics-heatmap-legend').innerHTML = max > 0
        ? `<span>0</span><span>Less</span>
           <div class="hm-legend-bar" style="background: linear-gradient(to right, ${HEATMAP_COLOR_STOPS.join(', ')});"></div>
           <span>More</span><span>${max.toLocaleString()} jobs</span>`
        : '';

    // Busiest slot and busiest hour across all days, for the subtitle
    let peak = { count: 0 };
    grid.forEach((row, weekday) => row.forEach((count, h) => {
        if (count > peak.count) peak = { count, weekday, h };
    }));
    const hourTotals = Array.from({ length: 24 }, (_, h) => grid.reduce((sum, row) => sum + row[h], 0));
    const busiestHour = hourTotals.indexOf(Math.max(...hourTotals));
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

    document.getElementById('analytics-heatmap-subtitle').textContent = peak.count > 0
        ? `Jobs by weekday and hour (${timeZone} time). Busiest: ${HEATMAP_WEEKDAYS[peak.weekday]} ${hourLabel(peak.h)} (${peak.count} jobs); busiest hour overall: ${hourLabel(busiestHour)}–${hourLabel((busiestHour + 1) % 24)}.`
        : `Jobs by weekday and hour (${timeZone} time). No jobs in this range.`;
}

const ANALYTICS_HOTSPOT_MIN_JOBS = 5; // ignore pairs too small for a meaningful rate
const ANALYTICS_HOTSPOT_LIMIT = 10;

function renderFailureRate(data, rows) {
    const { buckets, bucketOf } = getAnalyticsBuckets(data.startDate, data.days);

    // Only finished jobs count; pending/processing ones would drag the rate down
    const finished = rows.filter(row => row.status === 'completed' || row.status === 'failed');
    const perBucket = new Map(buckets.map(bucket => [bucket.key, { completed: 0, failed: 0 }]));
    finished.forEach(row => {
        const bucket = perBucket.get(bucketOf(row.date));
        if (bucket) bucket[row.status] += row.count;
    });

    const { gridColor, textColor, tint } = getAnalyticsThemeColors();
    const failureColor = tint('#dc3545');
    const rates = buckets.map(bucket => {
        const { completed, failed } = perBucket.get(bucket.key);
        // Gap (null) instead of 0% on days with no finished jobs
        return completed + failed > 0 ? Number(((failed / (completed + failed)) * 100).toFixed(1)) : null;
    });

    const canvasId = 'analytics-failure-rate';
    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }

    charts[canvasId] = new Chart(document.getElementById(canvasId).getContext('2d'), {
        type: 'line',
        data: {
            labels: buckets.map(bucket => bucket.label),
            datasets: [{
                label: 'Failure rate',
                data: rates,
                borderColor: failureColor,
                backgroundColor: failureColor + '20',
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 2,
                spanGaps: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: item => `Failure rate: ${item.raw}%`,
                        footer: items => {
                            const { completed, failed } = perBucket.get(buckets[items[0].dataIndex].key);
                            return `${failed} failed / ${completed + failed} finished`;
                        }
                    }
                }
            },
            scales: {
                x: { grid: { display: false }, ticks: { maxTicksLimit: 15, font: { size: 10 }, color: textColor } },
                y: { beginAtZero: true, suggestedMax: 20, grid: { color: gridColor }, ticks: { callback: value => `${value}%`, font: { size: 10 }, color: textColor } }
            }
        }
    });

    // Hotspots: highest failure rate first, ties broken by more failures
    const pairs = new Map();
    finished.forEach(row => {
        const key = `${row.country}|${row.document_type}`;
        const pair = pairs.get(key) || { country: row.country, documentType: row.document_type, completed: 0, failed: 0 };
        pair[row.status] += row.count;
        pairs.set(key, pair);
    });

    const hotspots = [...pairs.values()]
        .filter(pair => pair.failed > 0 && pair.completed + pair.failed >= ANALYTICS_HOTSPOT_MIN_JOBS)
        .map(pair => ({ ...pair, rate: pair.failed / (pair.completed + pair.failed) }))
        .sort((a, b) => b.rate - a.rate || b.failed - a.failed)
        .slice(0, ANALYTICS_HOTSPOT_LIMIT);

    document.getElementById('analytics-failure-hotspots').innerHTML = hotspots.length
        ? `<table>
                <thead><tr><th>Country</th><th>Document Type</th><th>Failed</th><th>Finished</th><th>Failure Rate</th></tr></thead>
                <tbody>${hotspots.map(pair => `
                    <tr>
                        <td>${escapeHtml(pair.country)}</td>
                        <td>${escapeHtml(formatDocumentType(pair.documentType))}</td>
                        <td>${pair.failed.toLocaleString()}</td>
                        <td>${(pair.completed + pair.failed).toLocaleString()}</td>
                        <td style="color: var(--danger); font-weight: 600;">${(pair.rate * 100).toFixed(1)}%</td>
                    </tr>`).join('')}
                </tbody>
           </table>`
        : `<div class="loading">No failure hotspots (pairs with at least ${ANALYTICS_HOTSPOT_MIN_JOBS} finished jobs)</div>`;
}

// Abuse flag: plenty of attempts but few (or no) watermark removals, i.e. regenerating previews without paying
const ABUSE_MIN_ATTEMPTS = 20;
const ABUSE_MAX_RATIO = 10; // attempts per no-watermark job
const TOP_USERS_SHOWN = 50;
let analyticsUsers = [];
let analyticsTotalUsers = 0;
let analyticsTotalUnwatermarked = 0;
let analyticsTotalJobs = 0;

// Attempts per no-watermark job; Infinity when the user never removed a watermark
function attemptsPerUnlock(user) {
    return user.unwatermarked > 0 ? user.attempts / user.unwatermarked : Infinity;
}

function isAbuseFlagged(user) {
    return user.attempts >= ABUSE_MIN_ATTEMPTS && attemptsPerUnlock(user) >= ABUSE_MAX_RATIO;
}

function renderTopUsers() {
    const users = analyticsUsers;
    const flagged = users.filter(isAbuseFlagged);

    // Totals cover every user in range, not just the top ones sent with their profiles
    document.getElementById('analytics-users-active').textContent = analyticsTotalUsers.toLocaleString();
    document.getElementById('analytics-users-unwatermarked').textContent = analyticsTotalUnwatermarked.toLocaleString();
    document.getElementById('analytics-users-ratio').textContent =
        analyticsTotalUnwatermarked > 0 ? `${(analyticsTotalJobs / analyticsTotalUnwatermarked).toFixed(1)} : 1` : '-';
    document.getElementById('analytics-users-flagged').textContent = flagged.length.toLocaleString();
    document.getElementById('analytics-users-subtitle').textContent =
        `Top ${users.length} of ${analyticsTotalUsers} users by attempts. Flagged: ${ABUSE_MIN_ATTEMPTS}+ attempts and ${ABUSE_MAX_RATIO}+ attempts per no-watermark job.`;

    const sortBy = document.getElementById('analytics-users-sort').value;
    const sorters = {
        attempts: (a, b) => b.attempts - a.attempts,
        unwatermarked: (a, b) => b.unwatermarked - a.unwatermarked || b.attempts - a.attempts,
        ratio: (a, b) => attemptsPerUnlock(b) - attemptsPerUnlock(a) || b.attempts - a.attempts,
        flagged: (a, b) => isAbuseFlagged(b) - isAbuseFlagged(a) || b.attempts - a.attempts
    };
    const shown = users.slice().sort(sorters[sortBy] || sorters.attempts).slice(0, TOP_USERS_SHOWN);

    const container = document.getElementById('analytics-top-users');
    if (shown.length === 0) {
        container.innerHTML = '<div class="loading">No jobs in this range</div>';
        return;
    }

    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>User</th><th>Admin</th><th>Plan</th><th>Attempts</th><th>Completed</th><th>Failed</th>
                    <th>No-Watermark</th><th>Attempts / No-WM</th><th>Credits Left</th><th>Last Job</th><th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${shown.map(user => {
                    const ratio = attemptsPerUnlock(user);
                    const flaggedUser = isAbuseFlagged(user);
                    return `
                    <tr${flaggedUser ? ' style="background: rgba(220, 53, 69, 0.08);"' : ''}>
                        <td>
                            ${escapeHtml(user.email || user.user_id)}
                            ${flaggedUser ? '<span title="High attempts with few no-watermark downloads" style="color: var(--danger); font-weight: 600;"> ⚠ Flagged</span>' : ''}
                            ${user.banned ? '<span style="color: var(--text-muted);"> (banned)</span>' : ''}
                        </td>
                        <td>${user.admins && user.admins.length ? user.admins.map(escapeHtml).join('<br>') : '<span style="color: var(--text-muted);">Self-serve</span>'}</td>
                        <td>${user.plan ? getPlanBadge(user.plan) : 'N/A'}</td>
                        <td>${user.attempts.toLocaleString()}</td>
                        <td>${user.completed.toLocaleString()}</td>
                        <td>${user.failed.toLocaleString()}</td>
                        <td>${user.unwatermarked.toLocaleString()}</td>
                        <td style="${flaggedUser ? 'color: var(--danger); font-weight: 600;' : ''}">${ratio === Infinity ? '∞ (none)' : `${ratio.toFixed(1)} : 1`}</td>
                        <td>${user.generations_left ?? 'N/A'}</td>
                        <td>${user.last_job_at ? new Date(user.last_job_at).toLocaleString() : 'N/A'}</td>
                        <td>
                            <button class="btn btn-small ${user.banned ? '' : 'btn-danger'}" onclick="toggleBanProfile('${escapeHtml(user.user_id)}', ${user.banned})">${user.banned ? 'Unban' : 'Ban'}</button>
                        </td>
                    </tr>`;
                }).join('')}
            </tbody>
        </table>`;
}

// Utility functions
function escapeHtml(value) {
    if (value === null || value === undefined) return '';
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function showError(message) {
    // Simple error display - you can enhance this
    alert('Error: ' + message);
}
