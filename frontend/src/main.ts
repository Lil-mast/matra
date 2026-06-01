import Navigo from 'navigo';
import { getLandingView } from './views/landing';
import { getDashboardView } from './views/dashboard';
import { getTriageView } from './views/triage';
import { getLoginView } from './views/login';
import { registerSW } from 'virtual:pwa-register';

import { auth } from './firebase';
import { signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut, onAuthStateChanged } from 'firebase/auth';

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
            showToast('Account created successfully');
            router.navigate('/dashboard');
        } catch (error: any) {
            showToast(error.message, true);
        }
    });
}
