// Map Handler - ArcGIS country nodes visualization
import { socket } from './socket_handler.js';

// Country coordinates (latitude, longitude)
const COUNTRY_COORDS = {
    'USA': { lat: 39.8283, lon: -98.5795, label: 'United States' },
    'Canada': { lat: 56.1304, lon: -106.3468, label: 'Canada' },
    'Mexico': { lat: 23.6345, lon: -102.5528, label: 'Mexico' },
    'Brazil': { lat: -14.2350, lon: -51.9253, label: 'Brazil' },
    'Argentina': { lat: -38.4161, lon: -63.6167, label: 'Argentina' },
    'Chile': { lat: -35.6751, lon: -71.5430, label: 'Chile' },
    'Colombia': { lat: 4.5709, lon: -74.2973, label: 'Colombia' },
    'Venezuela': { lat: 6.4238, lon: -66.5897, label: 'Venezuela' }
};

let graphicsLayer = null;
let connectionsLayer = null;
let view = null;
let latestCountryData = {};
let globalVaccineProgress = 0;
let activeConnections = []; // Track active connection lines

// Initialize map with country markers
async function initMapMarkers(sceneView) {
    view = sceneView;
    
    const [GraphicsLayer, Graphic, Point, SimpleMarkerSymbol, TextSymbol, PopupTemplate] = await $arcgis.import([
        "@arcgis/core/layers/GraphicsLayer.js",
        "@arcgis/core/Graphic.js",
        "@arcgis/core/geometry/Point.js",
        "@arcgis/core/symbols/SimpleMarkerSymbol.js",
        "@arcgis/core/symbols/TextSymbol.js",
        "@arcgis/core/PopupTemplate.js"
    ]);
    
    // Create graphics layer for connection lines (added first so it's behind markers)
    connectionsLayer = new GraphicsLayer({
        id: 'countryConnections'
    });
    view.map.add(connectionsLayer);
    
    // Create graphics layer for country markers
    graphicsLayer = new GraphicsLayer({
        id: 'countryMarkers'
    });
    
    view.map.add(graphicsLayer);
    
    // Add initial markers for each country
    for (const [name, coords] of Object.entries(COUNTRY_COORDS)) {
        const point = new Point({
            longitude: coords.lon,
            latitude: coords.lat
        });
        
        // Create popup template for the marker
        const popupTemplate = new PopupTemplate({
            title: "{name}",
            content: getPopupContent
        });
        
        // Main marker
        const markerGraphic = new Graphic({
            geometry: point,
            symbol: new SimpleMarkerSymbol({
                style: 'circle',
                color: [59, 130, 246, 0.6], // Blue, healthy
                size: 20,
                outline: {
                    color: [59, 130, 246, 1],
                    width: 2
                }
            }),
            attributes: {
                name: name,
                type: 'marker',
                containment_level: 0,
                airports_open: true,
                ports_open: true,
                population: 0,
                infected: 0,
                vaccine_progress: 0
            },
            popupTemplate: popupTemplate
        });
        
        // Label
        const labelGraphic = new Graphic({
            geometry: point,
            symbol: new TextSymbol({
                text: name,
                color: 'white',
                font: {
                    size: 10,
                    family: 'Share Tech Mono'
                },
                haloColor: [10, 14, 26, 0.8],
                haloSize: 2,
                yoffset: -25
            }),
            attributes: {
                name: name,
                type: 'label'
            }
        });
        
        graphicsLayer.addMany([markerGraphic, labelGraphic]);
    }
    
    // Configure popup behavior
    view.popup.autoOpenEnabled = true;
    view.popup.dockEnabled = false;
    view.popup.dockOptions = {
        buttonEnabled: false
    };
    
    // Listen for state updates to update markers
    socket.on('state_update', updateMapMarkers);
    
    // Listen for connection events (foreign_aid and share_data)
    socket.on('country_connection', handleConnectionEvent);
    
    // Clear connections on simulation reset
    socket.on('simulation_reset', clearConnections);
}

// Generate popup content dynamically
function getPopupContent(feature) {
    const name = feature.graphic.attributes.name;
    const data = latestCountryData[name];
    
    if (!data) {
        return '<div class="popup-loading">Loading data...</div>';
    }
    
    const containmentPercent = (data.containment_level * 100).toFixed(0);
    const infectedPercent = (data.infected * 100).toFixed(2);
    const vaccinePercent = (globalVaccineProgress * 100).toFixed(1);
    const population = formatPopulation(data.population);
    
    return `
        <div class="country-popup">
            <div class="popup-row">
                <span class="popup-label">Containment Level</span>
                <span class="popup-value containment">${containmentPercent}%</span>
                <div class="popup-bar">
                    <div class="popup-bar-fill containment" style="width: ${containmentPercent}%"></div>
                </div>
            </div>
            <div class="popup-row">
                <span class="popup-label">Airport Status</span>
                <span class="popup-value ${data.airports_open ? 'open' : 'closed'}">${data.airports_open ? 'OPEN' : 'CLOSED'}</span>
            </div>
            <div class="popup-row">
                <span class="popup-label">Port Status</span>
                <span class="popup-value ${data.ports_open ? 'open' : 'closed'}">${data.ports_open ? 'OPEN' : 'CLOSED'}</span>
            </div>
            <div class="popup-row">
                <span class="popup-label">Current Population</span>
                <span class="popup-value population">${population}</span>
            </div>
            <div class="popup-row">
                <span class="popup-label">Current Infected</span>
                <span class="popup-value infected">${infectedPercent}%</span>
                <div class="popup-bar">
                    <div class="popup-bar-fill infected" style="width: ${Math.min(data.infected * 100, 100)}%"></div>
                </div>
            </div>
            <div class="popup-row">
                <span class="popup-label">Vaccine Progress</span>
                <span class="popup-value vaccine">${vaccinePercent}%</span>
                <div class="popup-bar">
                    <div class="popup-bar-fill vaccine" style="width: ${globalVaccineProgress * 100}%"></div>
                </div>
            </div>
        </div>
    `;
}

// Format population number
function formatPopulation(pop) {
    if (pop >= 1000000000) return (pop / 1000000000).toFixed(2) + ' B';
    if (pop >= 1000000) return (pop / 1000000).toFixed(2) + ' M';
    if (pop >= 1000) return (pop / 1000).toFixed(1) + ' K';
    return pop.toLocaleString();
}

// Update marker colors and attributes based on infection levels
async function updateMapMarkers(data) {
    if (!graphicsLayer || !data.countries) return;
    
    // Store latest data for popup content
    latestCountryData = data.countries;
    globalVaccineProgress = data.global_vaccine_progress || 0;
    
    const [SimpleMarkerSymbol] = await $arcgis.import([
        "@arcgis/core/symbols/SimpleMarkerSymbol.js"
    ]);
    
    for (const graphic of graphicsLayer.graphics.items) {
        if (graphic.attributes.type !== 'marker') continue;
        
        const countryName = graphic.attributes.name;
        const countryData = data.countries[countryName];
        
        if (!countryData) continue;
        
        // Update attributes for popup
        graphic.attributes.containment_level = countryData.containment_level;
        graphic.attributes.airports_open = countryData.airports_open;
        graphic.attributes.ports_open = countryData.ports_open;
        graphic.attributes.population = countryData.population;
        graphic.attributes.infected = countryData.infected;
        graphic.attributes.vaccine_progress = globalVaccineProgress;
        
        const infected = countryData.infected;
        const { color, outlineColor, size } = getMarkerStyle(infected);
        
        // Update symbol
        graphic.symbol = new SimpleMarkerSymbol({
            style: 'circle',
            color: color,
            size: size,
            outline: {
                color: outlineColor,
                width: 2
            }
        });
    }
    
    // Refresh popup if open
    if (view.popup.visible && view.popup.selectedFeature) {
        view.popup.content = getPopupContent(view.popup.selectedFeature);
    }
}

// Get marker style based on infection level
function getMarkerStyle(infected) {
    if (infected > 0.5) {
        // Critical - Red
        return {
            color: [239, 68, 68, 0.8],
            outlineColor: [239, 68, 68, 1],
            size: 30
        };
    } else if (infected > 0.2) {
        // High - Orange
        return {
            color: [249, 115, 22, 0.7],
            outlineColor: [249, 115, 22, 1],
            size: 26
        };
    } else if (infected > 0.05) {
        // Medium - Yellow
        return {
            color: [234, 179, 8, 0.6],
            outlineColor: [234, 179, 8, 1],
            size: 22
        };
    } else if (infected > 0.01) {
        // Low - Light yellow
        return {
            color: [253, 224, 71, 0.5],
            outlineColor: [253, 224, 71, 1],
            size: 20
        };
    } else {
        // Healthy - Blue
        return {
            color: [59, 130, 246, 0.5],
            outlineColor: [59, 130, 246, 1],
            size: 18
        };
    }
}

// Handle connection events from backend
async function handleConnectionEvent(data) {
    const { source, target, type } = data;
    
    if (!COUNTRY_COORDS[source] || !COUNTRY_COORDS[target]) {
        console.warn(`Unknown country in connection: ${source} or ${target}`);
        return;
    }
    
    await drawConnectionLine(source, target, type);
}

// Draw a geodesic line between two countries
async function drawConnectionLine(sourceCountry, targetCountry, connectionType) {
    if (!connectionsLayer) return;
    
    const [Graphic, Polyline, SimpleLineSymbol, geometryEngine] = await $arcgis.import([
        "@arcgis/core/Graphic.js",
        "@arcgis/core/geometry/Polyline.js",
        "@arcgis/core/symbols/SimpleLineSymbol.js",
        "@arcgis/core/geometry/geometryEngine.js"
    ]);
    
    const sourceCoords = COUNTRY_COORDS[sourceCountry];
    const targetCoords = COUNTRY_COORDS[targetCountry];
    
    // Create connection key to track duplicates
    const connectionKey = [sourceCountry, targetCountry].sort().join('-');
    
    // Check if connection already exists
    if (activeConnections.includes(connectionKey + '-' + connectionType)) {
        return; // Don't draw duplicate lines
    }
    activeConnections.push(connectionKey + '-' + connectionType);
    
    // Create a geodesic polyline for the great circle path
    const polyline = new Polyline({
        paths: [[
            [sourceCoords.lon, sourceCoords.lat],
            [targetCoords.lon, targetCoords.lat]
        ]],
        spatialReference: { wkid: 4326 }
    });
    
    // Densify the line to make it follow the geodesic (great circle) path
    const geodesicLine = geometryEngine.geodesicDensify(polyline, 100000); // 100km segments
    
    // Different styles for different connection types
    let lineColor, lineWidth, lineStyle;
    if (connectionType === 'foreign_aid') {
        // Gold/yellow for foreign aid (money flow)
        lineColor = [255, 215, 0, 0.8]; // Gold
        lineWidth = 3;
        lineStyle = 'solid';
    } else if (connectionType === 'share_data') {
        // Cyan/blue for data sharing (information flow)
        lineColor = [0, 255, 255, 0.8]; // Cyan
        lineWidth = 2;
        lineStyle = 'dash';
    } else {
        // Default white
        lineColor = [255, 255, 255, 0.6];
        lineWidth = 2;
        lineStyle = 'solid';
    }
    
    const lineSymbol = new SimpleLineSymbol({
        color: lineColor,
        width: lineWidth,
        style: lineStyle
    });
    
    const lineGraphic = new Graphic({
        geometry: geodesicLine,
        symbol: lineSymbol,
        attributes: {
            source: sourceCountry,
            target: targetCountry,
            type: connectionType,
            connectionKey: connectionKey
        }
    });
    
    connectionsLayer.add(lineGraphic);
    
    // Add animated glow effect by adding a second wider line behind
    const glowSymbol = new SimpleLineSymbol({
        color: [...lineColor.slice(0, 3), 0.3], // Same color but more transparent
        width: lineWidth + 4,
        style: 'solid'
    });
    
    const glowGraphic = new Graphic({
        geometry: geodesicLine,
        symbol: glowSymbol,
        attributes: {
            source: sourceCountry,
            target: targetCountry,
            type: connectionType + '_glow',
            connectionKey: connectionKey
        }
    });
    
    // Add glow behind the main line
    connectionsLayer.graphics.unshift(glowGraphic);
}

// Clear all connection lines (useful for game reset)
function clearConnections() {
    if (connectionsLayer) {
        connectionsLayer.removeAll();
    }
    activeConnections = [];
}

export { initMapMarkers, COUNTRY_COORDS, drawConnectionLine, clearConnections };
