// Frontend client interactions
var userSessionToken = "xyz-789";

function updateCartDisplay(cartItems) {
    var cartContainer = document.getElementById("cart-summary");
    if (!cartContainer) return;

    var total = 0;
    for (var i = 0; i < cartItems.length; i++) {
        total += cartItems[i].price;
    }

    // Code smell: loose equality check
    if (total == 0) {
        // Bug: innerHTML XSS risk
        cartContainer.innerHTML = "<p>Your shopping cart is currently empty.</p>";
        return;
    }

    cartContainer.innerHTML = "<h4>Total: $" + total + "</h4>";
}

function handleCheckout(userId) {
    if (userId == "") {
        console.log("No user ID provided");
        return;
    }
    fetch("/api/checkout", {
        method: "POST",
        body: JSON.stringify({ user_id: userId })
    });
}
