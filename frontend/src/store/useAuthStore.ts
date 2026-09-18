import { create } from 'zustand';
import { auth, onAuthStateChanged, FirebaseUser } from '../api/firebase';

export interface AuthUserInfo {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
}

interface AuthState {
  status: 'LOADING' | 'AUTHENTICATED' | 'UNAUTHENTICATED';
  user: AuthUserInfo | null;
  idToken: string | null;
  error: string | null;
  isAuthModalOpen: boolean;
  openAuthModal: () => void;
  closeAuthModal: () => void;
  setError: (error: string | null) => void;
  setUserFromFirebase: (firebaseUser: FirebaseUser | null, token: string | null) => void;
  initAuthListener: () => () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  status: 'LOADING',
  user: null,
  idToken: null,
  error: null,
  isAuthModalOpen: false,

  openAuthModal: () => set({ isAuthModalOpen: true, error: null }),
  closeAuthModal: () => set({ isAuthModalOpen: false, error: null }),
  setError: (error) => set({ error }),

  setUserFromFirebase: (firebaseUser, token) => {
    if (firebaseUser) {
      set({
        status: 'AUTHENTICATED',
        user: {
          uid: firebaseUser.uid,
          email: firebaseUser.email,
          displayName: firebaseUser.displayName || (firebaseUser.email ? firebaseUser.email.split('@')[0] : 'Beneficiary'),
          photoURL: firebaseUser.photoURL,
        },
        idToken: token,
        error: null,
      });
    } else {
      set({
        status: 'UNAUTHENTICATED',
        user: null,
        idToken: null,
      });
    }
  },

  initAuthListener: () => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        try {
          const token = await firebaseUser.getIdToken();
          set({
            status: 'AUTHENTICATED',
            user: {
              uid: firebaseUser.uid,
              email: firebaseUser.email,
              displayName: firebaseUser.displayName || (firebaseUser.email ? firebaseUser.email.split('@')[0] : 'Beneficiary'),
              photoURL: firebaseUser.photoURL,
            },
            idToken: token,
            error: null,
          });
        } catch (e: any) {
          set({
            status: 'AUTHENTICATED',
            user: {
              uid: firebaseUser.uid,
              email: firebaseUser.email,
              displayName: firebaseUser.displayName || 'Beneficiary',
              photoURL: firebaseUser.photoURL,
            },
            idToken: null,
            error: null,
          });
        }
      } else {
        set({
          status: 'UNAUTHENTICATED',
          user: null,
          idToken: null,
        });
      }
    });

    return unsubscribe;
  },
}));
