// Opening Screen Handler
// Manages country selection and virus story display

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

let selectedCountry = null;
let selectedStory = null;

// Initialize opening screen
function initOpeningScreen() {
    const countryButtonsContainer = document.getElementById('countryButtons');
    
    // Create country buttons
    COUNTRIES.forEach(country => {
        const btn = document.createElement('button');
        btn.className = 'country-btn';
        btn.textContent = country;
        btn.dataset.country = country;
        btn.addEventListener('click', () => selectCountry(country, btn));
        countryButtonsContainer.appendChild(btn);
    });
}

// Select a country and show the story popup
function selectCountry(country, buttonElement) {
    selectedCountry = country;
    
    // Highlight selected button
    const allButtons = document.querySelectorAll('.country-btn');
    allButtons.forEach(btn => btn.classList.remove('selected'));
    buttonElement.classList.add('selected');
    
    // Pick a random story
    const storyKeys = Object.keys(PRESET_STORIES);
    const randomKey = storyKeys[Math.floor(Math.random() * storyKeys.length)];
    selectedStory = PRESET_STORIES[randomKey];
    
    // Hide opening screen with fade
    const openingScreen = document.getElementById('openingScreen');
    openingScreen.style.transition = 'opacity 0.3s ease';
    openingScreen.style.opacity = '0';
    setTimeout(() => {
        openingScreen.classList.add('hidden');
        // Show story popup
        showStoryPopup(country, selectedStory);
    }, 300);
}

// Show story popup over the map
function showStoryPopup(country, story) {
    // Create popup overlay
    const popup = document.createElement('div');
    popup.id = 'storyPopup';
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
            <div class="story-popup-location">
                <span class="location-label">DEPLOYMENT ZONE:</span>
                <span class="location-value">${country}</span>
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
                <button class="story-back-btn" id="backBtn">BACK</button>
                <button class="story-begin-btn" id="beginBtn">BEGIN SIMULATION</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(popup);
    
    // Animate in
    requestAnimationFrame(() => {
        popup.classList.add('visible');
    });
    
    // Add event listeners
    document.getElementById('backBtn').addEventListener('click', hideStoryPopup);
    document.getElementById('beginBtn').addEventListener('click', () => deployVirus(country));
}

// Hide story popup and go back to country selection
function hideStoryPopup() {
    const popup = document.getElementById('storyPopup');
    if (popup) {
        popup.classList.remove('visible');
        setTimeout(() => {
            popup.remove();
            // Show opening screen again
            const openingScreen = document.getElementById('openingScreen');
            openingScreen.classList.remove('hidden');
            openingScreen.style.opacity = '1';
        }, 300);
    }
}

// Deploy virus to selected country
async function deployVirus(country) {
    const beginBtn = document.getElementById('beginBtn');
    const backBtn = document.getElementById('backBtn');
    
    // Disable buttons and show deploying state
    beginBtn.disabled = true;
    backBtn.disabled = true;
    beginBtn.textContent = 'DEPLOYING...';
    beginBtn.classList.add('deploying');
    
    try {
        const response = await fetch('/deploy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ country })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            // Hide popup with fade
            const popup = document.getElementById('storyPopup');
            if (popup) {
                popup.classList.remove('visible');
                setTimeout(() => {
                    popup.remove();
                }, 300);
            }
        } else {
            // Re-enable buttons on failure
            beginBtn.disabled = false;
            backBtn.disabled = false;
            beginBtn.textContent = 'BEGIN SIMULATION';
            beginBtn.classList.remove('deploying');
            alert(`Failed to deploy: ${result.message}`);
        }
    } catch (error) {
        console.error('Deploy error:', error);
        beginBtn.disabled = false;
        backBtn.disabled = false;
        beginBtn.textContent = 'BEGIN SIMULATION';
        beginBtn.classList.remove('deploying');
        alert('Network error. Please try again.');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initOpeningScreen);

export { initOpeningScreen };
