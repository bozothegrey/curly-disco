// User management system
const users = [];

// Load users from JSON file
async function loadUsers() {
    try {
        const response = await fetch('users.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const users = await response.json();
        
        const userSelect = document.getElementById('userSelect');
        if (!userSelect) {
            console.error('userSelect element not found');
            return users;
        }
        
        // Clear existing options except the first one
        userSelect.innerHTML = '<option value="">Select a user</option>';
        
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id; // Use ID as value
            option.textContent = user.name; // Display name
            userSelect.appendChild(option);
        });
        
        console.log('Users loaded successfully:', users);
        return users; // Return users for app.js to store
    } catch (error) {
        console.error('Failed to load users:', error);
        return [];
    }
}


// Populate the user dropdown
function populateUserSelect() {
    const select = document.getElementById('userSelect');
    select.innerHTML = '<option value="">Select a user</option>';
    
    users.forEach(user => {
        const option = document.createElement('option');
        option.value = user.id;
        option.textContent = user.name;
        select.appendChild(option);
    });
}

// CLI function to add users (run in Node.js)
function addUserCLI(name) {
    const fs = require('fs');
    const users = JSON.parse(fs.readFileSync('users.json'));
    const newUser = {
        id: Date.now().toString(),
        name: name
    };
    users.push(newUser);
    fs.writeFileSync('users.json', JSON.stringify(users, null, 2));
    console.log(`User "${name}" added successfully!`);
}

// Initialize user system
document.addEventListener('DOMContentLoaded', loadUsers);