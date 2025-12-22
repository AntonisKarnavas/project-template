# Frontend Documentation

This directory contains the React Native Expo frontend application.

## Prerequisites

- Node.js (v18+)
- npm or yarn
- Expo Go app on your physical device (iOS/Android) OR
- Android Studio Emulator / iOS Simulator

## Setup

1.  **Install Dependencies:**
    ```bash
    cd frontend
    npm install
    ```

2.  **Configuration:**
    - The API URL is configured in `config.js`.
    - Android Emulator uses `10.0.2.2` to access localhost.
    - iOS Simulator uses `localhost`.
    - **Physical Device:** If running on a physical device, you MUST change `localhost` in `config.js` to your computer's local LAN IP address (e.g., `192.168.1.X`).

## Running the App

### Start the Development Server
```bash
npx expo start
```

### Run on iOS Simulator
Press `i` in the terminal after starting the server.

### Run on Android Emulator
Press `a` in the terminal after starting the server.

### Run on Web Browser
Press `w` in the terminal after starting the server.

### Run on Physical Device
1.  Ensure your phone and computer are on the same Wi-Fi network.
2.  Open the **Expo Go** app on your phone.
3.  Scan the QR code displayed in the terminal.

## Authentication
The app connects to the backend API for authentication:
- **Login:** POST `/auth/login`
- **Signup:** POST `/auth/register`
- **Logout:** POST `/auth/logout`

The session is managed via cookies, so ensure your backend is allowing credentials if testing on web or correctly handling cookies on mobile.
