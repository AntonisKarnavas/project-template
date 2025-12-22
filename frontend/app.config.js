import 'dotenv/config';

export default {
  expo: {
    name: "frontend",
    slug: "frontend",
    scheme: "frontend",
    version: "1.0.0",
    orientation: "portrait",
    icon: "./assets/icon.png",
    userInterfaceStyle: "light",
    newArchEnabled: true,
    splash: {
      image: "./assets/splash-icon.png",
      resizeMode: "contain",
      backgroundColor: "#ffffff"
    },
    ios: {
      supportsTablet: true,
      bundleIdentifier: "com.yourname.frontend"
    },
    android: {
      adaptiveIcon: {
        foregroundImage: "./assets/adaptive-icon.png",
        backgroundColor: "#ffffff"
      },
      package: "com.yourname.frontend",
      edgeToEdgeEnabled: true
    },
    web: {
      favicon: "./assets/favicon.png",
      bundler: "metro"
    },
    extra: {
      googleIosClientId: process.env.GOOGLE_IOS_CLIENT_ID,
      googleAndroidClientId: process.env.GOOGLE_ANDROID_CLIENT_ID,
      googleWebClientId: process.env.GOOGLE_WEB_CLIENT_ID,
      facebookAppId: process.env.FACEBOOK_APP_ID,
    }
  }
};