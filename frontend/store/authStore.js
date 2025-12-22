import { create } from 'zustand';
import { API_URL } from '../config';

const useAuthStore = create((set, get) => ({
    user: null,
    error: null,
    isLoading: false,

    login: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
            const response = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
                credentials: 'include',
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Login failed');
            }

            set({ user: { email }, isLoading: false });
            return true; // Success
        } catch (error) {
            set({ error: error.message, isLoading: false });
            return false; // Failed
        }
    },

    signup: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
            const response = await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
                credentials: 'include',
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Signup failed');
            }

            // Auto login after signup
            return await get().login(email, password);
        } catch (error) {
            set({ error: error.message, isLoading: false });
            return false;
        }
    },

    socialLogin: async (provider, token) => {
        set({ isLoading: true, error: null });
        try {
            const response = await fetch(`${API_URL}/auth/${provider}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token }),
                credentials: 'include',
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `${provider} login failed`);
            }

            set({ user: { email: data.email }, isLoading: false });
            return true;
        } catch (error) {
            set({ error: error.message, isLoading: false });
            return false;
        }
    },

    logout: async () => {
        try {
            await fetch(`${API_URL}/auth/logout`, { method: 'POST', credentials: 'include' });
        } catch (e) {
            console.error(e);
        }
        set({ user: null });
    },

    checkAuth: async () => {
        set({ isLoading: true });
        try {
            const response = await fetch(`${API_URL}/auth/me`, { credentials: 'include' });
            if (response.ok) {
                const user = await response.json();
                set({ user, isLoading: false });
            } else {
                set({ user: null, isLoading: false });
            }
        } catch (error) {
            set({ user: null, isLoading: false });
        }
    },
}));

export default useAuthStore;
