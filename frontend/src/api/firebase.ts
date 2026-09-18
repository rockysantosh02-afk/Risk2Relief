/**
 * Firebase Client SDK Initialization & Authentication Service.
 *
 * SCOPE CONSTRAINT:
 * Firebase is used EXCLUSIVELY for User Authentication and Identity Verification.
 * No Firestore, Realtime DB, Storage, Analytics, Functions, or Cloud Messaging are used.
 */

import { initializeApp, getApps, getApp } from 'firebase/app';
import {
  getAuth,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  signOut,
  onAuthStateChanged,
  User as FirebaseUser,
  UserCredential,
} from 'firebase/auth';

// Web App Firebase Configuration loaded securely from Vite environment variables
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || 'AIzaSyBT-3lDLriRD0VBpSGEScmXP7UQzJ_GZPA',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'risk2relief.firebaseapp.com',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'risk2relief',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || '1:978296699687:web:35dcdc1d1c8da9543a4702',
};

// Initialize Firebase App singleton
export const firebaseApp = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();

// Initialize Firebase Authentication ONLY
export const auth = getAuth(firebaseApp);

// Google Auth Provider
const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({ prompt: 'select_account' });

/**
 * Sign in with email and password
 */
export async function signInWithEmail(email: string, pass: string): Promise<UserCredential> {
  return await signInWithEmailAndPassword(auth, email, pass);
}

/**
 * Sign up / register with email and password
 */
export async function signUpWithEmail(email: string, pass: string): Promise<UserCredential> {
  return await createUserWithEmailAndPassword(auth, email, pass);
}

/**
 * Sign in with Google popup
 */
export async function signInWithGoogle(): Promise<UserCredential> {
  return await signInWithPopup(auth, googleProvider);
}

/**
 * Sign out current user
 */
export async function logOut(): Promise<void> {
  await signOut(auth);
}

/**
 * Retrieve active Firebase ID token for Authorization Bearer header
 */
export async function getCurrentIdToken(forceRefresh: boolean = false): Promise<string | null> {
  const user = auth.currentUser;
  if (!user) return null;
  try {
    return await user.getIdToken(forceRefresh);
  } catch (error) {
    console.warn('Failed to retrieve Firebase ID token:', error);
    return null;
  }
}

export { onAuthStateChanged };
export type { FirebaseUser };
