import { Platform } from 'react-native';

const LOCALHOST = Platform.OS === 'android' ? '10.0.2.2' : 'localhost';

export const API_URL = `http://${LOCALHOST}:8030`;
