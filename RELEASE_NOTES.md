# Release Notes

## iOS Home Screen Icons
- Added iOS home screen icons (apple-touch-icon) for all common device sizes (180×180, 152×152, 120×120, 167×167)
- Implemented diagonal split design with half light / half dark background for optimal visibility in both modes
- iOS automatically applies appropriate backgrounds based on system appearance

## Daily Collection Navigation
- Added day navigation buttons to daily collection header (left/right edges)
- Click left edge → previous day, right edge → next day
- Tinder-like swipe animation when switching days (translation + rotation)
- Animated hover/click glow effects on navigation buttons
- Tooltips: "go to previous day" / "go to next day"
- Mobile: Navigation buttons auto-hide after 3 seconds to prevent persistent visibility
- Single-tap navigation on mobile (no double-tap required)
- 40% opacity visibility on touch devices for better discoverability

## Image Modal Improvements
- Added image navigation with left/right arrows for snipsels with multiple images
- Keyboard support: ArrowLeft/ArrowRight to navigate, Escape to close
- Smooth fly-in animation when switching images (ease-out-cubic easing)
- Image counter showing current position (e.g., "2 / 5")
- Combined download and close buttons into pill-shaped control
- Fixed initial image loading issues

## Settings Page
- Removed header color styling from buttons - all buttons now use consistent slate colors
- Statistics numbers remain as the only element using header color
- Toggle buttons (Push Notifications, Carry Over) use simple active/inactive styling

## Navigation Bar
- Plus icon color now adapts based on background brightness
- Dark icon on light backgrounds, light icon on dark backgrounds
- Notification badge text color also adapts to background brightness

## API & Backend
- New Quick Add API with API key authentication
- Support for file uploads in quick_add endpoint
- Support for multiple file uploads
- HEIC/HEIF image format support for quick_add endpoint

## Keyboard Shortcuts
- Ctrl/Cmd+Shift+N: New snipsel in Today
- Ctrl/Cmd+Shift+Enter: New snipsel in current collection
- Ctrl/Cmd+Shift+T: Toggle between task and note type
- Delete/Backspace: Delete selected snipsels
- Ctrl/Cmd+Shift+Arrow: Move and indent selected snipsels
- Escape: Clear selection
- Ctrl/Cmd+S: Focus search
- Ctrl/Cmd+1-4: Navigation shortcuts
- Additional shortcuts for AI, card view, copy, move, info, upload

## Geo Location
- Added "My/Shared" scope filter to geo location map
- Custom SVG markers instead of default Leaflet icons
- Fixed shared collection geo snipsel loading

## Sharing
- Inherit sharing options when creating collection from snipsel

## Bug Fixes
- Fixed swipe gesture for day navigation
- Fixed navigation button visibility issues on mobile
- Fixed image modal loading and animation issues
- Fixed AI model dropdown to work when API key is already set
- Fixed page title to include Locations
- Fixed keyboard shortcut effect reactivity

## Documentation
- Updated README and user documentation with keyboard shortcuts
- Added geo location and multi-select features to documentation
