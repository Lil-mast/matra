import Navigo from 'navigo';
import { getLandingView } from './views/landing';
import { getDashboardView } from './views/dashboard';
import { getTriageView } from './views/triage';
import { saveAssessment, getOfflineAssessments, markAsSynced } from './db';
import { registerSW } from 'virtual:pwa-register';

// Initialize router
const router = new Navigo('/');
const appDiv = document.getElementById('app')!;

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
function showToast(message: string, isError = false) {
    const toast = document.getElementById('toast');
    if (toast) {
        toast.textContent = message;
        toast.style.backgroundColor = isError ? '#ba1a1a' : '#001f29';
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 3000);
    }
}

// Router config
router
  .on('/', () => {
    appDiv.innerHTML = getLandingView();
  })
  .on('/dashboard', async () => {
    appDiv.innerHTML = await getDashboardView();
  })
  .on('/triage', () => {
    appDiv.innerHTML = getTriageView();
    setupTriageForm();
  })
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

function setupTriageForm() {
    const form = document.getElementById('triage-form') as HTMLFormElement;
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const data = {
            age: parseInt(formData.get('age') as string),
            parity: parseInt(formData.get('parity') as string),
            systolic_bp: parseInt(formData.get('systolic_bp') as string),
            diastolic_bp: parseInt(formData.get('diastolic_bp') as string),
            pulse: parseInt(formData.get('pulse') as string),
            bleeding: parseInt(formData.get('bleeding') as string),
            fever: formData.get('fever') === 'on',
            convulsions: formData.get('convulsions') === 'on',
            reduced_fetal_movement: formData.get('reduced_fetal_movement') === 'on',
            anemia: formData.get('anemia') === 'on',
        };

        try {
            const result = await saveAssessment(data);
            showToast(`Assessment saved locally. Risk: ${result.risk_level.toUpperCase()}`);
            router.navigate('/dashboard');
        } catch (err) {
            showToast('Error saving assessment', true);
            console.error(err);
        }
    });
}

// Sync Logic
const syncStatusText = document.getElementById('sync-text');
const syncIndicator = document.getElementById('sync-indicator');
const syncBtn = document.getElementById('sync-btn');
const syncContainer = document.getElementById('sync-status');

function updateOnlineStatus() {
    if (navigator.onLine) {
        syncStatusText!.textContent = 'Online';
        syncIndicator!.className = 'w-2 h-2 rounded-full bg-primary';
        syncBtn!.classList.remove('hidden');
    } else {
        syncStatusText!.textContent = 'Offline';
        syncIndicator!.className = 'w-2 h-2 rounded-full bg-error';
        syncBtn!.classList.add('hidden');
    }
    syncContainer!.classList.remove('hidden');
}

window.addEventListener('online', updateOnlineStatus);
window.addEventListener('offline', updateOnlineStatus);
updateOnlineStatus();

syncBtn?.addEventListener('click', async () => {
    if (!navigator.onLine) return;
    
    try {
        syncBtn.classList.add('opacity-50', 'pointer-events-none');
        syncBtn.innerHTML = '<span class="material-symbols-outlined text-sm animate-spin">sync</span> Syncing...';
        
        const offlineData = await getOfflineAssessments();
        if (offlineData.length === 0) {
            showToast('Everything is up to date.');
            return;
        }

        // Mock sync to backend (In a real app, POST to /api/sync)
        /*
        const res = await fetch('/api/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(offlineData)
        });
        if (!res.ok) throw new Error('Sync failed');
        */

        // Simulate network delay
        await new Promise((r: any) => setTimeout(r, 1000));
        
        const syncedIds = offlineData.map((r: any) => r.id!);
        await markAsSynced(syncedIds);
        
        showToast(`Successfully synced ${syncedIds.length} records.`);
        
        // Refresh dashboard if we are on it
        if (window.location.pathname === '/dashboard') {
            appDiv.innerHTML = await getDashboardView();
        }

    } catch (err) {
        showToast('Sync failed', true);
    } finally {
        syncBtn.classList.remove('opacity-50', 'pointer-events-none');
        syncBtn.innerHTML = '<span class="material-symbols-outlined text-sm">sync</span> Sync';
    }
});
