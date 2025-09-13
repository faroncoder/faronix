final customerInfo = await Purchases.getCustomerInfo();
final entitlement = customerInfo.entitlements.all["{{ entitlement }}"];
final isActive = entitlement?.isActive ?? false;

if (isActive) {
  print("✅ Subscribed to {{ entitlement }} ({{ license_type }})");
  // TODO: Show premium content
} else {
  print("❌ Not subscribed");
  // TODO: Prompt upgrade
}
