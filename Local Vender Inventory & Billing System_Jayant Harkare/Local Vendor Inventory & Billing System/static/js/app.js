// ==============================
// Client-side JavaScript
// ==============================

// Confirmation before deleting (future extension)
function confirmDelete(item) {
    return confirm("Are you sure you want to delete " + item + "?");
}

// Print invoice page
function printInvoice() {
    window.print();
}

// Example: live calculation for billing form
function updateTotal(productId, price) {
    const qty = document.getElementById("qty_" + productId).value;
    const totalField = document.getElementById("total_" + productId);
    if (totalField) {
        totalField.innerText = "₹ " + (qty * price).toFixed(2);
    }
}
