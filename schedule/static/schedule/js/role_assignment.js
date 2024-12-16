// role_assignment.js

$(document).ready(function () {
    $("#role-assignment-form").on("submit", function (e) {
        e.preventDefault(); // Prevent default form submission

        const formData = $(this).serialize(); // Serialize form data

        $.ajax({
            type: "POST",
            url: window.location.href, // Send the request to the current URL
            data: formData,
            success: function (response) {
                if (response.success) {
                    // Close the modal and refresh the schedules
                    $("#exampleModal").modal('hide');
                    alert(response.message);
                    location.reload(); // Optional: reload the page
                }
            },
            error: function (xhr) {
                if (xhr.status === 400) {
                    const errorData = xhr.responseJSON.error;
                    const errorMessages = Object.values(errorData).flat().join("<br>");
                    $("#modal-error-message").html(`<div class="alert alert-danger">${errorMessages}</div>`);
                } else {
                    $("#modal-error-message").html(`<div class="alert alert-danger">An unexpected error occurred.</div>`);
                }
            }
        });
    });
});