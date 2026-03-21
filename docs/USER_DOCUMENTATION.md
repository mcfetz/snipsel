# Snipsel - User Documentation

## Purpose

Snipsel is a personal knowledge management application that helps you organize notes, tasks, and ideas in collections. It combines the flexibility of a note-taking app with powerful features like tagging, mentions, and search to help you quickly find and connect your information.

## Key Features (Overview)

- **Collections** - Organize your content into themed collections
- **Daily Collections** - Automatic daily notes for each day
- **Snipsels** - Individual notes within collections (text, tasks, links, images)
- **Tags** - Categorize snipsels with #hashtags
- **Mentions** - Reference other users with @username
- **Search** - Find content across all collections
- **Sharing** - Share collections with other users
- **Passcode Protection** - Secure sensitive collections
- **Notifications** - Stay informed about mentions and task assignments (now with content previews)
- **Reminders** - Set date-based alerts for individual snipsels
- **AI Assistant** - Process and generate content using a configurable LLM proxy
- **Sticky Navigation** - Keep track of your location with the sticky collection title tab
- **Geo Location** - Capture and view snipsels with geographic coordinates on an interactive map
- **Smart Multi-Select** - Range selection and auto-select collapsed children for efficient bulk operations

---

## Collections

### What is a Collection?

A collection is a container for related snipsels. Think of it like a notebook or folder. Each collection has:
- **Title** - Name of the collection
- **Icon** - Emoji icon for visual identification
- **Header Color** - Custom color for the collection header
- **Default Snipsel Type** - Preferred type for new snipsels

### Regular Collections

Regular collections are manual containers you create to organize content thematically. Examples:
- "Project Ideas"
- "Meeting Notes"
- "Reading List"

### Daily Collections

Daily collections are automatically created for each day. They provide a quick way to capture daily thoughts, tasks, and notes without creating a collection manually.

**Key behaviors:**
- One collection per day per user (unique by owner + date)
- Shown in the Calendar view
- When viewing your daily collection, you can see snipsels from other users that mention you (read-only)
- Useful for daily standups, journal entries, or daily task lists
- **Navigation**: You can swipe left or right on the daily collection to navigate between days quickly.
- **Sticky Title Tab**: When scrolling down a large collection, a "lasche" (tab) with the collection title slides out from behind the header. Clicking it scrolls you back to the top instantly.

![Screenshot: Daily Collection in Calendar View - PLACEHOLDER]

### Creating a Collection

1. Click the **+** button in the sidebar
2. Enter a title for the collection
3. Optionally select an icon and header color
4. Choose a default snipsel type (optional)
5. Click **Create**
6. **Create from Snipsel**: You can also create a collection by selecting a snipsel and clicking the **Create Collection** icon in the toolbox. This will move the snipsel (and its children) into a new collection and replace the original with a link.

### Collection Settings

Access collection settings by clicking the collection menu (three dots) and selecting **Settings**. Options include:
- Rename collection
- Change icon and color
- Set default snipsel type
- Enable/disable passcode protection
- **Show Completed Tasks**: Toggle whether completed tasks are shown by default in this collection.
- Archive collection
- Delete collection

---

## Snipsels

### What is a Snipsel?

A snipsel is an individual item within a collection. It's the basic unit of content in Snipsel.

### Snipsel Types

1. **Text** - Plain text or markdown content
2. **Task** - A task that can be marked as done/undone
3. **Link** - External URL with optional label. Clicking a link opens it automatically in a new browser tab.
4. **Image** - Image attachments displayed in a grid
5. **Attachment** - File attachments

### Creating a Snipsel

1. Open a collection
2. Click **Add new snipsel** (or press Enter after the last snipsel)
3. The new snipsel inherits the indent level from the previous snipsel
4. Select the type using the dropdown (text, task, link, image)
5. Enter content and press **Save**

**Refreshing content**: On mobile devices or touch screens, you can "pull-to-reload" at the top of a collection to refresh the snipsel list.

### Editing Snipsel Content

- Click on any snipsel to edit it
- **Real-time Indentation**: Indentation changes made with **Tab** or **Shift+Tab** are now visible immediately while editing.
- Supports Markdown formatting (Bold, Italic, Lists, **Blockquotes** using `>`, etc.)
- Tags and mentions are automatically extracted and linked

### Task Management

For **task** type snipsels:
- Click the checkbox to mark as done/undone.
- Done tasks show a strikethrough.
- **Recurring Tasks**: When you mark a task with a recurring reminder as done, a new open task is automatically created for the next occurrence and placed directly below the completed one. This ensures you never "lose" a task that hasn't been finished yet.
- Tasks assigned to you via @mention will appear in your notifications.
- **Cleanup**: In the collection menu, you can select **Delete completed tasks** to permanently remove finished tasks from the current collection, or **Reset completed tasks** to re-open them all at once.

### Reminders

You can set date-based reminders for any snipsel:
1. Open the snipsel detail (click the "edit" or "expand" icon).
2. Use the **Reminders** card to set a date and time.
3. **Recurrence**: Enter a standard iCalendar RRule (e.g., `FREQ=DAILY`) for repeating reminders.
4. **Behavior**: 
    - Reminders **stay on the task** even if the date passes, as long as the task is open.
    - When a recurring task is **marked as done**, the system automatically creates a **copy** of the task with the next reminder date and places it directly below the completed task.
    - If you complete a task early, the next date is still calculated based on the original series to maintain your schedule.
5. **Icon**: Tasks with recurring reminders show a curved arrow icon next to the date.
6. **Display**: Reminders are shown in the collection view and the dedicated **Tasks** page.

---

## Tasks Page

The **Tasks** page (accessible via the checkmark icon in the sidebar) provides a central view of all your tasks across all collections.

### Filtering Tasks

1. **Open / Done**: Switch between pending and completed tasks.
2. **My / Shared**: 
    - **My**: Shows tasks you created yourself that are NOT explicitly assigned to someone else via `@mention`.
    - **Shared**: Shows tasks created by others in collections shared with you, provided they are NOT explicitly assigned to a specific user.
- **Template Exclusion**: Tasks from collections marked as **Templates** are hidden from the main Todos view to avoid clutter. However, they remain accessible via the global search.

> [!NOTE]
> Tasks that contain an `@username` mention of a known user are considered "assigned" and will not appear in the general **My** or **Shared** lists. They will instead appear in the notifications and mentions of the respective user.

### Sorting

Tasks are sorted by their reminder date (if set), with the soonest or overdue tasks appearing at the top.

### Attachments

**Image Type:**
- Click to upload images
- Images display in a grid layout
- Click any image to view full size
- Thumbnails are auto-generated with correct rotation (EXIF-aware)

**Attachment Type:**
- Upload any file type
- Files show as download links
- Maximum file size: 10MB per file

![Screenshot: Snipsel with image attachments - PLACEHOLDER]

### Indent / Nesting

Snipsels can be indented to create hierarchy:
- Use the indent controls on the snipsel (or keyboard shortcuts)
- Indented snipsels are visually nested
- Helps organize related content

---

## Tags

### Using Tags

Tags are words prefixed with `#` that help categorize snipsels. Examples:
- `#project-alpha`
- `#ideas`
- `#read-later`

### How Tags Work

1. Add `#tagname` anywhere in snipsel content
2. Tags are automatically detected when saving
3. Tags are linked to the snipsel owner
4. You can filter snipsels by tag

### Tag Scope

When searching or filtering tags, you can choose scope:
- **My tags** - Tags you created (#mytag)
- **Shared tags** - Tags from others (#someone-else)
- **All tags** - Everything

### Tag Navigation

- Click any tag to filter snipsels by that tag
- Tags page shows all tags with snipsel counts

![Screenshot: Tag filtering - PLACEHOLDER]

---

## Mentions

### Using Mentions

Mention other users with `@username` to:
- Notify them about relevant content
- Assign tasks to them
- Reference their input

### How Mentions Work

1. Type `@username` in any snipsel
2. When saved, the mentioned user receives a notification
3. For tasks: "User assigned a task to you"
4. For other content: "User mentioned you in a snipsel"

> [!TIP]
> Push notifications for tasks and mentions now include a text preview of the actual content, giving you instant context without opening the app.

### Viewing Mentions

**In your collection:**
- Mentions you receive appear in notifications

**In Daily Collections:**
- When viewing your daily collection, you see snipsels from other users that mention you
- These are shown in a "Mentioned by others on this day" section
- Read-only view (you can see but not edit)
- Shows the author's username

![Screenshot: Incoming mentions in daily collection - PLACEHOLDER]

### Mention Notifications

Notifications are sent for:
- Being mentioned in any snipsel
- Being assigned a task
- Collection sharing invitations

---

## Search

### Basic Search

Enter search terms in the search bar to find snipsels across all your collections.

### Search Behavior

- **AND Logic**: All search terms must match
- Example: Searching "project meeting" finds snipsels containing BOTH "project" AND "meeting"
- Searches: snipsel content, external URLs, external labels

### Search Filters

You can narrow search results with:
- **Type**: text, task, link, image, attachment
- **Tag**: Filter by specific tag
- **Mention**: Filter by mention (@user)
- **Day**: Filter by date
- **Scope**: my, shared, or all collections
- **Task Done**: Filter completed/incomplete tasks

### Search Results

Results show:
- Snipsel content preview
- Collection it belongs to
- Last modified date
- Write access indicator

---

## Permissions & Sharing

### Permission Levels

1. **Owner** - Full control, can delete collection
2. **Write** - Can add/edit snipsels
3. **Read** - View-only access

### Sharing a Collection

1. Open collection settings
2. Click **Share**
3. Enter the username to share with
4. Select permission (Read or Write)
5. The shared user will see the collection in their sidebar

### Sharing Daily Collections

**Important distinction:**

| Feature | Regular Collections | Daily Collections |
|---------|--------------------|--------------------|
| Manual sharing | Yes - via collection settings | No - cannot share |
| Visibility | Only owner + shared users | Only owner (private) |
| Cross-user mentions | Read-only in mentions section | Yes - view others' snipsels mentioning you |

**Daily Collections:**
- Cannot be shared through settings
- However, when OTHER users mention you in THEIR daily collections, you can see those mentions in YOUR daily collection
- This enables cross-user collaboration on the same day without explicit sharing

### Passcode Protection

Protect sensitive collections with a passcode:
1. Open collection settings
2. Enable **Passcode Protection**
3. Set a passcode
4. Users must enter passcode to view collection content

---

## Notifications

### Notification Types

1. **Mention** - Someone mentioned you in a snipsel
2. **Task Assignment** - You were assigned a task
3. **Share** - A collection was shared with you
4. **Reminder** - A snipsel reminder time has been reached

> [!NOTE]
> All notifications (Mentions, Tasks, Reminders) now include a preview of the snipsel text to provide immediate context.

### Viewing Notifications

- Click the bell icon in the header
- Shows unread count badge
- Click to mark as read
- Click notification to jump to relevant snipsel

---

## Calendar View

The calendar shows your daily collections organized by date.

### Features

- Month view with dots indicating days with collections
- Click any day to view that day's collection
- Navigate between months
- Today's collection highlighted
- **Navigation**: Swipe left or right to navigate between months with smooth animations.

![Screenshot: Calendar View - PLACEHOLDER]

---

## Geo Location

Snipsel can capture and display geographic coordinates for your snipsels, allowing you to see where your notes, tasks, and ideas were created.

### Capturing Location

When creating a new snipsel, Snipsel automatically captures your device's GPS location (if permission is granted). This works on both mobile and desktop browsers.

**Privacy Note:** Location data is only stored if you grant permission. You can always deny location access and snipsels will be created without coordinates.

### Viewing Snipsels on the Map

Access the **Geo** view from the Tags/Mentions page (look for the map icon):

1. **Map View** — See all your geo-tagged snipsels plotted on an interactive map
2. **List Below Map** — A scrollable list shows all snipsels with their coordinates
3. **Click to Navigate** — Click any marker or list item to jump to that snipsel's collection

### Use Cases

- **Travel Journal** — Track where you've been and what you noted
- **Field Work** — Document site visits with location data
- **Photography** — Remember where you took specific photos
- **Real Estate** — Track property visits and notes
- **Delivery/Service Tasks** — Log where tasks were completed

---

## Multi-Select & Bulk Operations

Snipsel provides powerful selection tools for working with multiple snipsels at once.

### Basic Selection

1. **Hover to Reveal** — Move your mouse to the right edge of any snipsel to reveal the selection bar
2. **Click to Select** — Click the selection bar to toggle selection of that snipsel
3. **Visual Feedback** — Selected snipsels are highlighted with a colored background

### Range Selection

Quickly select multiple consecutive snipsels:

**Desktop:**
1. Select the first snipsel
2. Hold **Shift** and click the last snipsel you want to select
3. All snipsels between (inclusive) are selected

**Mobile:**
1. Select the first snipsel
2. **Long-press** the selection bar of the last snipsel you want to select
3. All snipsels between (inclusive) are selected

### Auto-Select Collapsed Children

When working with nested/indented snipsels:

- **Selecting a Parent** — If a parent snipsel has collapsed children, selecting it automatically selects all its children too
- **Deselecting a Parent** — Deselecting a parent also deselects all its children
- **Works with Range Selection** — Range selection also respects collapsed children and selects them automatically

### Bulk Operations

Once you have multiple snipsels selected, use the **Toolbox** that appears at the bottom:

- **Move Up/Down** — Reorder selected snipsels (short press = move one step, long press = move to top/bottom)
- **Indent/Outdent** — Change nesting level (long press on Outdent = remove all indentation)
- **Change Type** — Convert between text, task, image, and attachment types
- **Copy/Move/Link** — Copy or move snipsels to another collection, or create internal links
- **Delete** — Remove all selected snipsels at once
- **AI Assistant** — Process selected snipsels with the AI assistant
- **Add Attachments** — Upload files to all selected snipsels simultaneously

---

## Security & Authentication

Snipsel provides modern security features to keep your account safe. These can be configured in your **Settings**.

### Two-Factor Authentication (2FA)

You can enable 2FA to add an extra layer of security to your account.
1. Open Settings and click **Enable 2FA**.
2. Scan the QR code with your authenticator app (e.g., Google Authenticator, Authy, Apple Passwords).
3. Enter the 6-digit code and your current password to verify and enable.
4. On future logins, you will be prompted to enter a 6-digit code after your password.

### Passkeys

Passkeys allow you to log in securely without a password using your device's built-in authentication (Touch ID, Face ID, Windows Hello) or a hardware security key.

**Adding a Passkey:**
1. Open Settings and look for the **Login with Passkey** section.
2. Enter a name for your device (e.g., "MacBook Pro" or "iPhone").
3. Click **Add Passkey** and follow your browser/device prompts.

**Logging in with a Passkey:**
1. On the login screen, click the **Login with Passkey** button.
2. If you only have one passkey or have used one recently, your device will prompt you to authenticate. Alternatively, you can type your username first, and then click the button.

---

## AI Assistant

Snipsel includes a powerful AI assistant that you can configure with your own OpenAI-compatible LLM endpoint (like OpenAI, Groq, or a local Ollama instance).

### Configuration

1. Go to your **Settings**.
2. Fill in the **AI Integration** section:
   - **LLM API URL**: The endpoint URL (e.g., `https://api.openai.com/v1/chat/completions`).
   - **Model Name**: The model identifier (e.g., `gpt-4o` or `llama3`).
   - **API Key**: Your secret key for the service.
3. Click **Save AI Settings**.

### Using the Assistant

Once configured, an **AI Assistant** icon (a cube) appears in the snipsel toolbox when a single snipsel is selected.

1. Select a snipsel.
2. Click the **AI Assistant** button.
3. Enter a prompt describing what you want the AI to do (e.g., "Summarize this", "Fix grammar", "Translate to French").
4. After the response is generated, you can:
   - **Insert**: Adds the response as a new snipsel directly below the original one.
   - **Replace**: Replaces the content of the selected snipsel with the AI response.
   - **Copy**: Copies the response to your clipboard.
   - **New Prompt**: Start over with a different instruction.

---

## Settings

### Personal Settings

Access via the settings icon (gear):
- Change username
- View account info
- **Content Statistics**: View counts for your collections, snipsels, completed tasks, and attachments to track your usage.

### Collection Settings

Per-collection settings (accessed via collection menu):
- Title, icon, color
- Default snipsel type
- Passcode protection
- Sharing management
- Archive/Delete

---

## Keyboard Shortcuts

### Navigation (Global)
These shortcuts work when you're not editing a snipsel (not focused in an input field):

| Shortcut | Action |
|----------|--------|
| **Cmd/Ctrl + 1** | Open Calendar page |
| **Cmd/Ctrl + 2** | Open Tasks page |
| **Cmd/Ctrl + 3** | Open Collections list |
| **Cmd/Ctrl + 4** | Open Tags/Mentions page |
| **Cmd/Ctrl + N** | Create new snipsel in today's collection |
| **Cmd/Ctrl + S** | Focus search field |
| **Escape** | Deselect all selected snipsels |

### Selected Snipsels (when snipsels are selected)
| Shortcut | Action |
|----------|--------|
| **Shift + ↑** | Move selected snipsels up |
| **Shift + ↓** | Move selected snipsels down |
| **Shift + ←** | Outdent selected snipsels |
| **Shift + →** | Indent selected snipsels |

### Editing
- **Enter** after last snipsel: Create new snipsel
- **Tab**: Increase indent (now visible immediately)
- **Shift+Tab**: Decrease indent (now visible immediately)
- **Ctrl+Enter**: Save current snipsel and create a new one below with the same indentation and type.

### Selection
- **Shift + Click** (on selection bar): Select range of snipsels between last selected and clicked item

---

### Maintenance

#### Cleanup Command

To permanently delete all snipsels and collections marked as "deleted" (including physical attachment files and their thumbnails), run the following command from the `backend` directory:

```bash
flask --app snipsel_api.app cleanup
```

This command:
1. Identifies all items with a `deleted_at` timestamp.
2. Removes associated physical files from the storage directory.
3. Completely removes the database records and all their relationships (tags, mentions, shares, etc.).

---

## Technical Notes

### Image Handling
... (unchanged)

### Image Handling

- Thumbnails are auto-generated for images
- EXIF rotation metadata is respected (photos from phones display correctly)
- Supported formats: JPEG, PNG, GIF, WebP
- **Video Thumbnails**: Requires **FFmpeg** to be installed on the server. The official Docker image includes FFmpeg automatically.

### Data Storage

- All data stored in SQLite database
- File uploads stored in `./uploads/` directory
- Automatic thumbnail generation

### Security

- Sessions managed via secure cookies
- Passwords hashed with bcrypt
- Passcode collections require code to access

### Docker Deployment

To deploy Snipsel using Docker (frontend and backend in one container):

```bash
# 1. Build the Docker image
docker build -t snipsel .

# 2. Run the container
docker run -d \
  --name snipsel \
  -p 5000:5000 \
  -v ./snipsel_data:/app/data \
  -v ./snipsel_uploads:/app/uploads \
  -e SNIPSEL_SECRET_KEY="your-secure-secret-key" \
  -e SNIPSEL_DOMAIN="yourdomain.com" \
  -e SNIPSEL_FRONTEND_URL="https://yourdomain.com" \
  -e VAPID_PUBLIC_KEY="your_vapid_public_key" \
  -e VAPID_PRIVATE_KEY="your_vapid_private_key" \
  -e VAPID_SUBJECT="mailto:admin@yourdomain.com" \
  snipsel
```

**Required Environment Variables for Passkeys:**
If you want to use Passkeys, you *must* set `SNIPSEL_DOMAIN` and `SNIPSEL_FRONTEND_URL` to match your production domain. Without them, WebAuthn will fail.
For Push Notifications, you must set `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, and `VAPID_SUBJECT`.
