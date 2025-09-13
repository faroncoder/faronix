Purchases.shared.getCustomerInfo({ customerInfo ->
    val entitlement = customerInfo.entitlements["{{ entitlement }}"]
    val isActive = entitlement?.isActive ?: false

    if (isActive) {
        Log.d("RevenueCat", "✅ Access granted to {{ entitlement }} ({{ license_type }})")
        // TODO: Show premium features
    } else {
        Log.w("RevenueCat", "❌ Access denied")
        // TODO: Redirect to purchase
    }
})
