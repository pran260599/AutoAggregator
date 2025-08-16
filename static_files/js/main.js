// AutoAggregator/static_files/js/main.js

console.log("DEBUG: Script started. --- REAL AUTHENTICATION PHASE ---");

// --- API Base URL (Global Constant) ---
const API_BASE_URL = "http://127.0.0.1:8000/api";

// --- GLOBAL VARIABLES FOR DOM ELEMENTS (Declared here, assigned in DOMContentLoaded) ---
// These will be assigned values inside the DOMContentLoaded listener.
let carGrid, loadingDiv, searchMakeInput, searchModelInput, searchYearSelect,
  searchPriceRange, priceValueSpan, quickFilterButtons, backToTopBtn,
  mobileMenuBtn, mobileNavOverlay, closeMobileMenuBtn, mobileNavLinks, mainNavbar, sections;

let personalizedRecSection, personalizedRecTitle, personalizedCarGrid,
  loadingPersonalizedCars;

// NEW DOM Elements for Real Authentication
let authModalOverlay, closeAuthModalBtn, loginSection, registerSection,
  loginForm, loginUsernameInput, loginPasswordInput, loginSubmitBtn, loginAuthStatus,
  registerForm, registerUsernameInput, registerEmailInput, registerPasswordInput, registerConfirmPasswordInput, registerSubmitBtn, registerAuthStatus,
  authToggleLink, authToggleButton, logoutBtn, userDisplayLink, profileLink; // userDisplayLink will show "Welcome, [Username]!"

let currentLoggedInUserId = null;
let currentLoggedInUsername = null;


// --- GLOBAL HELPER FUNCTIONS (Must be defined before DOMContentLoaded calls them) ---
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function renderCarCard(car) {
  const make = car.make || "N/A";
  const model = car.model || "N/A";
  const year = car.year || "N/A";
  const msrpStarting = car.msrp_starting || null;
  const price = msrpStarting
    ? `Starting at $${parseFloat(msrpStarting).toLocaleString()}`
    : "Price N/A";
  const rating =
    car.overall_rating !== null
      ? parseFloat(car.overall_rating).toFixed(1)
      : "N/A";
  const aiInsight =
    car.ai_insight_summary || "No detailed AI analysis available yet.";

  let featuresDisplay = "N/A";
  if (Array.isArray(car.top_pros) && car.top_pros.length > 0) {
    featuresDisplay = car.top_pros
      .map((p) => {
        if (
          p.description &&
          p.description.toLowerCase() !== p.aspect.toLowerCase() &&
          p.description !== "Good" &&
          p.description !== "Poor"
        ) {
          return `${p.aspect}: ${p.description}`;
        }
        return p.aspect;
      })
      .join(" • ");
  } else if (car.body_type) {
    featuresDisplay = car.body_type;
  } else {
    featuresDisplay = "Key Features";
  }

  let consDisplay = "";
  if (Array.isArray(car.top_cons) && car.top_cons.length > 0) {
    const consList = car.top_cons
      .map((c) => {
        if (
          c.description &&
          c.description.toLowerCase() !== c.aspect.toLowerCase() &&
          c.description !== "Good" &&
          c.description !== "Poor"
        ) {
          return `${c.aspect}: ${c.description}`;
        }
        return c.aspect;
      })
      .join(" • ");
    consDisplay = `<div class="ai-cons"><strong style="color: var(--accent-red);">Cons:</strong> ${consList}</div>`;
  }

  const imageUrl =
    car.main_image_url ||
    `https://picsum.photos/320/220?random=${Math.floor(
      Math.random() * 1000
    )}`;

  let starHtml = "";
  if (car.overall_rating !== null) {
    const fullStars = "★".repeat(Math.floor(car.overall_rating));
    const emptyStars = "☆".repeat(5 - Math.floor(car.overall_rating));
    starHtml = `<span class="stars" aria-label="${car.overall_rating} out of 5 stars">${fullStars}${emptyStars}</span>`;
  } else {
    starHtml = `<span class="rating-text">No Rating</span>`;
  }

  return `
          <div class="car-card">
              <div class="car-image-wrapper">
                  <img src="${imageUrl}" alt="${year} ${make} ${model}">
              </div>
              <div class="car-info">
                  <div class="car-title">${year} ${make} ${model}</div>
                  <div class="car-price">${price}</div>
                  <div class="car-rating">
                      ${starHtml}
                      <span class="rating-text">${rating !== "N/A" ? rating + "/5" : ""
    }</span>
                      ${car.id
      ? `<span class="rating-text"> (ID: ${car.id})</span>`
      : ""
    } 
                  </div>
                  <div class="car-features">${featuresDisplay}</div> 
                  ${consDisplay} 
                  <div class="ai-insight-card">
                      <strong>AI Insight:</strong> "${aiInsight}"
                  </div>
                  <button class="view-details-btn" data-car-id="${car.id
    }">View Details & Reviews</button>
              </div>
          </div>
      `;
}

async function fetchAndDisplayCars(params = {}) {
  loadingDiv.classList.add("show");
  carGrid.style.display = "none";

  let queryString = new URLSearchParams(params).toString();
  if (queryString) {
    queryString = `?${queryString}`;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/cars/${queryString}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();

    carGrid.innerHTML = "";
    const carsToDisplay = data.results || data;

    if (carsToDisplay.length === 0) {
      carGrid.innerHTML =
        '<p style="text-align:center; padding: 2rem; color: var(--medium-gray-text);">No cars found matching your criteria. Try adjusting your search!</p>';
    } else {
      carsToDisplay.forEach((car) => {
        carGrid.innerHTML += renderCarCard(car);
      });
    }
  } catch (error) {
    console.error("Error fetching cars:", error);
    carGrid.innerHTML = `<p style="text-align:center; padding: 2rem; color: var(--accent-red);">Failed to load cars. Please ensure your Django server is running and accessible. (${error.message})</p>`;
  } finally {
    loadingDiv.classList.remove("show");
    carGrid.style.display = "grid";
    document
      .querySelectorAll("#carGrid .view-details-btn")
      .forEach((button) => {
        button.addEventListener("click", (event) => {
          viewCarDetails(event.target.dataset.carId);
        });
      });
  }
}

async function fetchAndDisplayWeeklyPick() {
  const aiPickCard = document.querySelector(".ai-pick-card");
  const aiPickImage = aiPickCard.querySelector(".ai-pick-image img");
  const aiPickContentH3 = aiPickCard.querySelector(".ai-pick-content h3");
  const aiPickContentP = aiPickCard.querySelector(".ai-pick-content p");
  const aiPickBtn = aiPickCard.querySelector(".ai-pick-btn");

  try {
    const response = await fetch(
      `${API_BASE_URL}/cars/weekly_recommendation/`
    );
    if (!response.ok) {
      if (response.status === 404) {
        aiPickCard.innerHTML = `<p style="text-align:center; padding: 2rem; color: var(--medium-gray-text);">No weekly recommendation available at this time.</p>`;
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const car = await response.json();

    aiPickImage.src =
      car.main_image_url ||
      `https://picsum.photos/500/300?random=${Math.floor(
        Math.random() * 1000
      )}`;
    aiPickImage.alt = `${car.year} ${car.make} ${car.model} - AI Pick`;
    aiPickContentH3.textContent = `${car.year} ${car.make} ${car.model}`;

    let insightHtml = `<p>${car.ai_insight_summary || "No detailed AI analysis available yet."
      }</p>`;

    let prosDisplay = "";
    if (Array.isArray(car.top_pros) && car.top_pros.length > 0) {
      const prosList = car.top_pros
        .map((p) => {
          if (
            p.description &&
            p.description.toLowerCase() !== p.aspect.toLowerCase() &&
            p.description !== "Good" &&
            p.description !== "Poor"
          ) {
            return `${p.aspect}: ${p.description}`;
          }
          return p.aspect;
        })
        .join(" • ");
      prosDisplay = `<div class="ai-pros-display" style="margin-top: var(--spacing-sm);"><strong style="color: var(--success-green);">Pros:</strong> ${prosList}</div>`;
    }

    let consDisplay = "";
    if (Array.isArray(car.top_cons) && car.top_cons.length > 0) {
      const consList = car.top_cons
        .map((c) => {
          if (
            c.description &&
            c.description.toLowerCase() !== c.aspect.toLowerCase() &&
            c.description !== "Good" &&
            c.description !== "Poor"
          ) {
            return `${c.aspect}: ${c.description}`;
          }
          return c.aspect;
        })
        .join(" • ");
      consDisplay = `<div class="ai-cons-display" style="margin-top: var(--spacing-sm);"><strong style="color: var(--accent-red);">Cons:</strong> ${consList}</div>`;
    }

    aiPickContentP.innerHTML = `${insightHtml}${prosDisplay}${consDisplay}`;

    aiPickBtn.href = `#car-details-${car.id}`; // Placeholder
    aiPickBtn.setAttribute("data-car-id", car.id);
    if (aiPickBtn.tagName === "BUTTON") {
      aiPickBtn.onclick = () => viewCarDetails(car.id);
    }
  } catch (error) {
    console.error("Error fetching weekly recommendation:", error);
    aiPickCard.innerHTML = `<p style="text-align:center; padding: 2rem; color: var(--accent-red);">Failed to load recommendation. (${error.message})</p>`;
  }
}

// --- Core function to fetch personalized recommendations for the *current* Django session user ---
// This function remains largely the same, but currentLoggedInUserId/Username are now managed by real login
async function fetchAndDisplayPersonalizedRecommendations() {
  // We no longer rely on simulatedUserIdInput.value directly for the backend call.
  // We rely on the Django session cookie.
  // currentLoggedInUserId and currentLoggedInUsername are for FE display only, but still control when this is called.

  personalizedRecTitle.textContent = `Recommended For You, ${currentLoggedInUsername || 'User'}!`;
  loadingPersonalizedCars.classList.add('show');
  personalizedCarGrid.style.display = 'none';

  try {
    const csrfToken = getCookie('csrftoken');

    const response = await fetch(`${API_BASE_URL}/cars/personalized_recommendations/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
    });

    if (response.status === 401) { // User is not authenticated with Django
      personalizedRecTitle.textContent = "Log In to See Your Personalized Picks!";
      personalizedCarGrid.innerHTML = `<p style="text-align:center; padding: 2rem; color: var(--medium-gray-text);">Please log in to your account to get personalized recommendations.</p>`;
      return; // Stop here, don't try to render cars
    }
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();

    personalizedCarGrid.innerHTML = '';
    if (data.length === 0) {
      personalizedCarGrid.innerHTML = '<p style="text-align:center; padding: 2rem; color: var(--medium-gray-text);">No personalized recommendations found at this time. Explore more cars!</p>';
    } else {
      data.forEach(car => {
        personalizedCarGrid.innerHTML += renderCarCard(car);
      });
    }
  } catch (error) {
    console.error("Error fetching personalized recommendations:", error);
    personalizedCarGrid.innerHTML = `<p style="text-align:center; padding: 2rem; color: var(--accent-red);">Failed to load personalized recommendations. (${error.message})</p>`;
  } finally {
    loadingPersonalizedCars.classList.remove('show');
    personalizedCarGrid.style.display = 'grid';
    document.querySelectorAll('#personalizedCarGrid .view-details-btn').forEach(button => {
      button.addEventListener('click', (event) => {
        viewCarDetails(event.target.dataset.carId);
      });
    });
  }
}

// --- NEW: Profile Page Specific Functions ---

// Function to fetch and display user's profile details
async function fetchAndDisplayUserProfile() {
    const profileUsernameElement = document.getElementById('profileUsername');
    const profileEmailElement = document.getElementById('profileEmail');

    if (!currentLoggedInUserId) {
        if (profileUsernameElement) profileUsernameElement.textContent = "Please log in to view your profile.";
        if (profileEmailElement) profileEmailElement.textContent = "";
        return;
    }

    try {
        const csrfToken = getCookie('csrftoken');
        const response = await fetch(`${API_BASE_URL}/users/${currentLoggedInUserId}/`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-CSRFToken': csrfToken,
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const userData = await response.json();

        if (profileUsernameElement) profileUsernameElement.textContent = `Welcome, ${userData.username}!`;
        if (profileEmailElement) profileEmailElement.textContent = `Email: ${userData.email}`;

    } catch (error) {
        console.error("Error fetching user profile:", error);
        if (profileUsernameElement) profileUsernameElement.textContent = "Error loading profile.";
        if (profileEmailElement) profileEmailElement.textContent = `(${error.message})`;
    }
}

// Function to fetch and display user's viewed cars
async function fetchAndDisplayViewedCars() {
    const viewedCarsList = document.getElementById('viewedCarsList');
    if (!viewedCarsList) return; // Exit if element not found

    if (!currentLoggedInUserId) {
        viewedCarsList.innerHTML = '<p>Log in to see your viewed cars.</p>';
        return;
    }

    viewedCarsList.innerHTML = '<div class="spinner"></div> Loading viewed cars...'; // Show spinner

    try {
        const csrfToken = getCookie('csrftoken');
        const response = await fetch(`${API_BASE_URL}/car-views/?user=${currentLoggedInUserId}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-CSRFToken': csrfToken,
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        const viewedCars = data.results || data; // Handle pagination

        if (viewedCars.length === 0) {
            viewedCarsList.innerHTML = '<p>No viewed cars yet.</p>';
        } else {
            let html = '<ul>';
            viewedCars.forEach(view => {
                html += `<li>${view.car.year} ${view.car.make} ${view.car.model} (Viewed: ${new Date(view.view_date).toLocaleString()})</li>`;
            });
            html += '</ul>';
            viewedCarsList.innerHTML = html;
        }
    } catch (error) {
        console.error("Error fetching viewed cars:", error);
        viewedCarsList.innerHTML = `<p style="color: var(--accent-red);">Failed to load viewed cars. (${error.message})</p>`;
    }
}

// Function to fetch and display user's saved cars
async function fetchAndDisplaySavedCars() {
    const savedCarsList = document.getElementById('savedCarsList');
    if (!savedCarsList) return; // Exit if element not found

    if (!currentLoggedInUserId) {
        savedCarsList.innerHTML = '<p>Log in to see your saved cars.</p>';
        return;
    }

    savedCarsList.innerHTML = '<div class="spinner"></div> Loading saved cars...'; // Show spinner

    try {
        const csrfToken = getCookie('csrftoken');
        const response = await fetch(`${API_BASE_URL}/car-saves/?user=${currentLoggedInUserId}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-CSRFToken': csrfToken,
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        const savedCars = data.results || data; // Handle pagination

        if (savedCars.length === 0) {
            savedCarsList.innerHTML = '<p>No saved cars yet.</p>';
        } else {
            let html = '<ul>';
            savedCars.forEach(save => {
                html += `<li>${save.car.year} ${save.car.make} ${save.car.model} (Saved: ${new Date(save.save_date).toLocaleString()})</li>`;
            });
            html += '</ul>';
            savedCarsList.innerHTML = html;
        }
    } catch (error) {
        console.error("Error fetching saved cars:", error);
        savedCarsList.innerHTML = `<p style="color: var(--accent-red);">Failed to load saved cars. (${error.message})</p>`;
    }
}

// Function to fetch and display user's search history
async function fetchAndDisplaySearchHistory() {
    const searchHistoryList = document.getElementById('searchHistoryList');
    if (!searchHistoryList) return; // Exit if element not found

    if (!currentLoggedInUserId) {
        searchHistoryList.innerHTML = '<p>Log in to see your search history.</p>';
        return;
    }

    searchHistoryList.innerHTML = '<div class="spinner"></div> Loading search history...'; // Show spinner

    try {
        const csrfToken = getCookie('csrftoken');
        const response = await fetch(`${API_BASE_URL}/search-queries/?user=${currentLoggedInUserId}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-CSRFToken': csrfToken,
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        const searchQueries = data.results || data; // Handle pagination

        if (searchQueries.length === 0) {
            searchHistoryList.innerHTML = '<p>No search history yet.</p>';
        } else {
            let html = '<ul>';
            searchQueries.forEach(query => {
                html += `<li>Searched for "${query.query_text}" on ${new Date(query.timestamp).toLocaleString()}</li>`;
            });
            html += '</ul>';
            searchHistoryList.innerHTML = html;
        }
    } catch (error) {
        console.error("Error fetching search history:", error);
        searchHistoryList.innerHTML = `<p style="color: var(--accent-red);">Failed to load search history. (${error.message})</p>`;
    }
}

// --- Event Handler Functions (Called by event listeners) ---
function performSearch() {
  const makeTerm = searchMakeInput.value.toLowerCase().trim();
  const modelTerm = searchModelInput.value.toLowerCase().trim();
  const yearTerm = searchYearSelect.value;
  const maxPrice = parseInt(searchPriceRange.value);

  const params = {};
  if (makeTerm) params.make__icontains = makeTerm;
  if (modelTerm) params.model__icontains = modelTerm;
  if (yearTerm) params.year = yearTerm;
  if (maxPrice < 100000) params.msrp_starting__lte = maxPrice;

  quickFilterButtons.forEach((btn) => btn.classList.remove("active"));
  fetchAndDisplayCars(params);
}

function updatePriceRangeDisplay() {
  priceValueSpan.textContent = `$${parseInt(this.value).toLocaleString()}${this.value === "100000" ? "+" : ""}`;
}

function startSearch() {
  document.getElementById("search-section").scrollIntoView({ behavior: "smooth" });
  searchMakeInput.focus();
  quickFilterButtons.forEach((btn) => btn.classList.remove("active"));
}

function handleNavbarScroll() {
  if (window.pageYOffset > 50) {
    mainNavbar.classList.add("scrolled");
  } else {
    mainNavbar.classList.remove("scrolled");
  }
}

function handleSmoothScroll(e) {
  e.preventDefault();
  const targetId = this.getAttribute("href");
  const targetElement = document.querySelector(targetId);

  // Only prevent default and scroll if it's an in-page anchor link
  if (targetId.startsWith('#')) { // <--- ADD THIS CHECK
    e.preventDefault(); // Prevent default only for in-page anchors
    const targetElement = document.querySelector(targetId);
    if (targetElement) {
      targetElement.scrollIntoView({ behavior: "smooth" });
    } else if (targetId === "#home") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }
  document.querySelectorAll(".nav-links a").forEach((link) => link.classList.remove("active"));
  const desktopNavLink = document.querySelector(`.nav-links a[href="${targetId}"]`);
  if (desktopNavLink) { desktopNavLink.classList.add("active"); }
  if (mobileNavOverlay.classList.contains("active")) {
    mobileNavOverlay.classList.remove("active");
    document.body.style.overflow = "";
    mobileMenuBtn.setAttribute("aria-expanded", "false");
  }
}

function handleBackToTop() {
  window.scrollTo({ top: 0, behavior: "smooth" });
  document.querySelectorAll(".nav-links a").forEach((link) => link.classList.remove("active"));
  document.querySelector('.nav-links a[href="#home"]').classList.add("active");
}

function toggleMobileMenu() {
  mobileNavOverlay.classList.add("active");
  document.body.style.overflow = "hidden";
  mobileMenuBtn.setAttribute("aria-expanded", "true");
}

function closeMobileMenu() {
  mobileNavOverlay.classList.remove("active");
  document.body.style.overflow = "";
  mobileMenuBtn.setAttribute("aria-expanded", "false");
}

function closeMobileOverlayClick(e) {
  if (e.target === mobileNavOverlay) {
    mobileNavOverlay.classList.remove("active");
    document.body.style.overflow = "";
    mobileMenuBtn.setAttribute("aria-expanded", "false");
  }
}

function handleScrollSpy() {
  let current = "";
  sections.forEach((section) => {
    const sectionTop = section.offsetTop;
    const sectionHeight = section.clientHeight;
    if (pageYOffset >= sectionTop - 150) {
      current = section.getAttribute("id");
    }
  });

  document.querySelectorAll(".nav-links a").forEach((link) => {
    link.classList.remove("active");
    if (link.getAttribute("href") === `#${current}`) {
      link.classList.add("active");
    }
  });
}

// --- NEW: Authentication UI Management Function ---
function updateAuthUI() {
  // Hide all auth sections in modal initially
  loginSection.classList.remove('active');
  registerSection.classList.remove('active');

  // Clear any previous status messages
  loginAuthStatus.textContent = '';
  registerAuthStatus.textContent = '';

  // Check if user is logged in (via localStorage, which will be set by real login API)
  const storedUserId = localStorage.getItem("loggedInUserId");
  const storedUsername = localStorage.getItem("loggedInUsername");

  if (storedUserId && storedUsername) {
    currentLoggedInUserId = parseInt(storedUserId);
    currentLoggedInUsername = storedUsername;

    if (userDisplayLink) {
      userDisplayLink.textContent = `Welcome, ${currentLoggedInUsername}!`;
      userDisplayLink.style.display = 'inline-block';
    }
    if (logoutBtn) logoutBtn.style.display = 'inline-block';
    if (loginPromptToggle) loginPromptToggle.style.display = 'none';
    if (profileLink) profileLink.style.display = 'inline-block';
  } else {
    currentLoggedInUserId = null;
    currentLoggedInUsername = null;

    if (userDisplayLink) userDisplayLink.textContent = '';
    if (userDisplayLink) userDisplayLink.style.display = 'none';
    if (logoutBtn) logoutBtn.style.display = 'none';
    if (loginPromptToggle) loginPromptToggle.style.display = 'inline-block';
    if (profileLink) profileLink.style.display = 'none';
  }

  // Always call personalized recommendations after UI updates
  fetchAndDisplayPersonalizedRecommendations();
}

// --- NEW: Handle User Registration API Call ---
async function handleUserRegistration(event) {
  event.preventDefault(); // Prevent default form submission

  const username = registerUsernameInput.value.trim();
  const email = registerEmailInput.value.trim();
  const password = registerPasswordInput.value.trim();
  const confirmPassword = registerConfirmPasswordInput.value.trim();

  if (!username || !email || !password || !confirmPassword) {
    registerAuthStatus.textContent = "All fields are required.";
    registerAuthStatus.style.color = "var(--accent-red)";
    return;
  }
  if (password !== confirmPassword) {
    registerAuthStatus.textContent = "Passwords do not match.";
    registerAuthStatus.style.color = "var(--accent-red)";
    return;
  }

  registerAuthStatus.textContent = "Registering...";
  registerAuthStatus.style.color = "var(--medium-gray-text)";

  try {
    const csrfToken = getCookie('csrftoken');
    const response = await fetch(`${API_BASE_URL}/register/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({ username, email, password }),
    });

    const data = await response.json();

    if (response.ok) { // Status 200-299
      registerAuthStatus.textContent = "Registration successful! You are now logged in.";
      registerAuthStatus.style.color = "var(--success-green)";

      // Automatically log in the user on successful registration
      localStorage.setItem("loggedInUserId", data.user_id); // Assuming backend sends user_id
      localStorage.setItem("loggedInUsername", data.username); // Assuming backend sends username
      updateAuthUI(); // Update UI to logged-in state
      authModalOverlay.classList.remove('active'); // Close modal
      document.body.style.overflow = '';
    } else {
      let errorMessage = "Registration failed. ";
      if (data.username) errorMessage += `Username: ${data.username.join(' ')} `;
      if (data.email) errorMessage += `Email: ${data.email.join(' ')} `;
      if (data.password) errorMessage += `Password: ${data.password.join(' ')} `;
      if (data.detail) errorMessage += data.detail; // General error detail

      registerAuthStatus.textContent = errorMessage.trim();
      registerAuthStatus.style.color = "var(--accent-red)";
    }
  } catch (error) {
    console.error("Registration API error:", error);
    registerAuthStatus.textContent = `An unexpected error occurred during registration. (${error.message})`;
    registerAuthStatus.style.color = "var(--accent-red)";
  }
}

// --- NEW: Handle User Login API Call ---
async function handleUserLogin(event) {
  event.preventDefault(); // Prevent default form submission

  const username = loginUsernameInput.value.trim();
  const password = loginPasswordInput.value.trim();

  if (!username || !password) {
    loginAuthStatus.textContent = "Username and password are required.";
    loginAuthStatus.style.color = "var(--accent-red)";
    return;
  }

  loginAuthStatus.textContent = "Logging in...";
  loginAuthStatus.style.color = "var(--medium-gray-text)";

  try {
    const csrfToken = getCookie('csrftoken');
    const response = await fetch(`${API_BASE_URL}/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({ username, password }),
    });

    const data = await response.json();

    if (response.ok) { // Status 200-299
      loginAuthStatus.textContent = "Login successful!";
      loginAuthStatus.style.color = "var(--success-green)";

      localStorage.setItem("loggedInUserId", data.user_id); // Assuming backend sends user_id
      localStorage.setItem("loggedInUsername", data.username); // Assuming backend sends username
      updateAuthUI(); // Update UI to logged-in state
      authModalOverlay.classList.remove('active'); // Close modal
      document.body.style.overflow = '';
    } else {
      let errorMessage = "Login failed. ";
      if (data.detail) errorMessage += data.detail; // E.g., "Invalid credentials"
      else if (data.non_field_errors) errorMessage += data.non_field_errors.join(' '); // Generic errors

      loginAuthStatus.textContent = errorMessage.trim();
      loginAuthStatus.style.color = "var(--accent-red)";
    }
  } catch (error) {
    console.error("Login API error:", error);
    loginAuthStatus.textContent = `An unexpected error occurred during login. (${error.message})`;
    loginAuthStatus.style.color = "var(--accent-red)";
  }
}

// --- NEW: Handle User Logout API Call ---
async function handleUserLogout() {
  try {
    const csrfToken = getCookie('csrftoken');
    const response = await fetch(`${API_BASE_URL}/logout/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
    });

    if (response.ok) {
      localStorage.removeItem('loggedInUserId');
      localStorage.removeItem('loggedInUsername');
      updateAuthUI(); // Update UI to logged-out state
      console.log("DEBUG: Successfully logged out.");
    } else {
      console.error("Logout failed:", await response.json());
    }
  } catch (error) {
    console.error("Logout API error:", error);
  }
}

// --- INITIALIZATION SCRIPT (Runs when DOM is fully loaded) ---
document.addEventListener("DOMContentLoaded", () => {
  console.log("DEBUG: DOMContentLoaded fired. Initializing elements and listeners. --- Real Auth ---");

  // --- All DOM Element Retrievals (Assign values to global variables) ---
  carGrid = document.getElementById("carGrid");
  loadingDiv = document.getElementById("loadingCars");
  searchMakeInput = document.getElementById("searchMake");
  searchModelInput = document.getElementById("searchModel");
  searchYearSelect = document.getElementById("searchYear");
  searchPriceRange = document.getElementById("searchPriceRange");
  priceValueSpan = document.getElementById("priceValue");
  quickFilterButtons = document.querySelectorAll(".filter-btn");
  backToTopBtn = document.getElementById("backToTopBtn");
  mobileMenuBtn = document.getElementById("mobileMenuBtn");
  mobileNavOverlay = document.getElementById("mobileNavOverlay");
  closeMobileMenuBtn = document.getElementById("closeMobileMenuBtn");
  mainNavbar = document.getElementById("mainNavbar");

  personalizedRecSection = document.getElementById('personalized-recommendations-section');
  personalizedRecTitle = document.getElementById('personalizedRecTitle');
  personalizedCarGrid = document.getElementById('personalizedCarGrid');
  loadingPersonalizedCars = document.getElementById('loadingPersonalizedCars');

  // NEW AUTH DOM Element Retrievals
  authModalOverlay = document.getElementById('authModalOverlay');
  closeAuthModalBtn = document.getElementById('closeAuthModalBtn');
  loginSection = document.getElementById('loginSection');
  registerSection = document.getElementById('registerSection');
  loginForm = document.getElementById('loginForm');
  loginUsernameInput = document.getElementById('loginUsername');
  loginPasswordInput = document.getElementById('loginPassword');
  loginSubmitBtn = document.getElementById('loginSubmitBtn');
  loginAuthStatus = document.getElementById('loginAuthStatus');
  registerForm = document.getElementById('registerForm');
  registerUsernameInput = document.getElementById('registerUsernameInput');
  registerEmailInput = document.getElementById('registerEmailInput');
  registerPasswordInput = document.getElementById('registerPasswordInput');
  registerConfirmPasswordInput = document.getElementById('registerConfirmPasswordInput');
  registerSubmitBtn = document.getElementById('registerSubmitBtn');
  registerAuthStatus = document.getElementById('registerAuthStatus');
  authToggleLink = document.getElementById('authToggleLink');
  logoutBtn = document.getElementById('logoutBtn');
  userDisplayLink = document.getElementById('userDisplayLink');
  profileLink = document.getElementById('profileLink');

  sections = document.querySelectorAll("section[id]"); // For scroll spy

  // Initial UI setup based on localStorage & fetching data
  updateAuthUI(); // Call this first to set login/logout state and trigger personalized recs
  fetchAndDisplayCars();
  fetchAndDisplayWeeklyPick();

   if (document.body.id === 'user-profile-page') { // <--- NEW CHECK FOR PROFILE PAGE
      fetchAndDisplayUserProfile();
      fetchAndDisplayViewedCars();
      fetchAndDisplaySavedCars();
      fetchAndDisplaySearchHistory();
  } else {
      // Existing homepage initialization
      updateAuthUI();
      fetchAndDisplayCars();
      fetchAndDisplayWeeklyPick();
  }

  // --- All Event Listeners Attached Here ---
  searchPriceRange.addEventListener("input", updatePriceRangeDisplay);
  document.querySelector('.search-btn').addEventListener('click', performSearch);

  quickFilterButtons.forEach((button) => {
    button.addEventListener("click", function () {
      quickFilterButtons.forEach((btn) => btn.classList.remove("active"));
      this.classList.add("active");
      searchMakeInput.value = "";
      searchModelInput.value = "";
      searchYearSelect.value = "";
      priceValueSpan.textContent = "$100,000+";
      const category = this.dataset.filter;
      fetchAndDisplayCars({ body_type__icontains: category });
      document.getElementById("featured-cars-section").scrollIntoView({ behavior: "smooth" });
    });
  });

  document.querySelector('.cta-btn').addEventListener("click", startSearch);

  if (backToTopBtn) { backToTopBtn.addEventListener("click", handleBackToTop); }
  if (mobileMenuBtn) { mobileMenuBtn.addEventListener("click", toggleMobileMenu); }
  if (closeMobileMenuBtn) { closeMobileMenuBtn.addEventListener("click", closeMobileMenu); }
  if (mobileNavOverlay) { mobileNavOverlay.addEventListener("click", closeMobileOverlayClick); }

  // NEW AUTH Event Listeners
  if (authModalOverlay) {
    authModalOverlay.addEventListener('click', (e) => { // Close modal if click outside content
      if (e.target === authModalOverlay) {
        authModalOverlay.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  }
  if (closeAuthModalBtn) {
    closeAuthModalBtn.addEventListener('click', () => {
      authModalOverlay.classList.remove('active');
      document.body.style.overflow = '';
    });
  }

  // Form Submissions
  if (loginForm) { loginForm.addEventListener('submit', handleUserLogin); }
  if (registerForm) { registerForm.addEventListener('submit', handleUserRegistration); }

  // Toggle between Login/Register forms
  if (authToggleLink) {
    authToggleLink.addEventListener('click', (e) => {
      e.preventDefault();
      if (loginSection.classList.contains('active')) {
        loginSection.classList.remove('active');
        registerSection.classList.add('active');
      } else {
        registerSection.classList.remove('active');
        loginSection.classList.add('active');
      }
      // Clear status messages when toggling
      loginAuthStatus.textContent = '';
      registerAuthStatus.textContent = '';
    });
  }

  // Navbar Auth/Logout Links (New)
  if (loginPromptToggle) { // This is the 'Log in to see your personalized picks' link
    loginPromptToggle.addEventListener('click', (e) => {
      e.preventDefault();
      authModalOverlay.classList.add('active');
      document.body.style.overflow = 'hidden';
      loginSection.classList.add('active'); // Default to showing login form
      registerSection.classList.remove('active');
      loginUsernameInput.focus();
      loginAuthStatus.textContent = ''; // Clear status on open
    });
  }
  if (logoutBtn) {
    logoutBtn.addEventListener('click', handleUserLogout);
  }


  document.querySelectorAll(".nav-links a, .mobile-nav-link").forEach((anchor) => {
    anchor.addEventListener("click", handleSmoothScroll);
  });

  window.addEventListener("scroll", handleNavbarScroll);
  window.addEventListener("scroll", handleScrollSpy);

}); // <--- END OF THE SINGLE DOMContentLoaded LISTENER ---