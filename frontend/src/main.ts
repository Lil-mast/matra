import Navigo from 'navigo';
import { getLandingView } from './views/landing';
import { getDashboardView } from './views/dashboard';
import { getTriageView } from './views/triage';
import { getLoginView } from './views/login';
import { registerSW } from 'virtual:pwa-register';

import { auth } from './firebase';
import { signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut, onAuthStateChanged } from 'firebase/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export function getApiToken() {
    return localStorage.getItem('MATRA_API_TOKEN');
}

export function setApiToken(token: string) {
    localStorage.setItem('MATRA_API_TOKEN', token);
}

async function backendLogin(username: string, password: string) {
    if (!API_BASE_URL) {
        throw new Error('Backend API base URL is not configured');
    }

    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
    });

    if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.error || 'Backend login failed');
    }

    const data = await response.json();
    return data.token;
}

async function backendRegister(username: string, password: string) {
    if (!API_BASE_URL) {
        throw new Error('Backend API base URL is not configured');
    }

    const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password, role: 'chw' })
    });

    if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        const error = new Error(body.error || 'Backend registration failed');
        (error as any).status = response.status;
        throw error;
    }

    const data = await response.json();
    return data.token;
}

// Initialize router
export const router = new Navigo('/');
const appDiv = document.getElementById('app')!;
const authLink = document.getElementById('auth-link')!;
const logoutBtn = document.getElementById('logout-btn')!;

let currentUser: any = null;

onAuthStateChanged(auth, (user) => {
    currentUser = user;
    if (user) {
        authLink.classList.add('hidden');
        logoutBtn.classList.remove('hidden');
    } else {
        authLink.classList.remove('hidden');
        logoutBtn.classList.add('hidden');
        if (window.location.pathname === '/dashboard' || window.location.pathname === '/triage') {
            router.navigate('/login');
        }
    }
});

logoutBtn.addEventListener('click', async () => {
    await signOut(auth);
    showToast('Logged out successfully');
    router.navigate('/');
});

// Setup PWA
// @ts-ignore
const updateSW = registerSW({
  onNeedRefresh() {
    showToast('New update available. Refresh to update.');
  },
  onOfflineReady() {
    showToast('App ready to work offline');
  },
});

// Toast notification
export function showToast(message: string, isError = false) {
    const toast = document.getElementById('toast');
    if (toast) {
        toast.textContent = message;
        toast.style.backgroundColor = isError ? '#ba1a1a' : '#001f29';
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 3000);
    }
}

const requireAuth = (callback: () => void) => {
    return () => {
        if (!currentUser && auth.currentUser === null) {
            showToast('Please login to access this page', true);
            router.navigate('/login');
        } else {
            callback();
        }
    };
};

// Router config
router
  .on('/', () => {
    appDiv.innerHTML = getLandingView();
  })
  .on('/login', () => {
      if (currentUser) {
          router.navigate('/dashboard');
          return;
      }
      appDiv.innerHTML = getLoginView();
      setupLoginForm();
  })
  .on('/dashboard', requireAuth(async () => {
    appDiv.innerHTML = await getDashboardView();
  }))
  .on('/triage', requireAuth(() => {
    appDiv.innerHTML = getTriageView();
    // Logic for setting up triage form moved to triage.ts
  }))
  .resolve();

// Catch all nav links
document.body.addEventListener('click', (e) => {
    const target = e.target as HTMLElement;
    const link = target.closest('a[data-nav]') || target.closest('div[data-nav]');
    if (link) {
        e.preventDefault();
        const href = link.getAttribute('href') || link.getAttribute('data-nav');
        if (href) router.navigate(href);
    }
});

function setupLoginForm() {
    const form = document.getElementById('login-form') as HTMLFormElement;
    const signupBtn = document.getElementById('signup-btn')!;
    
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = (form.elements.namedItem('email') as HTMLInputElement).value;
        const password = (form.elements.namedItem('password') as HTMLInputElement).value;
        try {
            await signInWithEmailAndPassword(auth, email, password);
            try {
                const token = await backendLogin(email, password);
                setApiToken(token);
            } catch (backendError: any) {
                showToast('Logged in, but backend voice auth unavailable.', true);
            }
            showToast('Logged in successfully');
            router.navigate('/dashboard');
        } catch (error: any) {
            showToast(error.message, true);
        }
    });

    signupBtn.addEventListener('click', async () => {
        const email = (form.elements.namedItem('email') as HTMLInputElement).value;
        const password = (form.elements.namedItem('password') as HTMLInputElement).value;
        if (!email || !password) {
            showToast('Enter email and password to signup', true);
            return;
        }
        try {
            await createUserWithEmailAndPassword(auth, email, password);
            try {
                const token = await backendRegister(email, password);
                setApiToken(token);
            } catch (backendError: any) {
                if ((backendError as any).status === 409) {
                    const token = await backendLogin(email, password);
                    setApiToken(token);
                } else {
                    showToast('Account created, but backend voice auth failed.', true);
                }
            }
            showToast('Account created successfully');
            router.navigate('/dashboard');
        } catch (error: any) {
            showToast(error.message, true);
        }
    });
}
