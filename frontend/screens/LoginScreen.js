import { View, Text, TextInput, TouchableOpacity, SafeAreaView, ActivityIndicator, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import useAuthStore from '../store/authStore';
import { useState, useEffect } from 'react';
import * as WebBrowser from 'expo-web-browser';
import * as Google from 'expo-auth-session/providers/google';
import * as Facebook from 'expo-auth-session/providers/facebook';
import * as AppleAuthentication from 'expo-apple-authentication';
import Constants from 'expo-constants';

WebBrowser.maybeCompleteAuthSession();

export default function LoginScreen() {
    const navigation = useNavigation();
    const login = useAuthStore((state) => state.login);
    const socialLogin = useAuthStore((state) => state.socialLogin);
    const isLoading = useAuthStore((state) => state.isLoading);
    const error = useAuthStore((state) => state.error);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const {
        googleIosClientId,
        googleAndroidClientId,
        googleWebClientId,
        facebookAppId
    } = Constants.expoConfig?.extra || {};

    // Google Auth
    const [request, response, promptAsync] = Google.useAuthRequest({
        iosClientId: googleIosClientId,
        androidClientId: googleAndroidClientId,
        webClientId: googleWebClientId,
    });

    useEffect(() => {
        if (response?.type === 'success') {
            const { authentication } = response;
            socialLogin('google', authentication.idToken || authentication.accessToken);
        } else if (response?.type === 'error') {
            Alert.alert('Google Login Error', 'Something went wrong');
        }
    }, [response]);

    // Facebook Auth
    const [fbRequest, fbResponse, fbPromptAsync] = Facebook.useAuthRequest({
        clientId: facebookAppId,
    });

    useEffect(() => {
        if (fbResponse?.type === 'success') {
            const { authentication } = fbResponse;
            socialLogin('facebook', authentication.accessToken);
        }
    }, [fbResponse]);

    // Apple Auth
    const handleAppleLogin = async () => {
        try {
            const credential = await AppleAuthentication.signInAsync({
                requestedScopes: [
                    AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
                    AppleAuthentication.AppleAuthenticationScope.EMAIL,
                ],
            });
            await socialLogin('apple', credential.identityToken);
        } catch (e) {
            if (e.code === 'ERR_CANCELED') {
                // Cancelled
            } else {
                Alert.alert('Apple Login Error', e.message);
            }
        }
    };

    const handleLogin = async () => {
        if (!email || !password) {
            Alert.alert('Error', 'Please enter both email and password');
            return;
        }
        await login(email, password);
    };

    return (
        <SafeAreaView className="flex-1 bg-slate-900">
            <KeyboardAvoidingView
                behavior={Platform.OS === "ios" ? "padding" : "height"}
                className="flex-1 justify-center px-8"
            >
                <View className="mb-12">
                    <Text className="text-4xl font-extrabold text-white mb-2 tracking-tighter">
                        Welcome Back
                    </Text>
                    <Text className="text-slate-400 text-base">
                        Sign in to continue to your account
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
                            placeholder="Enter your password"
                            placeholderTextColor="#64748b"
                            secureTextEntry
                            value={password}
                            onChangeText={setPassword}
                        />
                    </View>

                    <TouchableOpacity
                        className="bg-blue-600 p-4 rounded-xl mt-6 active:bg-blue-700 shadow-lg shadow-blue-500/30"
                        onPress={handleLogin}
                        disabled={isLoading}
                    >
                        {isLoading ? (
                            <ActivityIndicator color="white" />
                        ) : (
                            <Text className="text-white text-center font-bold text-lg">Sign In</Text>
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
                            onPress={() => promptAsync()}
                            disabled={!request || isLoading}
                        >
                            <Text className="text-black font-bold text-lg">Google</Text>
                        </TouchableOpacity>

                        {/* Facebook */}
                        <TouchableOpacity
                            className="bg-[#1877F2] p-4 rounded-xl flex-row justify-center items-center"
                            onPress={() => fbPromptAsync()}
                            disabled={!fbRequest || isLoading}
                        >
                            <Text className="text-white font-bold text-lg">Facebook</Text>
                        </TouchableOpacity>

                        {/* Apple */}
                        {Platform.OS === 'ios' && (
                            <AppleAuthentication.AppleAuthenticationButton
                                buttonType={AppleAuthentication.AppleAuthenticationButtonType.SIGN_IN}
                                buttonStyle={AppleAuthentication.AppleAuthenticationButtonStyle.WHITE}
                                cornerRadius={12}
                                style={{ width: '100%', height: 50 }}
                                onPress={handleAppleLogin}
                            />
                        )}
                    </View>

                    <View className="flex-row justify-center mt-6">
                        <Text className="text-slate-400">Don't have an account? </Text>
                        <TouchableOpacity onPress={() => navigation.navigate('Signup')}>
                            <Text className="text-blue-400 font-bold">Sign Up</Text>
                        </TouchableOpacity>
                    </View>
                </View>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
}
