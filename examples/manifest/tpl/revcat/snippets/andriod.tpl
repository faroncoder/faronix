const customerInfo = await Purchases.getCustomerInfo();
const isActive = customerInfo.entitlements.active["{{ entitlement }}"];
if (isActive) {
  console.log("✅ Access granted ({{ license_type }})");
  document.body.classList.add("has-access-{{ entitlement }}");
} else {
  console.warn("❌ Not subscribed ({{ license_type }})");
  // Optionally trigger paywall
}
