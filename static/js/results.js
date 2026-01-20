// ============================================
// Results Page - Progressive Loading
// ============================================

let map;
let markers = [];
let analysisData = { results: [], summary: null };
let eventSource = null;
let isAnalysisComplete = false;
let allResults = [];

document.addEventListener('DOMContentLoaded', function() {
    initializeMap();
    startProgressiveLoading();
    initializeEventHandlers();
});

// ============================================
// Progressive Loading with Server-Sent Events
// ============================================

function startProgressiveLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    console.log('Starting progressive loading for session:', sessionId);
    
    // Connect to SSE endpoint
    eventSource = new EventSource(`/progress/${sessionId}`);
    let messageCount = 0;
    
    console.log('EventSource created, waiting for data...');
    
    eventSource.onopen = function(event) {
        console.log('✓ SSE connection opened successfully');
    };
    
    eventSource.onmessage = function(event) {
        messageCount++;
        console.log(`SSE message #${messageCount} received:`, event.data);
        const data = JSON.parse(event.data);
        
        console.log('Parsed data:', {
            status: data.status,
            progress: data.progress,
            total: data.total,
            resultsCount: data.results?.length || 0
        });
        
        // Always update progress even if waiting
        if (data.status !== 'waiting') {
            updateProgress(data);
        } else {
            console.log('⏳ Waiting for analysis to start...');
        }
        
        if (data.status === 'completed') {
            console.log('✅ Analysis completed successfully via SSE');
            console.log('📊 Final SSE data:', {
                resultsCount: data.results?.length || 0,
                summaryExists: !!data.summary,
                status: data.status
            });
            isAnalysisComplete = true;
            eventSource.close();
            
            // Load final data
            console.log('🔄 About to call loadFinalData()...');
            loadFinalData();
            
            setTimeout(() => {
                loadingOverlay.classList.add('hidden');
                console.log('🎯 Loading overlay hidden');
            }, 1000);
        } else if (data.status === 'error') {
            console.error('❌ Analysis error:', data.error);
            eventSource.close();
            showError(data.error || 'An error occurred during analysis');
            loadingOverlay.classList.add('hidden');
        }
    };
    
    eventSource.onerror = function(error) {
        console.error('❌ SSE Error:', error);
        console.log('SSE readyState:', eventSource.readyState);
        console.log('Messages received before error:', messageCount);
        eventSource.close();
        
        // Fallback to polling if SSE fails
        console.log('⚠️ Switching to polling fallback');
        startPolling();
    };
    
    // Timeout check after 5 seconds
    setTimeout(() => {
        if (messageCount === 0) {
            console.error('⚠️ No SSE messages received after 5 seconds - switching to polling');
            if (eventSource && eventSource.readyState !== EventSource.CLOSED) {
                eventSource.close();
                startPolling();
            }
        }
    }, 5000);
}

function updateProgress(data) {
    if (!data) return;

    // Update progress display
    const processedCntEl = document.getElementById('processedCount');
    const totalCntEl = document.getElementById('totalCount');
    const progressPctEl = document.getElementById('progressPercent');
    const progressFillEl = document.getElementById('loadingProgress');

    if (processedCntEl) processedCntEl.textContent = data.progress || 0;
    if (totalCntEl) totalCntEl.textContent = data.total || 0;
    
    const percent = data.total > 0 ? Math.round((data.progress / data.total) * 100) : 0;
    if (progressPctEl) progressPctEl.textContent = percent + '%';
    if (progressFillEl) progressFillEl.style.width = percent + '%';
    
    // Update results as they come
    if (data.results && data.results.length > 0) {
        // Only append NEW results (crucial for polling which might send full list)
        const newResults = [];
        data.results.forEach(result => {
            const exists = allResults.find(r => 
                r.gov_bemis_code === result.gov_bemis_code && 
                r.gov_school_name === result.gov_school_name &&
                r.custom_school_name === result.custom_school_name
            );
            if (!exists) {
                allResults.push(result);
                newResults.push(result);
            }
        });
        
        // Update display incrementally with ONLY new results
        if (newResults.length > 0) {
            updateTableWithResults(newResults);
            updateMapWithResults(newResults);
        }
    }
    
    // Update summary if available
    if (data.summary) {
        updateSummaryStats(data.summary);
        analysisData.summary = data.summary;
    }
}

function startPolling() {
    console.log('🔄 Starting polling fallback for session:', sessionId);
    
    const pollInterval = setInterval(async () => {
        // Stop if analysis was completed via SSE while we were starting poll
        if (isAnalysisComplete) {
            console.log('🛑 Polling stopped: Analysis already marked complete');
            clearInterval(pollInterval);
            return;
        }

        try {
            // Cache-busting URL
            const response = await fetch(`/api/session/${sessionId}?t=${Date.now()}`);
            const data = await response.json();
            
            console.log('📡 Poll response:', { status: data.status, progress: data.progress, total: data.total, hasResults: !!(data.results && data.results.length) });
            
            if (data.status === 'completed') {
                console.log('✅ COMPLETION DETECTED! Stopping poll and loading final data...');
                clearInterval(pollInterval);
                isAnalysisComplete = true;
                
                try {
                    console.log('📊 Calling loadFinalData()...');
                    await loadFinalData();
                    console.log('📊 loadFinalData() completed successfully');
                } catch (loadError) {
                    console.error('❌ Error in loadFinalData:', loadError);
                }
                
                const overlay = document.getElementById('loadingOverlay');
                if (overlay) {
                    overlay.classList.add('hidden');
                    overlay.style.display = 'none';
                    console.log('🎯 Loading overlay hidden');
                }
                return; // Exit polling
            } else if (data.status === 'error') {
                clearInterval(pollInterval);
                console.error('❌ Analysis failed:', data.error);
                showError(data.error);
                const overlay = document.getElementById('loadingOverlay');
                if (overlay) {
                    overlay.classList.add('hidden');
                    overlay.style.display = 'none';
                }
                return;
            } else {
                // Update progress for active analysis
                updateProgress(data);
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 2000); // 2 second interval
}

async function loadFinalData() {
    console.log('📊 Loading final data for session:', sessionId);
    try {
        // Try to load from API first
        const response = await fetch(`/api/results/${sessionId}`);
        console.log('📊 Final data response status:', response.status, 'type:', response.headers.get('content-type'));
        
        if (!response.ok) {
            console.error('❌ API returned error status:', response.status);
            // Try fallback: download the JSON file directly
            console.log('📥 Trying fallback: loading from JSON file...');
            return await loadFromJsonFile();
        }
        
        // Get response as text first to check for issues
        const responseText = await response.text();
        console.log('📊 Response text length:', responseText.length, 'chars');
        console.log('📊 First 200 chars:', responseText.substring(0, 200));
        
        // Try to parse JSON
        let data;
        try {
            data = JSON.parse(responseText);
            console.log('✅ JSON parsed successfully');
        } catch (parseError) {
            console.error('❌ JSON Parse Error:', parseError.message);
            console.error('📄 Response preview (first 500 chars):', responseText.substring(0, 500));
            console.error('📄 Response preview (last 500 chars):', responseText.substring(responseText.length - 500));
            
            // Try fallback: download the JSON file directly
            console.log('📥 Trying fallback: loading from JSON file...');
            return await loadFromJsonFile();
        }
        
        console.log('📊 Final data loaded:', {
            resultsCount: data.results?.length || 0,
            summaryExists: !!data.summary,
            firstResult: data.results?.[0]
        });
        
        analysisData = data;
        allResults = data.results;
        
        // Update all displays with final data
        updateSummaryStats(data.summary);
        renderCompleteTable(data.results);
        renderCompleteMap(data.results);
        initializeCharts(data.summary);
        
        // Enable downloads
        const downloadBtn = document.getElementById('downloadExcelBtn');
        if (downloadBtn) {
            downloadBtn.disabled = false;
        }
        
        console.log('✅ Final data display completed');
    } catch (error) {
        console.error('❌ Error loading final data:', error);
        showError('Failed to load analysis results: ' + error.message);
    }
}

async function loadFromJsonFile() {
    console.log('📥 Loading data from JSON file as fallback...');
    try {
        const response = await fetch(`/download/${sessionId}/json`);
        if (!response.ok) {
            throw new Error(`Failed to download JSON file: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ JSON file loaded successfully:', {
            resultsCount: data.results?.length || 0,
            summaryExists: !!data.summary
        });
        
        analysisData = data;
        allResults = data.results;
        
        // Update all displays with final data
        updateSummaryStats(data.summary);
        renderCompleteTable(data.results);
        renderCompleteMap(data.results);
        initializeCharts(data.summary);
        
        // Enable downloads
        const downloadBtn = document.getElementById('downloadExcelBtn');
        if (downloadBtn) {
            downloadBtn.disabled = false;
        }
        
        console.log('✅ Final data display completed from JSON file');
    } catch (error) {
        console.error('❌ Fallback also failed:', error);
        throw error;
    }
}

// ============================================
// Update Summary Statistics
// ============================================

function updateSummaryStats(summary) {
    if (!summary) return;
    
    document.getElementById('totalRows').textContent = summary.total_rows || 0;
    document.getElementById('totalGovSchools').textContent = summary.total_gov_schools || 0;
    document.getElementById('totalCustomSchools').textContent = summary.total_custom_schools_found || 0;
    document.getElementById('avgDistance').textContent = (summary.avg_distance || 0) + ' km';
    
    // Update average distances by source type
    document.getElementById('avgBEACDistance').textContent = (summary.avg_beac_distance || 0) + ' km';
    document.getElementById('avgNCHDDistance').textContent = (summary.avg_nchd_distance || 0) + ' km';
    document.getElementById('avgBEFDistance').textContent = (summary.avg_bef_distance || 0) + ' km';
}

// ============================================
// Table Updates
// ============================================

function updateTableWithResults(results) {
    const tbody = document.getElementById('resultsTableBody');
    
    results.forEach((result, index) => {
        const row = createTableRow(result, allResults.length - results.length + index);
        tbody.appendChild(row);
    });
}

function renderCompleteTable(results) {
    const tbody = document.getElementById('resultsTableBody');
    tbody.innerHTML = ''; // Clear existing
    
    results.forEach((result, index) => {
        const row = createTableRow(result, index);
        tbody.appendChild(row);
    });
    
    // Initialize table functionality
    initializeTable();
}

function createTableRow(result, index) {
    const row = document.createElement('tr');
    row.setAttribute('data-index', index);
    row.setAttribute('data-source', result.custom_source || '');
    
    // Add badge color based on source (handle all variations)
    const sourceColors = {
        'BEAC': 'badge-beac',
        'NCHD': 'badge-nchd',
        'BEF': 'badge-bef'
    };
    const badgeClass = sourceColors[result.custom_source] || 'badge-none';
    
    row.innerHTML = `
        <td class="school-name">${result.gov_school_name || 'N/A'}</td>
        <td>${result.gov_bemis_code || 'N/A'}</td>
        <td>${result.gov_district || 'N/A'}</td>
        <td>${result.gov_level || 'N/A'}</td>
        <td>${result.gov_enrollment || 'N/A'}</td>
        <td class="school-name">${result.custom_school_name || 'N/A'}</td>
        <td><span class="badge ${badgeClass}">${result.custom_source || 'N/A'}</span></td>
        <td>${result.custom_level || 'N/A'}</td>
        <td class="distance">${result.distance_km ? result.distance_km + ' km' : 'N/A'}</td>
    `;
    
    return row;
}

// ============================================
// Map Updates
// ============================================

function initializeMap() {
    map = L.map('map').setView([29.0, 67.0], 7);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
}

function updateMapWithResults(results) {
    results.forEach(result => {
        if (result.gov_latitude && result.gov_longitude) {
            addMarkerToMap(result);
        }
    });
    
    // Fit bounds if we have markers
    if (markers.length > 0) {
        const group = new L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

function renderCompleteMap(results) {
    // Clear existing markers
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
    
    // Create distinct icons
    const govIcon = createCustomIcon('#14b8a6', 'fa-school');
    const beacIcon = createCustomIcon('#3b82f6', 'fa-graduation-cap');
    const nchdIcon = createCustomIcon('#8b5cf6', 'fa-university');
    const befIcon = createCustomIcon('#ec4899', 'fa-building');
    
    // Track unique government schools and custom schools
    const govSchools = new Map();
    const customSchools = new Map();
    
    // Collect unique schools
    results.forEach(result => {
        // Add government school - validate coordinates are numbers, not 'N/A'
        if (result.gov_latitude && result.gov_longitude && 
            typeof result.gov_latitude === 'number' && typeof result.gov_longitude === 'number' &&
            !isNaN(result.gov_latitude) && !isNaN(result.gov_longitude)) {
            const govKey = `${result.gov_latitude},${result.gov_longitude}`;
            if (!govSchools.has(govKey)) {
                govSchools.set(govKey, result);
            }
        }
        
        // Add custom school - validate coordinates are numbers, not 'N/A'
        if (result.custom_latitude && result.custom_longitude &&
            typeof result.custom_latitude === 'number' && typeof result.custom_longitude === 'number' &&
            !isNaN(result.custom_latitude) && !isNaN(result.custom_longitude)) {
            const customKey = `${result.custom_latitude},${result.custom_longitude}`;
            if (!customSchools.has(customKey)) {
                customSchools.set(customKey, {
                    latitude: result.custom_latitude,
                    longitude: result.custom_longitude,
                    school_name: result.custom_school_name,
                    district: result.custom_district,
                    tehsil: result.custom_tehsil,
                    source: result.custom_source,
                    level: result.custom_level
                });
            }
        }
    });
    
    // Plot government schools - double-check coordinates before plotting
    govSchools.forEach(result => {
        if (result.gov_latitude && result.gov_longitude &&
            typeof result.gov_latitude === 'number' && typeof result.gov_longitude === 'number') {
            const marker = L.marker([result.gov_latitude, result.gov_longitude], { icon: govIcon })
                .bindPopup(createGovSchoolPopup(result))
                .addTo(map);
            markers.push(marker);
        }
    });
    
    // Plot custom schools with appropriate icons based on source type
    customSchools.forEach(school => {
        // Assign icons: BEAC -> blue, NCHD -> purple, BEF -> pink
        let icon;
        if (school.source === 'BEAC') {
            icon = beacIcon;
        } else if (school.source === 'NCHD') {
            icon = nchdIcon;
        } else {
            icon = befIcon;  // BEF and any other source
        }
        
        const marker = L.marker([school.latitude, school.longitude], { icon })
            .bindPopup(createCustomSchoolPopup(school))
            .addTo(map);
        markers.push(marker);
    });
    
    // Fit bounds
    if (markers.length > 0) {
        const group = new L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

function addMarkerToMap(result) {
    const icon = createCustomIcon('#14b8a6', 'fa-school');
    const marker = L.marker([result.gov_latitude, result.gov_longitude], { icon })
        .bindPopup(createGovSchoolPopup(result))
        .addTo(map);
    markers.push(marker);
}

function createCustomIcon(color, iconClass = 'fa-circle') {
    return L.divIcon({
        className: 'custom-marker',
        html: `<div style="background-color: ${color}; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center;">
                 <i class="fas ${iconClass}" style="color: white; font-size: 14px;"></i>
               </div>`,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });
}

function createGovSchoolPopup(result) {
    return `
        <div style="min-width: 200px;">
            <h3 style="margin: 0 0 10px 0; color: #14b8a6; font-size: 1rem;">
                <i class="fas fa-school"></i> Government School
            </h3>
            <p style="margin: 5px 0;"><strong>Name:</strong> ${result.gov_school_name}</p>
            <p style="margin: 5px 0;"><strong>District:</strong> ${result.gov_district}</p>
            <p style="margin: 5px 0;"><strong>Tehsil:</strong> ${result.gov_tehsil}</p>
            <p style="margin: 5px 0;"><strong>Level:</strong> ${result.gov_level}</p>
            <p style="margin: 5px 0;"><strong>Enrollment:</strong> ${result.gov_enrollment}</p>
            <hr style="margin: 10px 0;">
            <p style="margin: 5px 0;"><strong>Nearest Type:</strong> 
                <span style="color: ${result.nearest_overall_type === 'BEAC' ? '#3b82f6' : result.nearest_overall_type === 'NCHD' ? '#8b5cf6' : '#ec4899'};">
                    ${result.nearest_overall_type || 'N/A'}
                </span>
            </p>
            <p style="margin: 5px 0;"><strong>Distance:</strong> ${result.nearest_overall_distance || 'N/A'} km</p>
        </div>
    `;
}

function createSpecialSchoolPopup(school, type) {
    const color = type === 'BEAC' ? '#3b82f6' : type === 'NCHD' ? '#8b5cf6' : '#ec4899';
    return `
        <div style="min-width: 200px;">
            <h3 style="margin: 0 0 10px 0; color: ${color}; font-size: 1rem;">
                <i class="fas fa-graduation-cap"></i> ${type} School
            </h3>
            <p style="margin: 5px 0;"><strong>Name:</strong> ${school.school_name}</p>
            <p style="margin: 5px 0;"><strong>District:</strong> ${school.district}</p>
            <p style="margin: 5px 0;"><strong>Tehsil:</strong> ${school.tehsil}</p>
        </div>
    `;
}

function createCustomSchoolPopup(school) {
    const colors = {
        'BEAC': '#3b82f6',
        'NCHD': '#8b5cf6',
        'BEF': '#ec4899'
    };
    const icons = {
        'BEAC': 'fa-graduation-cap',
        'NCHD': 'fa-university',
        'BEF': 'fa-building'
    };
    const color = colors[school.source] || '#999';
    const icon = icons[school.source] || 'fa-school';
    
    return `
        <div style="min-width: 200px;">
            <h3 style="margin: 0 0 10px 0; color: ${color}; font-size: 1rem;">
                <i class="fas ${icon}"></i> ${school.source} School
            </h3>
            <p style="margin: 5px 0;"><strong>Name:</strong> ${school.school_name || 'N/A'}</p>
            <p style="margin: 5px 0;"><strong>District:</strong> ${school.district || 'N/A'}</p>
            <p style="margin: 5px 0;"><strong>Tehsil:</strong> ${school.tehsil || 'N/A'}</p>
            <p style="margin: 5px 0;"><strong>Level:</strong> ${school.level || 'N/A'}</p>
        </div>
    `;
}

// ============================================
// Charts Initialization
// ============================================

function initializeCharts(summary) {
    if (!summary) return;
    
    createDistanceRangeChart(summary);
    createTypeDistributionChart(summary);
}

function createDistanceRangeChart(summary) {
    const ctx = document.getElementById('distanceRangeChart');
    if (!ctx) return;
    
    new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['0-2 km', '2-5 km', '5-10 km', '10+ km'],
            datasets: [
                {
                    label: 'BEAC Schools',
                    data: [
                        summary.beac_distance_ranges['0-2km'],
                        summary.beac_distance_ranges['2-5km'],
                        summary.beac_distance_ranges['5-10km'],
                        summary.beac_distance_ranges['10+km']
                    ],
                    backgroundColor: 'rgba(59, 130, 246, 0.7)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1
                },
                {
                    label: 'NCHD Schools',
                    data: [
                        summary.nchd_distance_ranges['0-2km'],
                        summary.nchd_distance_ranges['2-5km'],
                        summary.nchd_distance_ranges['5-10km'],
                        summary.nchd_distance_ranges['10+km']
                    ],
                    backgroundColor: 'rgba(139, 92, 246, 0.7)',
                    borderColor: 'rgba(139, 92, 246, 1)',
                    borderWidth: 1
                },
                {
                    label: 'BEF Schools',
                    data: [
                        summary.bef_distance_ranges['0-2km'],
                        summary.bef_distance_ranges['2-5km'],
                        summary.bef_distance_ranges['5-10km'],
                        summary.bef_distance_ranges['10+km']
                    ],
                    backgroundColor: 'rgba(236, 72, 153, 0.7)',
                    borderColor: 'rgba(236, 72, 153, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Distance Range Distribution',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Schools'
                    }
                }
            }
        }
    });
}

function createTypeDistributionChart(summary) {
    const ctx = document.getElementById('typeDistributionChart');
    if (!ctx) return;
    
    new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: ['Nearest to BEAC', 'Nearest to NCHD', 'Nearest to BEF'],
            datasets: [{
                data: [
                    summary.nearest_beac_count,
                    summary.nearest_nchd_count,
                    summary.nearest_bef_count
                ],
                backgroundColor: [
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(139, 92, 246, 0.8)',
                    'rgba(236, 72, 153, 0.8)'
                ],
                borderColor: [
                    'rgba(59, 130, 246, 1)',
                    'rgba(139, 92, 246, 1)',
                    'rgba(236, 72, 153, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Nearest School Type Distribution',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// ============================================
// Table Functionality
// ============================================

function initializeTable() {
    const searchInput = document.getElementById('searchInput');
    const filterType = document.getElementById('filterType');
    
    if (searchInput) {
        searchInput.addEventListener('input', filterTable);
    }
    
    if (filterType) {
        filterType.addEventListener('change', filterTable);
    }
}

function filterTable() {
    const searchValue = document.getElementById('searchInput').value.toLowerCase();
    const filterValue = document.getElementById('filterType').value;
    const rows = document.querySelectorAll('#resultsTableBody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const source = row.getAttribute('data-source');
        
        const matchesSearch = text.includes(searchValue);
        const matchesFilter = !filterValue || source === filterValue;
        
        if (matchesSearch && matchesFilter) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// ============================================
// Event Handlers
// ============================================

function initializeEventHandlers() {
    // Download Excel button
    const downloadExcelBtn = document.getElementById('downloadExcelBtn');
    if (downloadExcelBtn) {
        downloadExcelBtn.addEventListener('click', downloadExcel);
    }
    
    // Download Map button
    const downloadMapBtn = document.getElementById('downloadMapBtn');
    if (downloadMapBtn) {
        downloadMapBtn.addEventListener('click', downloadMap);
    }
    
    // Modal close button
    const modalClose = document.querySelector('.modal-close');
    if (modalClose) {
        modalClose.addEventListener('click', closeModal);
    }
    
    // Close modal on outside click
    const modal = document.getElementById('detailsModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal();
            }
        });
    }
}

function downloadExcel() {
    window.location.href = `/download/${sessionId}/excel`;
}

function downloadMap() {
    const mapHTML = `
<!DOCTYPE html>
<html>
<head>
    <title>Schools Distance Map</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { margin: 0; padding: 0; }
        #map { height: 100vh; width: 100%; }
        .legend {
            position: absolute;
            top: 10px;
            right: 10px;
            background: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 1000;
        }
        .legend-item {
            display: flex;
            align-items: center;
            margin: 5px 0;
        }
        .legend-marker {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            margin-right: 8px;
            border: 2px solid white;
        }
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="legend">
        <h4 style="margin: 0 0 10px 0;">Legend</h4>
        <div class="legend-item">
            <div class="legend-marker" style="background: #14b8a6;"></div>
            <span>Government Schools</span>
        </div>
        <div class="legend-item">
            <div class="legend-marker" style="background: #3b82f6;"></div>
            <span>BEAC Schools</span>
        </div>
        <div class="legend-item">
            <div class="legend-marker" style="background: #8b5cf6;"></div>
            <span>NCHD Schools</span>
        </div>
        <div class="legend-item">
            <div class="legend-marker" style="background: #ec4899;"></div>
            <span>BEF Schools</span>
        </div>
    </div>
    <script>
        const data = ${JSON.stringify(analysisData)};
        const map = L.map('map').setView([29.0, 67.0], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        
        const markers = [];
        
        data.results.forEach(result => {
            if (result.gov_latitude && result.gov_longitude) {
                const marker = L.circleMarker([result.gov_latitude, result.gov_longitude], {
                    radius: 6,
                    fillColor: '#14b8a6',
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                }).bindPopup('<strong>' + result.gov_school_name + '</strong><br>District: ' + result.gov_district).addTo(map);
                markers.push(marker);
            }
        });
        
        if (markers.length > 0) {
            const group = new L.featureGroup(markers);
            map.fitBounds(group.getBounds().pad(0.1));
        }
    </script>
</body>
</html>
    `;
    
    const blob = new Blob([mapHTML], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'schools_distance_map.html';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function showDetailsModal(result) {
    const modal = document.getElementById('detailsModal');
    const modalBody = document.getElementById('modalBody');
    
    // Format lists of schools within 5km
    const beacSchools = result.beac_within_5km || [];
    const nchdSchools = result.nchd_within_5km || [];
    const befSchools = result.bef_within_5km || [];
    
    const formatSchoolList = (schools, type, color) => {
        if (schools.length === 0) {
            return `<p style="color: #999; font-style: italic;">No ${type} schools within 5km</p>`;
        }
        return `
            <h4 style="margin-bottom: 15px; color: ${color};">
                ${schools.length} School${schools.length !== 1 ? 's' : ''} Within 5km
            </h4>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <thead>
                    <tr style="background: #f8f9fa;">
                        <th style="padding: 10px; text-align: left; border: 1px solid #dee2e6;">School Name</th>
                        <th style="padding: 10px; text-align: left; border: 1px solid #dee2e6;">Distance</th>
                        <th style="padding: 10px; text-align: left; border: 1px solid #dee2e6;">District</th>
                        <th style="padding: 10px; text-align: left; border: 1px solid #dee2e6;">Tehsil</th>
                    </tr>
                </thead>
                <tbody>
                    ${schools.map(school => `
                        <tr>
                            <td style="padding: 10px; border: 1px solid #dee2e6;">${school.name || 'N/A'}</td>
                            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong style="color: ${color};">${school.distance} km</strong></td>
                            <td style="padding: 10px; border: 1px solid #dee2e6;">${school.district || 'N/A'}</td>
                            <td style="padding: 10px; border: 1px solid #dee2e6;">${school.tehsil || 'N/A'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    };
    
    let detailsHTML = `
        <div class="detail-section">
            <h3><i class="fas fa-school"></i> Government School Information</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">School Name</div>
                    <div class="detail-value">${result.gov_school_name}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">BemisCode</div>
                    <div class="detail-value">${result.gov_bemis_code || 'N/A'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">District</div>
                    <div class="detail-value">${result.gov_district}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Tehsil</div>
                    <div class="detail-value">${result.gov_tehsil}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">UC</div>
                    <div class="detail-value">${result.gov_uc || 'N/A'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Level</div>
                    <div class="detail-value">${result.gov_level}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Gender</div>
                    <div class="detail-value">${result.gov_gender || 'N/A'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Enrollment</div>
                    <div class="detail-value">${result.gov_enrollment}</div>
                </div>
            </div>
        </div>

        <div class="detail-section">
            <h3><i class="fas fa-map-marker-alt"></i> Nearest School Overall</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">Type</div>
                    <div class="detail-value">
                        <span class="badge badge-${(result.nearest_overall_type || '').toLowerCase()}">
                            ${result.nearest_overall_type || 'None'}
                        </span>
                    </div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Distance</div>
                    <div class="detail-value" style="font-weight: 700;">${result.nearest_overall_distance || 'N/A'} km</div>
                </div>
            </div>
        </div>
    `;
    
    if (beacSchools.length > 0) {
        detailsHTML += `
            <div class="detail-section">
                <h3><i class="fas fa-building"></i> BEAC Schools</h3>
                ${formatSchoolList(beacSchools, 'BEAC', '#3b82f6')}
            </div>
        `;
    }
    
    if (nchdSchools.length > 0) {
        detailsHTML += `
            <div class="detail-section">
                <h3><i class="fas fa-university"></i> NCHD Schools</h3>
                ${formatSchoolList(nchdSchools, 'NCHD', '#8b5cf6')}
            </div>
        `;
    }
    
    if (befSchools.length > 0) {
        detailsHTML += `
            <div class="detail-section">
                <h3><i class="fas fa-graduation-cap"></i> BEF Schools</h3>
                ${formatSchoolList(befSchools, 'BEF', '#ec4899')}
            </div>
        `;
    }
    
    modalBody.innerHTML = detailsHTML;
    modal.classList.add('active');
}

function closeModal() {
    const modal = document.getElementById('detailsModal');
    modal.classList.remove('active');
}

function showError(message) {
    alert('Error: ' + message);
}

// Keyboard shortcut for closing modal
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
});
