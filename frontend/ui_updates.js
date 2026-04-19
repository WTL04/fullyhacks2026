import { socket } from './socket_handler.js';

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
    }
    if (data.tick != null) document.getElementById('footer-tick').innerText = data.tick;
    if (data.global_vaccine_progress != null) document.getElementById('footer-vac').innerText = data.global_vaccine_progress.toFixed(2);
    if (data.evolution_points != null) document.getElementById('footer-evo').innerText = data.evolution_points;
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
    const { tick, message, type } = data;
    const entry = document.createElement('div');
    entry.className = 'log-entry virus';
    const colorClass = type === 'mutation' ? 'mutation' : 'deploy';
    entry.innerHTML = `<div class="log-tick virus">TICK ${tick}</div><div class="log-message ${colorClass}">${message}</div>`;
    feed.prepend(entry);
}

socket.on('state_update', updateStats);
socket.on('action_results', updateCoordinatorLog);
socket.on('virus_log', updateVirusLog);
