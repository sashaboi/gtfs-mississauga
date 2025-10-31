// Global variables
let map;
let busMarkers = [];
let autoRefreshInterval;
let currentTab = 'live';
let highlightedBuses = new Set();
let userLocation = null;
let userLocationMarker = null;
let allStops = [];
let allRoutes = [];
let selectedStopIndex = -1;

// Initialize map
function initMap() {
    // Center on Mississauga
    map = L.map('map').setView([43.5890, -79.6441], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    console.log('Map initialized');
}

// Set/update user location marker
function setUserLocation(lat, lon) {
    // Remove old marker if exists
    if (userLocationMarker) {
        map.removeLayer(userLocationMarker);
    }

    // Add new marker
    userLocationMarker = L.marker([lat, lon], {
        icon: L.divIcon({
            className: 'user-marker',
            html: '<div style="font-size: 24px;">📍</div>',
            iconSize: [30, 30],
            iconAnchor: [15, 30]
        }),
        zIndexOffset: 1000 // Keep on top
    }).addTo(map).bindPopup('📍 You are here');

    userLocation = { lat, lon };
}

// Switch between tabs
function switchTab(tab) {
    currentTab = tab;

    // Update tab buttons
    document.querySelectorAll('.sidebar-tab').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // Update tab content
    if (tab === 'planner') {
        document.getElementById('plannerTab').style.display = 'block';
        document.getElementById('liveTab').style.display = 'none';
        clearBusMarkers();
    } else if (tab === 'live') {
        document.getElementById('plannerTab').style.display = 'none';
        document.getElementById('liveTab').style.display = 'block';
        loadRoutes();
        loadVehicles();
        loadAlerts();
        startAutoRefresh();
    }
}

// Load stops into memory
async function loadStops() {
    try {
        const response = await fetch('/api/stops');
        allStops = await response.json();
        console.log(`Loaded ${allStops.length} stops`);

        // Set up autocomplete
        setupAutocomplete('source');
        setupAutocomplete('destination');
    } catch (error) {
        console.error('Error loading stops:', error);
    }
}

// Setup autocomplete for a field
function setupAutocomplete(field) {
    const searchInput = document.getElementById(`${field}Search`);
    const resultsDiv = document.getElementById(`${field}Results`);
    const hiddenInput = document.getElementById(field);
    const clearBtn = searchInput.nextElementSibling;

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim().toLowerCase();

        if (query.length < 2) {
            resultsDiv.classList.remove('show');
            clearBtn.classList.remove('show');
            return;
        }

        clearBtn.classList.add('show');

        // Filter stops
        const matches = allStops.filter(stop => {
            const name = (stop.name || '').toLowerCase();
            const id = (stop.id || '').toString();

            return name.includes(query) || id.includes(query);
        }).slice(0, 10); // Limit to 10 results

        if (matches.length > 0) {
            displayAutocompleteResults(field, matches);
        } else {
            resultsDiv.innerHTML = '<div class="autocomplete-item">No stops found</div>';
            resultsDiv.classList.add('show');
        }
    });

    // Handle keyboard navigation
    searchInput.addEventListener('keydown', (e) => {
        const items = resultsDiv.querySelectorAll('.autocomplete-item');

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedStopIndex = Math.min(selectedStopIndex + 1, items.length - 1);
            updateSelection(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedStopIndex = Math.max(selectedStopIndex - 1, 0);
            updateSelection(items);
        } else if (e.key === 'Enter' && selectedStopIndex >= 0) {
            e.preventDefault();
            items[selectedStopIndex].click();
        } else if (e.key === 'Escape') {
            resultsDiv.classList.remove('show');
        }
    });

    // Close on click outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !resultsDiv.contains(e.target)) {
            resultsDiv.classList.remove('show');
        }
    });
}

function displayAutocompleteResults(field, stops) {
    const resultsDiv = document.getElementById(`${field}Results`);

    resultsDiv.innerHTML = stops.map((stop, index) => `
        <div class="autocomplete-item" data-stop-id="${stop.id}" data-stop-name="${stop.name}" 
             onclick="selectStop('${field}', '${stop.id}', '${stop.name.replace(/'/g, "\\'")}')">
            <strong>${stop.name}</strong><br>
            <small style="color: #999;">Stop ID: ${stop.id}</small>
        </div>
    `).join('');

    resultsDiv.classList.add('show');
    selectedStopIndex = -1;
}

function updateSelection(items) {
    items.forEach((item, index) => {
        item.classList.toggle('selected', index === selectedStopIndex);
    });
    if (selectedStopIndex >= 0) {
        items[selectedStopIndex].scrollIntoView({ block: 'nearest' });
    }
}

function selectStop(field, stopId, stopName) {
    document.getElementById(`${field}Search`).value = stopName;
    document.getElementById(field).value = stopId;
    document.getElementById(`${field}Results`).classList.remove('show');
    document.getElementById(`${field}Search`).nextElementSibling.classList.add('show');
}

function clearSearch(field) {
    document.getElementById(`${field}Search`).value = '';
    document.getElementById(field).value = '';
    document.getElementById(`${field}Results`).classList.remove('show');
    document.getElementById(`${field}Search`).nextElementSibling.classList.remove('show');
    document.getElementById(`${field}Search`).focus();
}

// Find nearby stops
async function findNearbyStops(field) {
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = '📍 Getting location...';

    if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser');
        btn.disabled = false;
        btn.textContent = '📍 Use My Location';
        return;
    }

    navigator.geolocation.getCurrentPosition(
        async (position) => {
            userLocation = {
                lat: position.coords.latitude,
                lon: position.coords.longitude
            };

            try {
                const response = await fetch(`/api/nearby-stops?lat=${userLocation.lat}&lon=${userLocation.lon}&limit=10`);
                const data = await response.json();
                const stops = data.stops || data; // Handle both formats

                if (stops.length > 0) {
                    // Show nearby stops in autocomplete
                    displayAutocompleteResults(field, stops.map(stop => ({
                        ...stop,
                        name: `${stop.name} (${stop.distance.toFixed(2)} km)`
                    })));

                    // Auto-select the closest one
                    selectStop(field, stops[0].id, stops[0].name);
                }

                btn.textContent = '✅ Location found';
                setTimeout(() => {
                    btn.textContent = '📍 Use My Location';
                    btn.disabled = false;
                }, 2000);

            } catch (error) {
                console.error('Error fetching nearby stops:', error);
                alert('Error fetching nearby stops');
                btn.textContent = '📍 Use My Location';
                btn.disabled = false;
            }
        },
        (error) => {
            console.error('Geolocation error:', error);
            alert('Unable to get your location');
            btn.textContent = '📍 Use My Location';
            btn.disabled = false;
        }
    );
}

// Handle form submission
document.getElementById('routeForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const source = document.getElementById('source').value;
    const destination = document.getElementById('destination').value;
    const maxTransfers = document.getElementById('maxTransfers').value;
    const includeWalking = document.getElementById('includeWalking').checked;

    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div>Searching routes...</div>';

    try {
        const response = await fetch('/api/find-route', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                source: source,
                destination: destination,
                max_transfers: parseInt(maxTransfers),
                include_walking: includeWalking
            })
        });

        const data = await response.json();
        displayResults(data);

    } catch (error) {
        console.error('Error:', error);
        resultsDiv.innerHTML = '<div class="alert alert-danger">Error finding routes. Please try again.</div>';
    }
});

// Display results
function displayResults(data) {
    const resultsDiv = document.getElementById('results');

    if (data.routes && data.routes.length > 0) {
        let html = '<div class="result-section"><h3>Available Routes</h3>';

        data.routes.forEach(route => {
            html += `
                <div class="route-option">
                    <div class="route-header">
                        <span class="route-number">Route ${route.route_number}</span>
                        <span class="route-time">${route.duration_minutes} min</span>
                    </div>
                    <div class="route-details">
                        <strong>${route.route_name}</strong><br>
                        ${route.trip_headsign}<br>
                        ${route.stops_count} stops • Departs: ${route.departure_time}
                    </div>
                </div>
            `;
        });

        html += '</div>';
        resultsDiv.innerHTML = html;

    } else {
        resultsDiv.innerHTML = '<div class="no-results">No routes found. Try different stops or increase max transfers.</div>';
    }
}

// Load routes into memory
async function loadRoutes() {
    try {
        const response = await fetch('/api/routes');
        allRoutes = await response.json();
        console.log(`Loaded ${allRoutes.length} routes`);

        // Set up autocomplete for route filter
        setupRouteAutocomplete();
    } catch (error) {
        console.error('Error loading routes:', error);
    }
}

// Setup autocomplete for route filter
function setupRouteAutocomplete() {
    const searchInput = document.getElementById('routeFilterSearch');
    const resultsDiv = document.getElementById('routeFilterResults');
    const hiddenInput = document.getElementById('routeFilter');
    const clearBtn = searchInput.nextElementSibling;

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim().toLowerCase();

        if (query.length === 0) {
            resultsDiv.classList.remove('show');
            clearBtn.classList.remove('show');
            hiddenInput.value = '';
            loadVehicles(); // Load all vehicles
            return;
        }

        clearBtn.classList.add('show');

        // Special case for "all"
        if (query === 'all') {
            hiddenInput.value = '';
            loadVehicles();
            resultsDiv.classList.remove('show');
            return;
        }

        // Filter routes
        const matches = allRoutes.filter(route => {
            const number = (route.number || '').toString().toLowerCase();
            const name = (route.name || '').toLowerCase();
            const id = (route.id || '').toString().toLowerCase();

            return number.includes(query) ||
                name.includes(query) ||
                id.includes(query);
        }).slice(0, 10);

        if (matches.length > 0) {
            displayRouteAutocompleteResults(matches);
        } else {
            resultsDiv.innerHTML = '<div class="autocomplete-item">No routes found</div>';
            resultsDiv.classList.add('show');
        }
    });

    // Handle keyboard navigation
    searchInput.addEventListener('keydown', (e) => {
        const items = resultsDiv.querySelectorAll('.autocomplete-item');

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedStopIndex = Math.min(selectedStopIndex + 1, items.length - 1);
            updateSelection(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedStopIndex = Math.max(selectedStopIndex - 1, 0);
            updateSelection(items);
        } else if (e.key === 'Enter' && selectedStopIndex >= 0) {
            e.preventDefault();
            items[selectedStopIndex].click();
        } else if (e.key === 'Escape') {
            resultsDiv.classList.remove('show');
        }
    });

    // Close on click outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !resultsDiv.contains(e.target)) {
            resultsDiv.classList.remove('show');
        }
    });
}

function displayRouteAutocompleteResults(routes) {
    const resultsDiv = document.getElementById('routeFilterResults');

    resultsDiv.innerHTML = routes.map((route, index) => `
        <div class="autocomplete-item" 
             onclick="selectRoute('${route.id}', '${route.number}', '${route.name.replace(/'/g, "\\'")}')">
            <strong>${route.number}</strong> - ${route.name}<br>
            <small style="color: #999;">Route ID: ${route.id}</small>
        </div>
    `).join('');

    resultsDiv.classList.add('show');
    selectedStopIndex = -1;
}

function selectRoute(routeId, routeNumber, routeName) {
    document.getElementById('routeFilterSearch').value = `${routeNumber} - ${routeName}`;
    document.getElementById('routeFilter').value = routeId;
    document.getElementById('routeFilterResults').classList.remove('show');
    document.getElementById('routeFilterSearch').nextElementSibling.classList.add('show');
    loadVehicles(); // Reload vehicles with filter
    loadAlerts(); // Reload alerts with filter
}

function clearRouteFilter() {
    document.getElementById('routeFilterSearch').value = '';
    document.getElementById('routeFilter').value = '';
    document.getElementById('routeFilterResults').classList.remove('show');
    document.getElementById('routeFilterSearch').nextElementSibling.classList.remove('show');
    loadVehicles(); // Reload all vehicles
    loadAlerts(); // Reload all alerts
}

// Select route from alert click
async function selectRouteFromAlert(routeId) {
    // Make sure we have routes loaded
    if (allRoutes.length === 0) {
        await loadRoutes();
    }

    // Find the route
    const route = allRoutes.find(r => r.id === routeId);

    if (route) {
        selectRoute(route.id, route.number, route.name);

        // Scroll map into view if on mobile
        document.getElementById('map').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
        console.warn('Route not found:', routeId);
    }
}

// Load vehicles (buses)
async function loadVehicles() {
    const routeId = document.getElementById('routeFilter').value;
    const url = routeId ? `/api/vehicles?route_id=${routeId}` : '/api/vehicles';

    try {
        const response = await fetch(url);
        const data = await response.json();
        const vehicles = data.vehicles || data; // Handle both formats

        clearBusMarkers();

        if (vehicles.length === 0) {
            document.getElementById('apiStatusAlert').style.display = 'block';
        } else {
            document.getElementById('apiStatusAlert').style.display = 'none';
        }

        vehicles.forEach(vehicle => {
            if (vehicle.latitude && vehicle.longitude) {
                createBusMarker(vehicle);
            }
        });

        console.log(`Loaded ${vehicles.length} vehicles`);

    } catch (error) {
        console.error('Error loading vehicles:', error);
        document.getElementById('apiStatusAlert').style.display = 'block';
    }
}

// Create bus marker
function createBusMarker(vehicle) {
    const isHighlighted = highlightedBuses.has(vehicle.vehicle_id);

    // Determine direction from headsign
    const headsign = (vehicle.headsign || '').toUpperCase();
    let directionArrow = '';
    let directionColor = isHighlighted ? '#ff9800' : '#f15a29';

    // Extract direction from headsign (N/S/E/W or To keywords)
    if (headsign.includes(' N ') || headsign.includes('NORTH')) {
        directionArrow = '↑';
        directionColor = '#2196f3'; // Blue for North
    } else if (headsign.includes(' S ') || headsign.includes('SOUTH')) {
        directionArrow = '↓';
        directionColor = '#f44336'; // Red for South
    } else if (headsign.includes(' E ') || headsign.includes('EAST')) {
        directionArrow = '→';
        directionColor = '#4caf50'; // Green for East
    } else if (headsign.includes(' W ') || headsign.includes('WEST')) {
        directionArrow = '←';
        directionColor = '#ff9800'; // Orange for West
    } else if (headsign.includes('TO ')) {
        // Try to infer from destination
        const destination = headsign.split('TO ')[1] || '';
        if (destination.includes('KIPLING') || destination.includes('ETOBICOKE')) {
            directionArrow = '→'; // East
            directionColor = '#4caf50';
        } else if (destination.includes('MALTON') || destination.includes('AIRPORT')) {
            directionArrow = '←'; // West
            directionColor = '#ff9800';
        }
    }

    // Use bearing if available and no direction from headsign
    if (!directionArrow && vehicle.bearing !== null && vehicle.bearing !== undefined) {
        const bearing = vehicle.bearing;
        if (bearing >= 315 || bearing < 45) {
            directionArrow = '↑'; // North
            directionColor = '#2196f3';
        } else if (bearing >= 45 && bearing < 135) {
            directionArrow = '→'; // East
            directionColor = '#4caf50';
        } else if (bearing >= 135 && bearing < 225) {
            directionArrow = '↓'; // South
            directionColor = '#f44336';
        } else {
            directionArrow = '←'; // West
            directionColor = '#ff9800';
        }
    }

    const busIcon = L.divIcon({
        className: 'bus-marker',
        html: `<div style="
            display: flex;
            align-items: center;
            gap: 2px;
        ">
            ${directionArrow ? `<span style="
                background: ${directionColor};
                color: white;
                padding: 2px 3px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
                line-height: 1;
                box-shadow: 0 1px 3px rgba(0,0,0,0.3);
            ">${directionArrow}</span>` : ''}
            <span style="font-size: 16px;">🚌</span>
            <span style="
                background: white;
                color: ${isHighlighted ? '#ff9800' : '#f15a29'};
                padding: 2px 4px;
                border-radius: 3px;
                font-size: 10px;
                font-weight: bold;
                border: 1px solid ${isHighlighted ? '#ff9800' : '#f15a29'};
                line-height: 1;
            ">${vehicle.route_number || vehicle.route_id}</span>
        </div>`,
        iconSize: [55, 20],
        iconAnchor: [27, 10]
    });

    const marker = L.marker([vehicle.latitude, vehicle.longitude], { icon: busIcon })
        .addTo(map);

    let popupContent = `
        <strong>Bus ${vehicle.vehicle_id}</strong><br>
        Route: ${vehicle.route_number || vehicle.route_id} - ${vehicle.route_name || 'N/A'}<br>
        ${vehicle.headsign || ''}
    `;

    if (vehicle.speed !== null && vehicle.speed !== undefined) {
        popupContent += `<br>Speed: ${(vehicle.speed * 3.6).toFixed(1)} km/h`;
    }

    if (vehicle.occupancy) {
        const occupancyMap = {
            'MANY_SEATS_AVAILABLE': '🟢 Many seats',
            'FEW_SEATS_AVAILABLE': '🟡 Few seats',
            'STANDING_ROOM_ONLY': '🟠 Standing only',
            'FULL': '🔴 Full'
        };
        popupContent += `<br>${occupancyMap[vehicle.occupancy] || vehicle.occupancy}`;
    }

    marker.bindPopup(popupContent);

    busMarkers.push({ marker, vehicle });
}

// Clear bus markers
function clearBusMarkers() {
    busMarkers.forEach(({ marker }) => marker.remove());
    busMarkers = [];
}

// Load service alerts
async function loadAlerts() {
    const routeId = document.getElementById('routeFilter').value;
    const url = routeId ? `/api/alerts?route_id=${routeId}` : '/api/alerts';

    try {
        const response = await fetch(url);
        const data = await response.json();

        // API returns {alerts: [...], count: N}
        const alerts = data.alerts || data || [];

        const alertsDiv = document.getElementById('serviceAlerts');

        if (alerts.length > 0) {
            let html = '<div class="result-section"><h3>🚨 Service Alerts</h3>';

            alerts.forEach(alert => {
                // API uses 'header' and 'description', not 'header_text' and 'description_text'
                const header = alert.header || alert.header_text || 'Service Alert';
                const description = alert.description || alert.description_text || '';
                const routeIds = alert.route_ids || [];

                // Create clickable route badges
                let routeBadges = '';
                if (routeIds.length > 0) {
                    routeBadges = '<div style="margin-top: 8px;">';
                    routeIds.forEach(routeId => {
                        routeBadges += `
                            <span class="route-badge" onclick="selectRouteFromAlert('${routeId}')">
                                Route ${routeId}
                            </span>
                        `;
                    });
                    routeBadges += '</div>';
                }

                html += `
                    <div class="alert alert-warning">
                        <strong>${header}</strong><br>
                        ${description}
                        ${routeBadges}
                    </div>
                `;
            });

            html += '</div>';
            alertsDiv.innerHTML = html;
        } else {
            alertsDiv.innerHTML = '';
        }

    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

// Find buses near user
async function findMyBuses() {
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = '📍 Getting location...';

    if (!navigator.geolocation) {
        alert('Geolocation is not supported');
        btn.disabled = false;
        btn.textContent = '📍 Find Buses Near Me';
        return;
    }

    navigator.geolocation.getCurrentPosition(
        async (position) => {
            userLocation = {
                lat: position.coords.latitude,
                lon: position.coords.longitude
            };

            try {
                const response = await fetch(`/api/nearby-buses?lat=${userLocation.lat}&lon=${userLocation.lon}&limit=10`);
                const data = await response.json();

                displayNearbyBuses(data.buses || data.nearby_buses || []);
                highlightNearbyBuses(data.buses || data.nearby_buses || []);

                // Center map on user
                map.setView([userLocation.lat, userLocation.lon], 14);

                // Add/update user marker
                setUserLocation(userLocation.lat, userLocation.lon);

                btn.textContent = '✅ Buses found';
                setTimeout(() => {
                    btn.textContent = '📍 Find Buses Near Me';
                    btn.disabled = false;
                }, 2000);

            } catch (error) {
                console.error('Error:', error);
                console.error('Full response data:', data);
                alert('Error finding nearby buses');
                btn.textContent = '📍 Find Buses Near Me';
                btn.disabled = false;
            }
        },
        (error) => {
            console.error('Geolocation error:', error);
            alert('Unable to get your location');
            btn.textContent = '📍 Find Buses Near Me';
            btn.disabled = false;
        }
    );
}

// Display nearby buses
function displayNearbyBuses(buses) {
    const container = document.getElementById('nearbyBusesContainer');

    if (!buses || buses.length === 0) {
        container.innerHTML = '<div class="no-results">No buses found nearby</div>';
        return;
    }

    let html = '<div class="result-section"><h3>Buses Near You</h3>';

    buses.forEach((bus, index) => {
        const routeNumber = bus.route_number || bus.route_short_name;
        const routeName = bus.route_name || bus.route_long_name;
        const stopDistance = bus.stop_distance_from_user || bus.stop_distance || 0;
        const headsign = bus.headsign || bus.trip_headsign || 'N/A';

        html += `
            <div class="bus-card" onclick="focusBusOnMap('${bus.vehicle_id}')">
                <div class="bus-header">
                    <span class="bus-route">Route ${routeNumber}</span>
                    <span class="bus-eta">${bus.eta_minutes} min</span>
                </div>
                <div class="bus-details">
                    ${routeName}<br>
                    Stop: ${bus.stop_name} (${stopDistance.toFixed(2)} km)<br>
                    ${headsign}
                </div>
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
}

// Highlight nearby buses on map
function highlightNearbyBuses(buses) {
    highlightedBuses.clear();
    buses.forEach(bus => {
        highlightedBuses.add(bus.vehicle_id);
    });
    loadVehicles(); // Reload to apply highlighting
}

// Focus on a specific bus
function focusBusOnMap(vehicleId) {
    const busData = busMarkers.find(b => b.vehicle.vehicle_id === vehicleId);
    if (busData) {
        map.setView([busData.vehicle.latitude, busData.vehicle.longitude], 16);
        busData.marker.openPopup();
    }
}

// Refresh live data
async function refreshLiveData() {
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = '⏳ Refreshing...';

    try {
        const response = await fetch('/api/refresh-realtime');
        const data = await response.json();

        if (data.success) {
            console.log('Live data refreshed:', data);
            loadVehicles();
            loadAlerts();
            updateDataFreshness();

            btn.textContent = '✅ Refreshed';
            setTimeout(() => {
                btn.textContent = '🔴 Live Refresh';
                btn.disabled = false;
            }, 2000);

            // Show error details if any
            if (data.errors && data.errors.length > 0) {
                console.warn('Refresh warnings:', data.errors);
                if (data.error_details) {
                    console.warn('Error details:', data.error_details);

                    // Show connection error alert
                    const hasConnectionError = data.error_details.some(e =>
                        e.error === 'Connection Error' || e.status_code === 0
                    );
                    if (hasConnectionError) {
                        document.getElementById('apiStatusAlert').style.display = 'block';
                    }
                }
            }
        } else {
            console.error('Refresh failed:', data.errors);
            document.getElementById('apiStatusAlert').style.display = 'block';

            if (data.error_details) {
                console.error('Error details:', data.error_details);
                // Check for rate limiting
                const rateLimited = data.error_details.some(e => e.status_code === 429);
                const connectionError = data.error_details.some(e => e.error === 'Connection Error');

                if (rateLimited) {
                    alert('⚠️ Rate limited by MiWay servers. Please wait before refreshing again.');
                } else if (connectionError) {
                    // Silently show alert banner, don't popup
                    console.log('MiWay API is currently unavailable');
                }
            }
            btn.textContent = '❌ Failed';
            setTimeout(() => {
                btn.textContent = '🔴 Live Refresh';
                btn.disabled = false;
            }, 2000);
        }

    } catch (error) {
        console.error('Error refreshing:', error);
        btn.textContent = '❌ Error';
        setTimeout(() => {
            btn.textContent = '🔴 Live Refresh';
            btn.disabled = false;
        }, 2000);
    }
}

// Show user's current location on map
function showMyLocation() {
    if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser');
        return;
    }

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;

            setUserLocation(lat, lon);
            map.setView([lat, lon], 15);

            // Open popup
            if (userLocationMarker) {
                userLocationMarker.openPopup();
            }
        },
        (error) => {
            console.error('Geolocation error:', error);
            alert('Unable to get your location. Please check your browser permissions.');
        }
    );
}

// Update data freshness indicator
async function updateDataFreshness() {
    try {
        const response = await fetch('/api/data-freshness');
        const data = await response.json();

        const freshnessDiv = document.getElementById('dataFreshness');
        const freshnessText = document.getElementById('freshnessText');

        // Convert seconds to minutes
        const ageSeconds = data.data_age_seconds;

        if (!ageSeconds && ageSeconds !== 0) {
            freshnessText.textContent = '⚠️ No data';
            freshnessDiv.className = 'data-freshness very-stale';
            return;
        }

        const ageMinutes = ageSeconds / 60;

        if (ageMinutes < 2) {
            freshnessDiv.className = 'data-freshness fresh';
            freshnessText.textContent = `🟢 Live (${Math.round(ageMinutes)}m ago)`;
        } else if (ageMinutes < 5) {
            freshnessDiv.className = 'data-freshness stale';
            freshnessText.textContent = `🟡 ${Math.round(ageMinutes)}m ago`;
        } else {
            freshnessDiv.className = 'data-freshness very-stale';
            freshnessText.textContent = `🔴 ${Math.round(ageMinutes)}m ago`;
        }

    } catch (error) {
        console.error('Error updating freshness:', error);
        document.getElementById('freshnessText').textContent = '❌ Error';
    }
}

// Auto-refresh
function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }

    autoRefreshInterval = setInterval(() => {
        if (currentTab === 'live') {
            loadVehicles();
            updateDataFreshness();
        }
    }, 15000); // Refresh every 15 seconds
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    loadStops();
    updateDataFreshness();

    // Update freshness every 30 seconds
    setInterval(updateDataFreshness, 30000);
});


