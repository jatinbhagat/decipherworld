# DecipherWorld Mixpanel Events Documentation

## Overview
This document lists all Mixpanel events tracked by the DecipherWorld platform, including their properties and when they're triggered.

## Event Categories

### 1. Page Navigation Events

#### `Viewed [Page Name]`
**Triggered**: On every page load
**Properties**:
- `user_id`: Anonymous user identifier
- `login_status`: "Not Logged In" (or actual status if logged in)
- `page_from`: Previous page URL
- `current_page`: Current page path
- `page_title`: HTML title of the page
- `page_url`: Full URL
- `page_name`: Human-readable page name
- `page_category`: Page category (Games, Learning Platform, Teachers, etc.)
- `load_time`: Page load time in milliseconds
- `timestamp`: ISO timestamp
- `user_agent`: Browser user agent
- `screen_resolution`: Screen dimensions
- `viewport_size`: Browser viewport dimensions
- `referrer`: Referring website or "direct"
- `session_duration`: Time spent in current session (seconds)

**Page Names Tracked**:
- `Viewed Homepage`
- `Viewed About Us`
- `Viewed Teachers Hub`
- `Viewed Games Hub`
- `Viewed AI Learning Games`
- `Viewed Robotic Buddy Landing`
- `Viewed Simple Game Landing`
- `Viewed Drag Drop Game Landing`
- `Viewed Group Learning Games`
- `Viewed Monsoon Mayhem Landing`
- `Viewed Cyber Security Games`
- `Viewed Financial Literacy Games`
- `Viewed Constitution Basic Games`
- `Viewed Constitution Advanced Games`
- `Viewed Entrepreneurship Games`
- `Viewed Group Learning Platform`
- `Viewed Contact Us`
- `Viewed Design Thinking Game`
- `Viewed Climate Game`
- `Viewed Robotic Buddy Game`
- `Viewed Robotic Buddy Activity`

### 2. User Interaction Events

#### `Interacted [Element Type]`
**Triggered**: When users click on buttons, links, or interactive elements
**Element Types**:
- `Interacted Link`
- `Interacted Button`
- `Interacted Element`

**Properties**:
- All base properties (user_id, timestamp, etc.)
- `element_type`: Type of element (Link, Button, Element)
- `element_text`: Text content of the element (truncated to 100 chars)
- `element_location`: Location context (Navigation, Header, Footer, Hero Section, Form, Game Interface, Main Content)
- `element_class`: CSS classes
- `element_id`: Element ID or "no-id"
- `click_coordinates`: X,Y coordinates of the click

### 3. Form Events

#### `Form Viewed`
**Triggered**: When a form is detected on page load
**Properties**:
- All base properties
- `form_name`: Identified form name (Contact Form, Teacher Form, Game Form, etc.)
- `form_id`: Form ID or "no-id"

#### `Form Submitted`
**Triggered**: When any form is submitted
**Properties**:
- All base properties
- `form_name`: Identified form name
- `form_id`: Form ID
- `form_method`: HTTP method (GET/POST)
- `form_action`: Form action URL

### 4. Game Events

#### `Game Started`
**Triggered**: When game start elements are clicked
**Properties**:
- All base properties
- `game_type`: Type of game (Design Thinking, Climate Game, AI Learning, etc.)
- `game_page`: Page where game was started

#### `Game Engagement`
**Triggered**: After 30 seconds on a game page
**Properties**:
- All base properties
- `engagement_duration`: 30 (seconds)
- `game_type`: Type of game

#### `Game [Action]` (via trackGameEvent API)
**Triggered**: Custom game events
**Properties**:
- All base properties
- `game_type`: Type of game
- Additional custom properties

**Common Actions**:
- `Game Completed`
- `Game Level Up`
- `Game Answer Submitted`
- `Game Hint Used`
- `Game Paused`
- `Game Resumed`

#### `Achievement Unlocked`
**Triggered**: When players unlock achievements
**Properties**:
- All base properties
- `achievement`: Achievement name
- `game_type`: Type of game
- Additional custom properties

### 5. Error Events

#### `Error Occurred`
**Triggered**: When JavaScript errors occur or custom errors are tracked
**Properties**:
- All base properties
- `error_type`: Type of error (JavaScript Error, Game Error, etc.)
- `error_message`: Error message
- Additional custom properties

#### `JavaScript Error`
**Triggered**: Global JavaScript error handler
**Properties**:
- All base properties
- `error_type`: "JavaScript Error"
- `error_message`: Error message
- `filename`: File where error occurred
- `line_number`: Line number
- `column_number`: Column number

### 6. Session Events

#### `Page Unloaded`
**Triggered**: When user leaves a page
**Properties**:
- All base properties
- `time_on_page`: Time spent on page in seconds

## Game-Specific Events

### AI Learning Games (Robotic Buddy)
- `Viewed Robotic Buddy Landing`
- `Game Started` (game_type: "AI Learning")
- `Robotic Buddy Created`
- `Classification Game Started`
- `Animal Classified`
- `Game Level Completed`
- `Hint Requested`

### Design Thinking Game
- `Viewed Design Thinking Game`
- `Game Started` (game_type: "Design Thinking")
- `Ideation Phase Started`
- `Prototype Created`
- `Feedback Submitted`
- `Challenge Completed`

### Climate Game
- `Viewed Climate Game`
- `Game Started` (game_type: "Climate Game")
- `Climate Action Selected`
- `Environmental Impact Calculated`
- `Team Collaboration Started`

### Financial Literacy Games
- `Viewed Financial Literacy Games`
- `Game Started` (game_type: "Financial Literacy")
- `Budget Created`
- `Investment Decision Made`
- `Financial Quiz Completed`

### Cyber Security Games
- `Viewed Cyber Security Games`
- `Game Started` (game_type: "Cyber Security")
- `Security Threat Identified`
- `Password Strength Tested`
- `Phishing Email Detected`

### Constitution Games
- `Viewed Constitution Basic Games`
- `Viewed Constitution Advanced Games`
- `Game Started` (game_type: "Constitution")
- `Constitution Article Studied`
- `Rights Quiz Completed`
- `Civic Scenario Solved`

### Entrepreneurship Games
- `Viewed Entrepreneurship Games`
- `Game Started` (game_type: "Entrepreneurship")
- `Business Plan Created`
- `Market Research Completed`
- `Pitch Presented`

## User Journey Events

### New User Flow
1. `Viewed Homepage`
2. `Interacted Button` (element_text: "Get Started" or "Explore Games")
3. `Viewed Games Hub`
4. `Interacted Link` (specific game selection)
5. `Viewed [Game] Landing`
6. `Game Started`

### Teacher Flow
1. `Viewed Homepage`
2. `Interacted Link` (element_text: "Teachers")
3. `Viewed Teachers Hub`
4. `Form Viewed` (form_name: "Teacher Form")
5. `Form Submitted`

### Learning Flow
1. `Viewed Games Hub`
2. `Game Started`
3. `Game Engagement` (after 30s)
4. `Achievement Unlocked` (optional)
5. `Game Completed`

## Implementation Notes

### Base Properties
All events include these standard properties:
- `user_id`: Anonymous identifier (anon_[random]_[timestamp])
- `login_status`: Authentication status
- `page_from`: Previous page for navigation flow
- `current_page`: Current page path
- `timestamp`: ISO 8601 timestamp
- `user_agent`: Browser information
- `screen_resolution`: Display resolution
- `viewport_size`: Browser window size
- `referrer`: Traffic source
- `session_duration`: Time in current session

### Game Properties (when applicable)
When on game pages or during game-related events, these additional properties are automatically included:
- `game_name`: Full descriptive name of the game
- `game_code`: Unique identifier code for the game
- `game_subtype`: Specific variation of the game (when applicable)
- `session_id`: Game session identifier (for multiplayer/collaborative games)

#### Game Code Reference Table
| Game Name | Game Code | Path Patterns | Subtypes |
|-----------|-----------|---------------|----------|
| Design Thinking Challenge | DTC001 | `/learn/design-thinking/`, `/learn/session/` | N/A |
| Climate Change Challenge | CCC001 | `/learn/climate/`, `/monsoon-mayhem/` | N/A |
| Robotic Buddy AI Learning | RBAL001 | `/buddy/`, `/robotic-buddy/` | Animal Classification, Simple AI Game, Drag Drop Game |
| Financial Literacy Adventure | FLA001 | `/financial-literacy/` | N/A |
| Cyber Security Mission | CSM001 | `/cyber-security/`, `/cyber-city/` | N/A |
| Constitution Explorer Basic | CEB001 | `/constitution-basic/` | N/A |
| Constitution Explorer Advanced | CEA001 | `/constitution-advanced/` | N/A |
| Entrepreneurship Challenge | EC001 | `/entrepreneurship/` | N/A |

### Debugging
- Debug mode enabled in development
- Console logging for all events
- Fallback logging to `window.dwAnalyticsLog` array
- Error logging to `window.dwAnalyticsErrors` array

### Privacy
- Only anonymous user IDs tracked
- No personally identifiable information collected
- Cookie-based persistence with 1-year expiry
- GDPR-compliant data collection

## API Usage Examples

### Manual Event Tracking
```javascript
// Track custom game event (game_name and game_code automatically included)
window.dwAnalytics.trackGameEvent('Level Completed', 'AI Learning', {
    level: 3,
    score: 250,
    time_taken: 45
});

// Results in event with properties:
// {
//   "event": "Game Level Completed",
//   "user_id": "anon_abc123_1698123456",
//   "game_name": "Robotic Buddy AI Learning",  // AUTO-ADDED
//   "game_code": "RBAL001",                    // AUTO-ADDED
//   "game_subtype": "Animal Classification",   // AUTO-ADDED (if applicable)
//   "game_type": "AI Learning",
//   "level": 3,
//   "score": 250,
//   "time_taken": 45,
//   "timestamp": "2025-10-24T09:30:15.123Z"
// }

// Track achievement (game properties automatically included)
window.dwAnalytics.trackAchievement('First Classification', 'AI Learning', {
    animal_count: 5,
    accuracy: 100
});

// Results in event with properties:
// {
//   "event": "Achievement Unlocked",
//   "user_id": "anon_abc123_1698123456",
//   "game_name": "Robotic Buddy AI Learning",  // AUTO-ADDED
//   "game_code": "RBAL001",                    // AUTO-ADDED
//   "achievement": "First Classification",
//   "game_type": "AI Learning",
//   "animal_count": 5,
//   "accuracy": 100,
//   "timestamp": "2025-10-24T09:30:15.123Z"
// }

// Track error (game context automatically included)
window.dwAnalytics.trackError('Game Loading Error', 'Failed to load game assets', {
    asset_url: '/static/games/ai-learning.js'
});
```

### Example Page View Events with Game Properties

**Design Thinking Game Page**:
```json
{
  "event": "Viewed Design Thinking Game",
  "user_id": "anon_xyz789_1698123456",
  "game_name": "Design Thinking Challenge",
  "game_code": "DTC001",
  "session_id": "ABC123",
  "current_page": "/learn/session/ABC123/",
  "timestamp": "2025-10-24T09:30:15.123Z"
}
```

**Robotic Buddy Game Page**:
```json
{
  "event": "Viewed Robotic Buddy Game",
  "user_id": "anon_xyz789_1698123456",
  "game_name": "Robotic Buddy AI Learning",
  "game_code": "RBAL001",
  "game_subtype": "Animal Classification",
  "current_page": "/buddy/classification/",
  "timestamp": "2025-10-24T09:30:15.123Z"
}
```

### Check Analytics Status
```javascript
// Check if analytics is working
console.log('Analytics initialized:', !!window.dwAnalytics);
console.log('Mixpanel available:', typeof mixpanel !== 'undefined');
console.log('Events logged:', window.dwAnalyticsLog?.length || 0);
console.log('Errors:', window.dwAnalyticsErrors?.length || 0);
```

This comprehensive event tracking provides insights into:
- User engagement and navigation patterns
- Game usage and completion rates
- Form conversion rates
- Error occurrence and debugging
- User journey optimization opportunities
- Feature usage analytics