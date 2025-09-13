const customerInfo = await Purchases.getCustomerInfo();
const isActive = customerInfo.entitlements.active["{{ entitlement }}"];
if (isActive) {
  console.log("✅ Access granted ({{ license_type }})");
  // TODO: Unlock UI or redirect
} else {
  console.warn("❌ Not subscribed ({{ license_type }})");
  // TODO: Show paywall
}
