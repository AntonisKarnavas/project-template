import { View, Text, TextInput, TouchableOpacity, SafeAreaView, ActivityIndicator, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import useFirebaseAuthStore from '../store/firebaseAuthStore';
import { useState, useEffect } from 'react';
import * as Google from 'expo-auth-session/providers/google';
import * as WebBrowser from 'expo-web-browser';
import { GoogleAuthProvider } from 'firebase/auth';
import Constants from 'expo-constants';

// Required for web-based OAuth redirects
WebBrowser.maybeCompleteAuthSession();

export default function SignupScreen() {
    const navigation = useNavigation();
    const signup = useFirebaseAuthStore((state) => state.signup);
    const googleLogin = useFirebaseAuthStore((state) => state.googleLogin);
    const socialLoginMobile = useFirebaseAuthStore((state) => state.socialLoginMobile);
    const isLoading = useFirebaseAuthStore((state) => state.isLoading);
    const error = useFirebaseAuthStore((state) => state.error);
    const clearError = useFirebaseAuthStore((state) => state.clearError);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    // Google OAuth configuration
    const [request, response, promptAsync] = Google.useAuthRequest({
        iosClientId: Constants.expoConfig?.extra?.googleIosClientId,
        androidClientId: Constants.expoConfig?.extra?.googleAndroidClientId,
        webClientId: Constants.expoConfig?.extra?.googleWebClientId,
    });

    // Handle Google OAuth response (mobile)
    useEffect(() => {
        if (response?.type === 'success') {
            const { id_token } = response.params;
            handleGoogleCredential(id_token);
        }
    }, [response]);

    // Process Google credential and sign in with Firebase
    const handleGoogleCredential = async (idToken) => {
        try {
            const credential = GoogleAuthProvider.credential(idToken);
            const success = await socialLoginMobile(credential);
            if (success) {
                navigation.navigate('Home');
            }
        } catch (err) {
            Alert.alert('Error', err.message);
        }
    };

    // Clear error when component unmounts
    useEffect(() => {
        return () => clearError();
    }, []);

    // Show error alert
    useEffect(() => {
        if (error) {
            Alert.alert('Error', error);
        }
    }, [error]);

    const handleSignup = async () => {
        if (!email || !password || !confirmPassword) {
            Alert.alert('Error', 'Please fill in all fields');
            return;
        }

        if (password !== confirmPassword) {
            Alert.alert('Error', 'Passwords do not match');
            return;
        }

        if (password.length < 6) {
            Alert.alert('Error', 'Password must be at least 6 characters');
            return;
        }

        const success = await signup(email, password);
        if (success) {
            navigation.navigate('Home');
        }
    };

    const handleGoogleSignup = async () => {
        if (Platform.OS === 'web') {
            // Web uses Firebase popup
            const success = await googleLogin();
            if (success) {
                navigation.navigate('Home');
            }
        } else {
            // Mobile uses expo-auth-session
            if (request) {
                await promptAsync();
            } else {
                Alert.alert(
                    'Configuration Required',
                    'Google Sign-In requires OAuth Client IDs. Please configure GOOGLE_IOS_CLIENT_ID and GOOGLE_ANDROID_CLIENT_ID in your .env file.'
                );
            }
        }
    };

    return (
        <SafeAreaView className="flex-1 bg-slate-900">
            <KeyboardAvoidingView
                behavior={Platform.OS === "ios" ? "padding" : "height"}
                className="flex-1 justify-center px-8"
            >
                <View className="mb-12">
                    <Text className="text-4xl font-extrabold text-white mb-2 tracking-tighter">
                        Create Account
                    </Text>
                    <Text className="text-slate-400 text-base">
                        Sign up to get started
                    </Text>
                </View>

                {error && (
                    <View className="bg-red-500/10 border border-red-500/50 p-4 rounded-xl mb-6">
                        <Text className="text-red-400 text-center font-medium">{error}</Text>
                    </View>
                )}

                <View className="space-y-4">
                    <View>
                        <Text className="text-slate-300 mb-2 font-medium ml-1">Email</Text>
                        <TextInput
                            className="bg-slate-800 text-white p-4 rounded-xl border border-slate-700 focus:border-blue-500 placeholder:text-slate-500"
                            placeholder="name@example.com"
                            placeholderTextColor="#64748b"
                            value={email}
                            onChangeText={setEmail}
                            autoCapitalize="none"
                            keyboardType="email-address"
                        />
                    </View>

                    <View>
                        <Text className="text-slate-300 mb-2 font-medium ml-1">Password</Text>
                        <TextInput
                            className="bg-slate-800 text-white p-4 rounded-xl border border-slate-700 focus:border-blue-500"
                            placeholder="At least 6 characters"
                            placeholderTextColor="#64748b"
                            secureTextEntry
                            value={password}
                            onChangeText={setPassword}
                        />
                    </View>

                    <View>
                        <Text className="text-slate-300 mb-2 font-medium ml-1">Confirm Password</Text>
                        <TextInput
                            className="bg-slate-800 text-white p-4 rounded-xl border border-slate-700 focus:border-blue-500"
                            placeholder="Re-enter your password"
                            placeholderTextColor="#64748b"
                            secureTextEntry
                            value={confirmPassword}
                            onChangeText={setConfirmPassword}
                        />
                    </View>

                    <TouchableOpacity
                        className="bg-blue-600 p-4 rounded-xl mt-6 active:bg-blue-700 shadow-lg shadow-blue-500/30"
                        onPress={handleSignup}
                        disabled={isLoading}
                    >
                        {isLoading ? (
                            <ActivityIndicator color="white" />
                        ) : (
                            <Text className="text-white text-center font-bold text-lg">Sign Up</Text>
                        )}
                    </TouchableOpacity>

                    <View className="flex-row items-center my-6">
                        <View className="flex-1 h-px bg-slate-700" />
                        <Text className="mx-4 text-slate-500">Or continue with</Text>
                        <View className="flex-1 h-px bg-slate-700" />
                    </View>

                    <View className="space-y-3 mb-6">
                        {/* Google */}
                        <TouchableOpacity
                            className="bg-white p-4 rounded-xl flex-row justify-center items-center"
                            onPress={handleGoogleSignup}
                            disabled={isLoading}
                        >
                            <Text className="text-black font-bold text-lg">Google</Text>
                        </TouchableOpacity>
                    </View>

                    <View className="flex-row justify-center mt-6">
                        <Text className="text-slate-400">Already have an account? </Text>
                        <TouchableOpacity onPress={() => navigation.navigate('Login')}>
                            <Text className="text-blue-400 font-bold">Sign In</Text>
                        </TouchableOpacity>
                    </View>
                </View>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
}
