# Swastya Assist V11.0.8 Final

- Preserves V11.0.7 timeline normalization and all prior features.
- Safe GET handling for destructive admin delete URLs: GET never deletes; it redirects to the admin dashboard.
- Prevents noisy 405 responses from browser prefetchers/crawlers while retaining POST + CSRF for actual deletion.
- App version: 11.0.8.
