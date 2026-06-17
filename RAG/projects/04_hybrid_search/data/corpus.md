# Helios Knowledge Base (sample corpus for hybrid search)

Each "## " section below is treated as one passage. Some contain rare codes/names
(great for keyword search) and some are paraphrasable prose (great for vector search).

## Error E-4021
Error code E-4021 means a Helios Compute virtual server failed to attach its boot volume within 60 seconds. The fix is to detach the volume, run a filesystem check, and reattach. If it recurs, the host may have a degraded storage controller and should be drained.

## Error E-7750
Error code E-7750 indicates that Helios Store rejected an upload because the object exceeded the 5 terabyte per-object limit. Split the object into parts and use multipart upload.

## Refunds
Customers may request a full refund within 30 days of their first paid invoice. Refunds are returned to the original payment method within 10 business days. After 30 days only prorated credits are offered.

## Getting your money back
If you are unhappy with the service and want reimbursement, you can ask for your payment to be returned. The window for a complete return of funds is the first month after your initial bill.

## The Abyss dead-letter topic
Messages in Helios Pipe that fail processing five times are routed to a dead-letter topic named Abyss. An engineer reviews Abyss daily and either fixes the consumer or discards poison messages.

## Orbit scheduler hot hosts
When a Helios Compute host exceeds 85 percent CPU for five minutes, the Orbit scheduler marks it as hot and stops placing new servers on it. Sustained pressure triggers live migration of existing servers to cooler hosts.

## Two-factor authentication
Customers can protect their account by enabling two-factor authentication. Helios also supports SAML single sign-on for enterprise identity providers.

## Securing your login
To keep unauthorized people out of your account, turn on a second verification step in addition to your password. Enterprise customers can connect their corporate identity system.

## Uptime SLA
Helios Compute guarantees 99.9 percent monthly uptime. Uptime between 99.0 and 99.9 percent earns a 10 percent service credit; below 99.0 percent earns 25 percent. Credits must be claimed within 30 days.

## Data regions
Helios Store data can live in North America, Europe, or Asia Pacific, and never leaves the chosen region. Premium customers can negotiate custom data residency.
