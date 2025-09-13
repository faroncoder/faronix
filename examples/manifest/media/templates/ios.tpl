Purchases.shared.getCustomerInfo { customerInfo, error in
    let entitlement = customerInfo?.entitlements["{{ entitlement }}"]
    let isActive = entitlement?.isActive == true

    if isActive {
        print("✅ iOS Access: {{ entitlement }} ({{ license_type }})")
        // TODO: Unlock features
    } else {
        print("❌ iOS No access")
        // TODO: Show upgrade prompt
    }
}
