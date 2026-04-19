// Opening Screen Handler
// Manages the sequence of outbreak report and country selection popups

const COUNTRIES = [
    'USA', 'Canada', 'Mexico', 'Brazil', 
    'Argentina', 'Chile', 'Colombia', 'Venezuela'
];

const PRESET_STORIES = {
    "1": "BREAKING: Global pandemic declared after a tourist dropped a flaming hot Cheeto into the Mariana Trench and gave the ocean a fever.",
    "2": "A new virus is spreading because someone tried to 'tip' an Atlantean statue with a piece of used nicotine gum.",
    "3": "The 'Bikini Bottom Flu' has escaped the sea after a diver tried to steal the Krabby Patty secret formula.",
    "4": "The Bermuda Triangle is leaking a virus that makes people walk backward after a jet skier tried to jump a ghost ship.",
    "5": "Panic ensues as a prehistoric plague emerges from the Mariana Trench because a YouTuber tried to 'prank' a giant squid.",
    "6": "Scientists confirm the 'Atlantis Itch' started when a billionaire tried to install a vending machine in the sunken palace.",
    "7": "A new virus is turning people blue because a snorkeler tried to use Poseidon's trident as a marshmallow roaster.",
    "8": "The latest outbreak began when a cruise ship captain tried to use the Bermuda Triangle as a shortcut to save five minutes.",
    "9": "BREAKING: We are all turning into crabs because someone threw a car battery into the Mariana Trench for 'vibes.'",
    "10": "A viral contagion is spreading after a diver tried to give a high-five to a cursed barnacle in Bikini Bottom.",
    "11": "The 'Deep Sea Sneeze' is here because a submarine pilot tried to brew espresso using hydrothermal vent water.",
    "12": "The world is ending because an influencer tried to host a 'gender reveal' party in the ruins of Atlantis.",
    "13": "A new plague has arrived because someone tried to pet a glowing fish in the Mariana Trench using a Slim Jim.",
    "14": "The Bermuda Triangle has released a virus that makes everyone speak in pirate slang after a yacht lost its Wi-Fi.",
    "15": "BREAKING: A jellyfish-based virus is spreading because a surfer tried to use a Portuguese man-o'-war as a hairpiece."
};

// Initialize the flow
function initOpeningScreen() {
    showOutbreakReport();
}

// Phase 1: Outbreak Report Popup
function showOutbreakReport() {
    const storyKeys = Object.keys(PRESET_STORIES);
    const randomKey = storyKeys[Math.floor(Math.random() * storyKeys.length)];
    const story = PRESET_STORIES[randomKey];

    const popup = document.createElement('div');
    popup.id = 'outbreakReportPopup';
    popup.className = 'story-popup-overlay';
    
    popup.innerHTML = `
        <div class="story-popup-container">
            <div class="story-popup-header">
                <div class="story-popup-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                        <path d="M2 17l10 5 10-5"/>
                        <path d="M2 12l10 5 10-5"/>
                    </svg>
                </div>
                <h2 class="story-popup-title">OUTBREAK REPORT</h2>
            </div>
            <div class="story-popup-content">
                <p class="story-text">${story}</p>
            </div>
            <div class="story-popup-info">
                <p><strong>YOUR GOAL:</strong> Infect 60% of the global population before a vaccine is developed.</p>
                <p><strong>AGENT:</strong> AI coordinator develops vaccines & containment. Outsmart it.</p>
                <p><strong>UTILITY:</strong> Your score - balanced from infection spread, deaths, and GDP.</p>
                <p><strong>GDP:</strong> Global economic health. Countries with closed borders lose GDP.</p>
            </div>
            <div class="story-popup-footer">
                <button class="story-begin-btn" id="continueBtn" style="width: 100%">CONTINUE TO DEPLOYMENT</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(popup);
    requestAnimationFrame(() => popup.classList.add('visible'));
    
    document.getElementById('continueBtn').addEventListener('click', () => {
        popup.classList.remove('visible');
        setTimeout(() => {
            popup.remove();
            showCountrySelection();
        }, 300);
    });
}

// Phase 2: Country Selection Popup
function showCountrySelection() {
    const popup = document.createElement('div');
    popup.id = 'countrySelectionPopup';
    popup.className = 'story-popup-overlay';
    
    popup.innerHTML = `
        <div class="story-popup-container">
            <div class="story-popup-header">
                <div class="story-popup-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/>
                        <path d="M2 12h20"/>
                    </svg>
                </div>
                <h2 class="story-popup-title">SELECT DEPLOYMENT ZONE</h2>
            </div>
            <div class="story-popup-content">
                <div class="country-buttons" id="popupCountryButtons" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin: 20px 0;">
                    <!-- Buttons populated by JS -->
                </div>
            </div>
            <div class="story-popup-footer">
                <span style="font-size: 10px; color: var(--text-muted); text-align: center; width: 100%;">SELECT A COUNTRY TO SEED THE INFECTION</span>
            </div>
        </div>
    `;
    
    document.body.appendChild(popup);
    requestAnimationFrame(() => popup.classList.add('visible'));
    
    const container = document.getElementById('popupCountryButtons');
    COUNTRIES.forEach(country => {
        const btn = document.createElement('button');
        btn.className = 'country-btn';
        btn.textContent = country;
        btn.addEventListener('click', () => deployVirus(country, popup));
        container.appendChild(btn);
    });
}

// Deploy virus and close everything
async function deployVirus(country, popup) {
    // Use a temporary overlay to show loading
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'story-popup-overlay visible';
    loadingOverlay.innerHTML = `
        <div class="story-popup-container" style="text-align: center; padding: 40px;">
            <h2 class="story-popup-title">DEPLOYING VIRUS...</h2>
            <p style="margin-top: 20px; color: var(--text-muted);">Seeding infection in ${country}</p>
        </div>
    `;
    document.body.appendChild(loadingOverlay);
    
    if (popup) {
        popup.classList.remove('visible');
        setTimeout(() => popup.remove(), 300);
    }
    
    try {
        const response = await fetch('/deploy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ country })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            loadingOverlay.classList.remove('visible');
            setTimeout(() => loadingOverlay.remove(), 300);
        } else {
            loadingOverlay.remove();
            alert(`Failed to deploy: ${result.message}`);
            // Re-show country selection if failed
            showCountrySelection();
        }
    } catch (error) {
        console.error('Deploy error:', error);
        loadingOverlay.remove();
        alert('Network error. Please try again.');
        showCountrySelection();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initOpeningScreen);

export { initOpeningScreen, showOutbreakReport };
