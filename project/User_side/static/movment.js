// Select all sidebar links
const sidebarLinks = document.querySelectorAll(".sidebar a");

// Function to handle click events on sidebar links
function handleSidebarClick(event) {
    event.preventDefault(); // Prevent the default link behavior

    // Remove the 'active' class from all links
    sidebarLinks.forEach(link => link.classList.remove("active"));

    // Add the 'active' class to the clicked link
    this.classList.add("active");

    // Hide all content sections
    document.querySelectorAll(".content-section").forEach(section => {
        section.style.display = "none"; // Hide all sections
    });

    // Show the content section corresponding to the clicked link
    const sectionToShow = this.getAttribute("data-section");
    const targetSection = document.getElementById(sectionToShow);
    
    if (targetSection) {
        targetSection.style.display = "block"; // Show the clicked section
    } else {
        console.error("Target section not found: ", sectionToShow);
    }
}

// Attach event listeners to each link
sidebarLinks.forEach(link => {
    link.addEventListener("click", handleSidebarClick);
});


