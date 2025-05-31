// User management system
const users = [];

// Load users from JSON file
async function loadUsers() {
    try {
        const response = await fetch('users.json');
        const data = await response.json();
        users.push(...data);
        populateUserSelect();
    } catch (error) {
        console.error("Error loading users:", error);
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