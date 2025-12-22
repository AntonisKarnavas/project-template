import { View, Text, TextInput, TouchableOpacity, SafeAreaView, ActivityIndicator, Alert, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import useAuthStore from '../store/authStore';
import { useState } from 'react';

export default function SignupScreen() {
    const navigation = useNavigation();
    const signup = useAuthStore((state) => state.signup);
    const isLoading = useAuthStore((state) => state.isLoading);
    const error = useAuthStore((state) => state.error);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    const handleSignup = async () => {
        if (!email || !password || !confirmPassword) {
            Alert.alert('Error', 'Please fill in all fields');
            return;
        }
        if (password !== confirmPassword) {
            Alert.alert('Error', 'Passwords do not match');
            return;
        }

        const success = await signup(email, password);
        if (success) {
            Alert.alert('Success', 'Account created successfully! Please login.');
            navigation.navigate('Login');
        }
    };

    return (
        <SafeAreaView className="flex-1 bg-slate-900">
            <KeyboardAvoidingView
                behavior={Platform.OS === "ios" ? "padding" : "height"}
                className="flex-1"
            >
                <ScrollView contentContainerStyle={{ flexGrow: 1, justifyContent: 'center' }} className="px-8">
                    <View className="mb-10">
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
                                placeholder="Create a password"
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
                                placeholder="Confirm your password"
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

                        <View className="flex-row justify-center mt-6 mb-8">
                            <Text className="text-slate-400">Already have an account? </Text>
                            <TouchableOpacity onPress={() => navigation.navigate('Login')}>
                                <Text className="text-blue-400 font-bold">Log In</Text>
                            </TouchableOpacity>
                        </View>
                    </View>
                </ScrollView>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
}
