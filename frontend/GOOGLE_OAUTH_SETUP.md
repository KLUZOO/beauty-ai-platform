# Google OAuth 2.0 Integration

## Setup Completed

Google OAuth 2.0 has been successfully integrated into the Beauty AI platform.

### Configuration

**Google Client ID**: `136485800268-6lrfcd7uh3g14jhaspul8k2n8rpnm8o6.apps.googleusercontent.com`

### Files Created/Modified

1. **authService.ts** (`src/services/authService.ts`)

   - Service for handling Google authentication
   - Functions:
     - `sendGoogleTokenToBackend(idToken)` - Sends Google ID token to backend
     - `getAuthToken()` - Retrieves stored auth token
     - `getUserInfo()` - Retrieves stored user info
     - `logout()` - Clears authentication data
     - `isAuthenticated()` - Checks if user is authenticated

2. **GoogleAuthButton.tsx** (`src/components/GoogleAuthButton/GoogleAuthButton.tsx`)

   - React component for Google login button
   - Handles Google login response
   - Sends ID token to backend
   - Shows loading and error states

3. **GoogleAuthButton.scss** (`src/components/GoogleAuthButton/GoogleAuthButton.scss`)

   - Styles for the Google auth button

4. **Header.tsx** - Updated

   - Integrated GoogleAuthButton component
   - Shows user info when authenticated
   - Shows logout button
   - Tracks authentication state

5. **Header.scss** - Updated

   - Added styles for `header__auth-section` and `header__user-section`

6. **index.tsx** - Updated
   - Wrapped app with `GoogleOAuthProvider`
   - Configured with Google Client ID

### How It Works

1. **User clicks "Sign in with Google"** - Triggers Google OAuth flow
2. **Google returns ID token** - User is authenticated
3. **Token sent to backend** - Via POST request to `/api/auth/google`
4. **Backend verifies token** - Returns auth token and user info
5. **Token stored locally** - In localStorage for subsequent requests
6. **User session established** - User is logged in

### Backend API Expected

The backend should have an endpoint: `POST /api/auth/google`

**Request body:**

```json
{
  "id_token": "<GOOGLE_TOKEN>"
}
```

**Expected response:**

```json
{
  "token": "YOUR_AUTH_TOKEN",
  "user": {
    "id": "USER_ID",
    "email": "user@example.com",
    "name": "User Name",
    "picture": "USER_PHOTO_URL"
  }
}
```

### Token Storage

- Auth token is stored in `localStorage` as `authToken`
- User info is stored in `localStorage` as `user`
- On logout, both are cleared

### Using Auth Token

To include auth token in API requests:

```typescript
const token = getAuthToken();
const headers = {
  Authorization: `Bearer ${token}`,
  'Content-Type': 'application/json',
};
```

### Environment Variables (Optional)

To use a different API URL, set:

```
REACT_APP_API_URL=https://your-api-url.com/api
```

Default: `https://localhost:5000/api`

### Testing

1. Run `npm start` to start the development server
2. Navigate to the home page
3. Click the "Sign in with Google" button
4. Complete the Google OAuth flow
5. User info should appear in the header
6. Click "Вийти" to logout
