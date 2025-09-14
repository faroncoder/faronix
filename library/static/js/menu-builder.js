/**
 * Enhanced Sidebar Generator
 * 
 * Supports:
 * - Custom data attributes
 * - External links
 * - Custom icons (both Feather and custom URLs)
 * - Unlimited nesting
 * - Custom CSS classes
 * - Post data for AJAX loading
 */
// Store for sidebar state
const SidebarState = {
    // Key for localStorage
    STORAGE_KEY: 'sidebar_state',
    // Get the current state from localStorage
    getState: function() {
        const savedState = localStorage.getItem(this.STORAGE_KEY);
        return savedState ? JSON.parse(savedState) : { expanded: {}, active: null };
    },
    // Save the current state to localStorage
    saveState: function(state) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(state));
    },
    // Check if a section is expanded
    isExpanded: function(sectionId) {
        const state = this.getState();
        return state.expanded[sectionId] === true;
    },
    // Set a section as expanded or collapsed
    setExpanded: function(sectionId, isExpanded) {
        const state = this.getState();
        state.expanded[sectionId] = isExpanded;
        this.saveState(state);
    },
    // Get the active menu item
    getActive: function() {
        const state = this.getState();
        return state.active;
    },
    // Set the active menu item
    setActive: function(itemId) {
        const state = this.getState();
        state.active = itemId;
        this.saveState(state);
    }
};
// Function to load the sidebar structure from a JSON file
function loadSidebarFromJSON(jsonUrl) {
    // Fetch the JSON file
    fetch(jsonUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Check if the data has a 'sidebar' property
            const sidebarData = data.sidebar || data;
            // Generate the sidebar from the JSON data
            generateSidebar(sidebarData);
            // Initialize feather icons if available
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
            // Setup event listeners for the collapsible sections
            setupSidebarEventListeners();
            // Apply saved state (expanded sections and active item)
            applySavedState();
            // Set active item based on current URL if no active item is set
            if (!SidebarState.getActive()) {
                setActiveItemFromCurrentUrl();
            }
        })
        .catch(error => {
            console.error('Error loading sidebar JSON:', error);
        });
}
// Function to generate the sidebar HTML from JSON data
function generateSidebar(sidebarData) {
    const sidenavMenu = document.querySelector('.sidenav-menu');
    const nav = document.createElement('div');
    nav.className = 'nav accordion';
    nav.id = 'accordionSidenav';
    // Do not clear existing content; append generated sidebar below any static markup
    // Mobile account section (if needed)
    const mobileAccountSection =
        `
        <div class="sidenav-menu-heading d-sm-none">Account</div>
        <a class="nav-link panel-link d-sm-none" href="#!">
            <div class="nav-link panel-link-icon"><i class="fas fa-bell"></i></div>
            Alerts
            <span class="badge bg-warning-soft text-warning ms-auto">4 New!</span>
        </a>
        <a class="nav-link panel-link d-sm-none" href="#!">
            <div class="nav-link panel-link-icon"><i class="fas fa-mail"></i></div>
            Messages
            <span class="badge bg-success-soft text-success ms-auto">2 New!</span>
        </a>
    `;
    nav.innerHTML = mobileAccountSection;
    // Process each section in the sidebar data
    sidebarData.forEach((section, sectionIndex) => {
        // Add section heading
        const headingDiv = document.createElement('div');
        headingDiv.className = 'sidenav-menu-heading';
        headingDiv.textContent = section.heading;
        nav.appendChild(headingDiv);
        // Process section items
        if (section.items && section.items.length > 0) {
            section.items.forEach((item, itemIndex) => {
                const itemContent = generateMenuItem(item, sectionIndex, itemIndex);
                nav.innerHTML += itemContent;
            });
        }
    });
    sidenavMenu.appendChild(nav);
}
// Function to generate menu item HTML (supports nested items)
function generateMenuItem(item, sectionIndex, itemIndex, parentId = null) {
    let html = '';
    // Use provided id or generate one
    const itemId = item.id || (parentId ? `${parentId}_${itemIndex}` : `section${sectionIndex}_item${itemIndex}`);
    if (item.items && item.items.length > 0) {
        // This is a collapsible menu item with children
        const expanded = !item.collapsed;
        const collapsedClass = item.collapsed ? 'collapsed' : '';
        const showClass = !item.collapsed ? 'show' : '';
        const customClass = item["placeholder div"] || 'nav-link panel-link';
        // Create the collapsible menu item
        html +=
            `
            <a class="${customClass} ${collapsedClass}" 
               href="${item.href || 'javascript:void(0);'}" 
               data-bs-toggle="collapse" 
               data-bs-target="#collapse${itemId}" 
               aria-expanded="${expanded}" 
               aria-controls="collapse${itemId}"
               data-section-id="${itemId}"
               ${item.parent ? `data-parent="${item.parent}"` : ''}
               ${item.datalink ? `data-link="${item.datalink}"` : ''}
               ${item["data-url"] ? `data-url="${item["data-url"]}"` : ''}
               ${item["data-target"] ? `data-target="${item["data-target"]}"` : ''}
               ${item["data-post-data"] ? `data-post-data='${item["data-post-data"]}'` : ''}
               ${item.child ? `data-child="${item.child}"` : ''}
               id="${itemId}">
        `;
        
        // Add icon
        if (item.icon) {
            if (item.icon.startsWith('http')) {
                // Custom image icon
                html += `<div class="${item["icon span"] || 'nav-link panel-link-icon'}"><img src="${item.icon}" alt="${item.title}" width="24" height="24"></div>`;
            } else {
                // Feather icon
                html += `<div class="${item["icon span"] || 'nav-link panel-link-icon'}"><i class="fas fa-${item.icon}"></i></div>`;
            }
        }
        
        // Add title
        html += `${item.title}`;
        
        // Add badge if specified
        if (item.badge) {
            html += `<span class="badge ${item.badge.class} ms-auto">${item.badge.text}</span>`;
        }
        
        // Add collapse arrow
        html += `<div class="sidenav-collapse-arrow"><i class="fas fa-angle-down"></i></div></a>`;
        
        // Create the collapsible content container
        html += `
            <div class="collapse ${showClass}" id="collapse${itemId}" data-bs-parent="${parentId ? '#collapse' + parentId : '#accordionSidenav'}">
                <nav class="sidenav-menu-nested nav ${item.items.some(subitem => subitem.items && subitem.items.length > 0) ? 'accordion' : ''}" ${item.items.some(subitem => subitem.items && subitem.items.length > 0) ? 'id="accordionSidenav' + itemId + '"' : ''}>
        `;
        
        // Generate nested items
        item.items.forEach((subItem, subIndex) => {
            html += generateMenuItem(subItem, sectionIndex, subIndex, itemId);
        });
        
        html += `</nav></div>`;
    } else {
        // This is a simple menu item (no children)
        const customClass = item["placeholder div"] || 'nav-link panel-link';
        const isExternal = item.url && (item.url.startsWith('http') || item["data-target"] === '_blank');
        const target = isExternal ? '_blank' : '';
        const rel = isExternal ? 'noopener noreferrer' : '';
        
        // For external links use href, for internal use data-url and javascript:void(0)
        html += `<a class="${customClass}" 
                   href="${item.href || (isExternal ? item.url : 'javascript:void(0)')}" 
                   ${!isExternal || item["data-url"] ? `data-url="${item["data-url"] || item.url}"` : ''} 
                   ${target ? `target="${target}"` : ''} 
                   ${rel ? `rel="${rel}"` : ''}
                   ${item["data-target"] ? `data-target="${item["data-target"]}"` : ''} 
                   ${item["data-post-data"] ? `data-post-data='${item["data-post-data"]}'` : ''} 
                   ${item.parent ? `data-parent="${item.parent}"` : ''} 
                   ${item.datalink ? `data-link="${item.datalink}"` : ''}
                   ${item.child ? `data-child="${item.child}"` : ''}
                   data-item-id="${itemId}" 
                   id="${itemId}">`;
        
        // Add icon
        if (item.icon) {
            if (item.icon.startsWith('http')) {
                // Custom image icon
                html += `<div class="${item["icon span"] || 'nav-link panel-link-icon'}"><img src="${item.icon}" alt="${item.title}" width="24" height="24"></div>`;
            } else {
                // Feather icon
                html += `<div class="${item["icon span"] || 'nav-link panel-link-icon'}"><i class="fas fa-${item.icon}"></i></div>`;
            }
        }
        
        // Add title
        html += `${item.title}`;
        
        // Add badge if specified
        if (item.badge) {
            html += `<span class="badge ${item.badge.class} ms-auto">${item.badge.text}</span>`;
        }
        
        html += `</a>`;
    }
    
    return html;
}

// Function to set up event listeners for the sidebar
function setupSidebarEventListeners() {
    // Handle collapsible sections
    document.querySelectorAll('.nav-link[data-bs-toggle="collapse"]').forEach(element => {
        element.addEventListener('click', function() {
            const sectionId = this.getAttribute('data-section-id');
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            
            // Update local storage with the new state
            SidebarState.setExpanded(sectionId, !isExpanded);
        });
    });
    
    // Handle menu item clicks (only for internal links)
    document.querySelectorAll('.nav-link[data-url]:not([target="_blank"])').forEach(element => {
        element.addEventListener('click', function() {
            const itemId = this.getAttribute('data-item-id') || this.getAttribute('id');
            
            // Remove active class from all items
            document.querySelectorAll('.nav-link.active').forEach(el => {
                el.classList.remove('active');
            });
            
            // Add active class to this item
            this.classList.add('active');
            
            // Save active state
            SidebarState.setActive(itemId);
        });
    });
}

// Function to apply saved state (expanded sections and active item)
function applySavedState() {
    const state = SidebarState.getState();
    
    // Apply expanded state to sections
    Object.keys(state.expanded).forEach(sectionId => {
        const isExpanded = state.expanded[sectionId];
        const sectionElement = document.querySelector(`[data-section-id="${sectionId}"]`);
        
        if (sectionElement) {
            const targetId = sectionElement.getAttribute('data-bs-target');
            const targetElement = document.querySelector(targetId);
            
            // Set the expanded attribute
            sectionElement.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
            
            // Add or remove the 'collapsed' class
            if (isExpanded) {
                sectionElement.classList.remove('collapsed');
            } else {
                sectionElement.classList.add('collapsed');
            }
            
            // Add or remove the 'show' class on the target
            if (targetElement) {
                if (isExpanded) {
                    targetElement.classList.add('show');
                } else {
                    targetElement.classList.remove('show');
                }
            }
        }
    });
    
    // Apply active state
    if (state.active) {
        const activeElement = document.querySelector(`[data-item-id="${state.active}"]`) || document.getElementById(state.active);
        if (activeElement) {
            // Remove active class from all items
            document.querySelectorAll('.nav-link.active').forEach(el => {
                el.classList.remove('active');
            });
            
            // Add active class to this item
            activeElement.classList.add('active');
            
            // Expand parent sections if needed
            expandParents(activeElement);
        }
    }
}

// Function to expand all parent sections of an element
function expandParents(element) {
    let parent = element.closest('.collapse');
    
    while (parent) {
        // Find the trigger element for this collapse
        const triggerId = parent.id;
        const trigger = document.querySelector(`[data-bs-target="#${triggerId}"]`);
        
        if (trigger) {
            // Set as expanded
            trigger.setAttribute('aria-expanded', 'true');
            trigger.classList.remove('collapsed');
            
            // Show the collapse
            parent.classList.add('show');
            
            // Update state in localStorage
            const sectionId = trigger.getAttribute('data-section-id');
            if (sectionId) {
                SidebarState.setExpanded(sectionId, true);
            }
            
            // Move up to the next parent
            parent = trigger.closest('.collapse');
        } else {
            break;
        }
    }
}

// Function to set active item based on current URL
function setActiveItemFromCurrentUrl() {
    // Get the current page URL
    const currentUrl = window.location.pathname;
    const filename = currentUrl.split('/').pop();
    
    if (filename) {
        // Find the menu item with this URL
        const menuItem = document.querySelector(`[data-url="${filename}"]`);
        
        if (menuItem) {
            // Get the item ID
            const itemId = menuItem.getAttribute('data-item-id') || menuItem.getAttribute('id');
            
            // Remove active class from all items
            document.querySelectorAll('.nav-link.active').forEach(el => {
                el.classList.remove('active');
            });
            
            // Add active class to this item
            menuItem.classList.add('active');
            
            // Save active state
            SidebarState.setActive(itemId);
            
            // Expand parent sections
            expandParents(menuItem);
            
            return true;
        }
    }
    
    return false;
}

// Initialize the sidebar
function initSidebar(jsonUrl) {
    // Load the sidebar structure from JSON
    loadSidebarFromJSON(jsonUrl);
    
    // Additional initialization can be added here
    
    // If URL parameters are used for content loading, parse them here
    const urlParams = new URLSearchParams(window.location.search);
    const page = urlParams.get('page');
    
    if (page) {
        // Find and activate the corresponding menu item
        const menuItem = document.querySelector(`[data-url="${page}"]`);
        if (menuItem) {
            setTimeout(() => {
                menuItem.click();
            }, 100);
        }
    }
}


// Suggestion by Claude:
// develop scripts to handle compression for AJAX responses