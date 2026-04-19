import { socket, sendAction } from './socket_handler.js';

function updateStats(data) {
    if (!data) return;
    
    if (data.utility_score != null) {
        document.getElementById('stat-utility').innerText = data.utility_score.toFixed(3);
        document.getElementById('bar-utility').style.width = `${data.utility_score * 100}%`;
    }
    if (data.global_infected != null) {
        document.getElementById('stat-infected').innerText = `${(data.global_infected * 100).toFixed(2)}%`;
        document.getElementById('bar-infected').style.width = `${data.global_infected * 100}%`;
    }
    if (data.countries) {
        const totalDeaths = Object.values(data.countries).reduce((sum, c) => sum + (c.dead || 0), 0);
        document.getElementById('stat-deaths').innerText = totalDeaths.toLocaleString();
        
        // Update country cards
        updateCountryCards(data.countries, data.global_vaccine_progress);
    }
    if (data.tick != null) document.getElementById('footer-tick').innerText = data.tick;
    if (data.global_vaccine_progress != null) document.getElementById('footer-vac').innerText = data.global_vaccine_progress.toFixed(2);
    if (data.evolution_points != null) document.getElementById('footer-evo').innerText = data.evolution_points;
}

function updateCountryCards(countries, vaccineProgress) {
    const container = document.getElementById('countriesList');
    if (!container) return;
    
    // Sort countries by infection rate (highest first)
    const sortedCountries = Object.entries(countries)
        .sort((a, b) => b[1].infected - a[1].infected);
    
    // Build HTML for all country cards
    let html = '';
    for (const [name, data] of sortedCountries) {
        const infectedPercent = (data.infected * 100).toFixed(2);
        const gdpPercent = (data.gdp * 100).toFixed(1);
        const containmentPercent = (data.containment_level * 100).toFixed(0);
        const population = formatPopulation(data.population);
        const deaths = data.dead.toLocaleString();
        
        // Determine card class based on infection level
        let cardClass = 'country-card';
        if (data.infected > 0.3) {
            cardClass += ' critical';
        } else if (data.infected > 0.01) {
            cardClass += ' infected';
        }
        
        html += `
            <div class="${cardClass}" data-country="${name}">
                <div class="country-card-header">
                    <span class="country-name">${name}</span>
                    <span class="country-population">Pop: ${population}</span>
                </div>
                <div class="country-stats">
                    <div class="country-stat">
                        <span class="country-stat-label">Infected</span>
                        <span class="country-stat-value infected">${infectedPercent}%</span>
                    </div>
                    <div class="country-stat">
                        <span class="country-stat-label">GDP</span>
                        <span class="country-stat-value gdp">${gdpPercent}%</span>
                    </div>
                    <div class="country-stat">
                        <span class="country-stat-label">Contain</span>
                        <span class="country-stat-value containment">${containmentPercent}%</span>
                    </div>
                    <div class="country-stat">
                        <span class="country-stat-label">Deaths</span>
                        <span class="country-stat-value deaths">${deaths}</span>
                    </div>
                    <div class="country-stat">
                        <span class="country-stat-label">Vaccine</span>
                        <span class="country-stat-value vaccine">${((vaccineProgress || 0) * 100).toFixed(1)}%</span>
                    </div>
                    <div class="country-stat">
                        <span class="country-stat-label">Research</span>
                        <span class="country-stat-value">${data.research_capacity || 0}</span>
                    </div>
                </div>
                <div class="country-infrastructure">
                    <span class="infra-badge ${data.airports_open ? 'open' : 'closed'}">
                        Airport: ${data.airports_open ? 'OPEN' : 'CLOSED'}
                    </span>
                    <span class="infra-badge ${data.ports_open ? 'open' : 'closed'}">
                        Port: ${data.ports_open ? 'OPEN' : 'CLOSED'}
                    </span>
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

function formatPopulation(pop) {
    if (pop >= 1000000000) return (pop / 1000000000).toFixed(1) + 'B';
    if (pop >= 1000000) return (pop / 1000000).toFixed(1) + 'M';
    if (pop >= 1000) return (pop / 1000).toFixed(1) + 'K';
    return pop.toString();
}

function updateCoordinatorLog(data) {
    const feed = document.getElementById('log-feed');
    const { thought, actions, tick } = data;
    const entry = document.createElement('div');
    entry.className = 'log-entry active';
    let html = `<div class="log-tick">TICK ${tick}</div>`;
    if (thought) html += `<div class="log-thought">${thought}</div>`;
    if (actions && actions.length) {
        html += `<div class="log-actions">`;
        actions.forEach(a => {
            html += `<span>${a.type} ${a.target}</span>`;
        });
        html += `</div>`;
    }
    entry.innerHTML = html;
    feed.prepend(entry);
}

function updateVirusLog(data) {
    const feed = document.getElementById('virus-feed');
    if (!feed) {
        console.warn('virus-feed element not found');
        return;
    }
    const { tick, message, type } = data;
    const entry = document.createElement('div');
    entry.className = 'log-entry virus';
    const colorClass = type === 'mutation' ? 'mutation' : 'deploy';
    entry.innerHTML = `<div class="log-tick virus">TICK ${tick}</div><div class="log-message ${colorClass}">${message}</div>`;
    feed.prepend(entry);
    console.log('Virus log updated:', data);
}

socket.on('state_update', updateStats);
socket.on('action_results', updateCoordinatorLog);
socket.on('virus_log', updateVirusLog);
