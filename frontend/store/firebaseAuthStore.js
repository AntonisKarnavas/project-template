/**
 * Firebase Authentication Store
 *
 * Token-only authentication pattern for both web and mobile.
 * Firebase handles auth, backend verifies tokens on each request.
 */
import { create } from 'zustand';
import {
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    signInWithCredential,
    signOut,
    GoogleAuthProvider,
    signInWithPopup,
    onAuthStateChanged
} from 'firebase/auth';
import { auth } from '../firebaseConfig';
import { API_URL } from '../config';
import { Platform } from 'react-native';

const useFirebaseAuthStore = create((set, get) => ({
    user: null,
    firebaseUser: null,
    error: null,
    isLoading: false,
    isAuthenticated: false,

    /**
     * Initialize auth state listener
     * Call this once when the app starts
     */
    initializeAuth: () => {
        const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
            if (firebaseUser) {
                // User is signed in with Firebase
                set({ firebaseUser, isAuthenticated: true });

                // Sync with backend to ensure user exists in database
                try {
                    const idToken = await firebaseUser.getIdToken();
                    await get().syncWithBackend(idToken);
                } catch (error) {
                    console.error('Error syncing with backend:', error);
                    set({ error: error.message, isLoading: false });
                }
            } else {
                // User is signed out
                set({ firebaseUser: null, user: null, isAuthenticated: false });
            }
        });

        return unsubscribe;
    },

    /**
     * Sync Firebase auth with backend (JIT user provisioning)
     */
    syncWithBackend: async (idToken) => {
        try {
            const response = await fetch(`${API_URL}/auth/firebase/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ idToken }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Backend sync failed');
            }

            set({ user: { email: data.email, id: data.user_id, firebase_uid: data.firebase_uid }, isLoading: false });
            return true;
        } catch (error) {
            set({ error: error.message, isLoading: false });
            return false;
        }
    },

    /**
     * Sign up with email and password
     */
    signup: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
            const userCredential = await createUserWithEmailAndPassword(auth, email, password);
            const idToken = await userCredential.user.getIdToken();

            // Sync with backend
            await get().syncWithBackend(idToken);

            return true;
        } catch (error) {
            let errorMessage = error.message;

            // Provide user-friendly error messages
            if (error.code === 'auth/email-already-in-use') {
                errorMessage = 'This email is already registered';
            } else if (error.code === 'auth/invalid-email') {
                errorMessage = 'Invalid email address';
            } else if (error.code === 'auth/weak-password') {
                errorMessage = 'Password should be at least 6 characters';
            }

            set({ error: errorMessage, isLoading: false });
            return false;
        }
    },

    /**
     * Sign in with email and password
     */
    login: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
            const userCredential = await signInWithEmailAndPassword(auth, email, password);
            const idToken = await userCredential.user.getIdToken();

            // Sync with backend
            await get().syncWithBackend(idToken);

            return true;
        } catch (error) {
            let errorMessage = error.message;

            // Provide user-friendly error messages
            if (error.code === 'auth/user-not-found' || error.code === 'auth/wrong-password') {
                errorMessage = 'Invalid email or password';
            } else if (error.code === 'auth/invalid-email') {
                errorMessage = 'Invalid email address';
            } else if (error.code === 'auth/too-many-requests') {
                errorMessage = 'Too many failed attempts. Please try again later';
            }

            set({ error: errorMessage, isLoading: false });
            return false;
        }
    },

    /**
     * Sign in with Google (Web)
     * For web: uses popup
     * For mobile: use socialLoginMobile() instead
     */
    googleLogin: async () => {
        set({ isLoading: true, error: null });
        try {
            const provider = new GoogleAuthProvider();

            if (Platform.OS === 'web') {
                const result = await signInWithPopup(auth, provider);
                const idToken = await result.user.getIdToken();
                await get().syncWithBackend(idToken);
                return true;
            } else {
                throw new Error('Google sign-in on mobile requires additional setup. Use socialLoginMobile() with a credential from expo-google-sign-in.');
            }
        } catch (error) {
            set({ error: error.message, isLoading: false });
            return false;
        }
    },

    /**
     * Sign in with social credential (Mobile)
     * Use with credentials from native SDKs (expo-google-sign-in, etc.)
     */
    socialLoginMobile: async (credential) => {
        set({ isLoading: true, error: null });
        try {
            const result = await signInWithCredential(auth, credential);
            const idToken = await result.user.getIdToken();
            await get().syncWithBackend(idToken);
            set({ isLoading: false });
            return true;
        } catch (error) {
            set({ error: error.message, isLoading: false });
            return false;
        }
    },

    /**
     * Sign out
     */
    logout: async () => {
        try {
            // Sign out from Firebase (this is all that's needed with token-only auth)
            await signOut(auth);
            set({ user: null, firebaseUser: null, isAuthenticated: false });
        } catch (error) {
            console.error('Logout error:', error);
            set({ error: error.message });
        }
    },

    /**
     * Check authentication status by fetching current user from backend
     * Uses Bearer token authentication
     */
    checkAuth: async () => {
        set({ isLoading: true });
        try {
            const idToken = await get().getIdToken();
            if (!idToken) {
                set({ user: null, isLoading: false, isAuthenticated: false });
                return;
            }

            const response = await fetch(`${API_URL}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${idToken}`,
                },
            });

            if (response.ok) {
                const user = await response.json();
                set({ user, isLoading: false, isAuthenticated: true });
            } else {
                set({ user: null, isLoading: false, isAuthenticated: false });
            }
        } catch (error) {
            set({ user: null, isLoading: false, isAuthenticated: false });
        }
    },

    /**
     * Get current Firebase ID token for API calls
     */
    getIdToken: async () => {
        const currentUser = auth.currentUser;
        if (currentUser) {
            return await currentUser.getIdToken();
        }
        return null;
    },

    /**
     * Make authenticated API request
     * Helper method that includes the Bearer token automatically
     */
    authenticatedFetch: async (url, options = {}) => {
        const idToken = await get().getIdToken();
        if (!idToken) {
            throw new Error('Not authenticated');
        }

        return fetch(url, {
            ...options,
            headers: {
                ...options.headers,
                'Authorization': `Bearer ${idToken}`,
            },
        });
    },

    /**
     * Clear error
     */
    clearError: () => set({ error: null }),
}));

export default useFirebaseAuthStore;
