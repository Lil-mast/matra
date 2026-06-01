import { db, auth } from '../firebase';
import { collection, query, where, getDocs, orderBy } from 'firebase/firestore';

export async function getDashboardView() {
    if (!auth.currentUser) return '';

    let assessments: any[] = [];
    try {
        const q = query(
            collection(db, "assessments"), 
            where("userId", "==", auth.currentUser.uid),
            orderBy("createdAt", "desc")
        );
        const querySnapshot = await getDocs(q);
        querySnapshot.forEach((doc) => {
            assessments.push({ id: doc.id, ...doc.data() });
        });
    } catch (e: any) {
        // If offline and index not cached, it might fail or return from cache
        console.error("Error fetching assessments: ", e);
    }
    
    // In Firestore offline mode with getDocs, it will fetch from local cache if offline.
    // The concept of 'pending sync' is handled transparently by Firestore. We won't try to manually calculate it here.
    const highRiskCount = assessments.filter((a: any) => a.risk_level === 'high').length;
    
    let listHTML = '';
    
    if (assessments.length === 0) {
        listHTML = '<div class="p-4 text-on-surface-variant text-center">No assessments found.</div>';
    } else {
        assessments.forEach((a: any) => {
            // Firestore serverTimestamp might be null when pending offline sync
            const date = a.createdAt ? new Date(a.createdAt.toDate()).toLocaleString() : 'Pending Sync...';
            const badgeColor = a.risk_level === 'high' ? 'bg-error-container text-on-error-container' : 
                               (a.risk_level === 'intermediate' ? 'bg-tertiary-container text-on-tertiary-container' : 'bg-secondary-container text-on-secondary-container');
            
            listHTML += `
            <div class="flex items-center justify-between p-4 border-b border-outline-variant/50 hover:bg-surface-container-lowest transition-colors">
                <div class="flex items-center gap-4">
                    <div class="w-10 h-10 rounded-full bg-surface-variant flex items-center justify-center text-on-surface-variant font-bold text-sm">
                        <span class="material-symbols-outlined text-outline text-sm">assignment</span>
                    </div>
                    <div>
                        <p class="text-label-md font-label-md text-on-surface">Age: ${a.age}</p>
                        <p class="text-body-sm font-body-sm text-on-surface-variant">${date}</p>
                    </div>
                </div>
                <div class="flex flex-col items-end gap-1">
                    <span class="px-3 py-1 rounded-full ${badgeColor} text-xs font-bold capitalize">${a.risk_level} Risk</span>
                </div>
            </div>
            `;
        });
    }

    return `
    <section class="py-3xl px-gutter bg-surface-container-lowest min-h-screen">
        <div class="max-w-container-max mx-auto">
            <div class="mb-lg flex flex-col md:flex-row md:items-end justify-between gap-lg">
                <div class="max-w-2xl">
                    <h2 class="text-headline-lg-mobile font-headline-lg-mobile md:text-headline-lg md:font-headline-lg text-on-surface mb-sm">Clinical Dashboard</h2>
                    <p class="text-body-lg font-body-lg text-on-surface-variant">Information organized for rapid cognitive processing.</p>
                </div>
                <a href="/triage" data-nav class="bg-primary text-on-primary font-label-md rounded-lg px-6 py-2 hover:opacity-90 shadow-sm flex items-center gap-2">
                    <span class="material-symbols-outlined">add</span> New Assessment
                </a>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-4 gap-lg bg-background rounded-2xl border border-outline-variant shadow-2xl p-lg">
                
                <!-- Main Content Area -->
                <div class="lg:col-span-4 flex flex-col gap-lg">
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-md">
                        <div class="bg-surface p-md rounded-xl card-shadow border-l-4 border-error">
                            <p class="text-label-sm font-label-sm text-on-surface-variant mb-1">High Risk Alerts</p>
                            <p class="text-headline-md font-headline-md text-on-surface">${highRiskCount}</p>
                        </div>
                        <div class="bg-surface p-md rounded-xl card-shadow border-l-4 border-secondary">
                            <p class="text-label-sm font-label-sm text-on-surface-variant mb-1">Total Assessments</p>
                            <p class="text-headline-md font-headline-md text-on-surface">${assessments.length}</p>
                        </div>
                    </div>
                    
                    <div class="bg-surface rounded-xl card-shadow border border-surface-variant overflow-hidden">
                        <div class="p-4 border-b border-outline-variant bg-surface-container-lowest">
                            <h4 class="text-headline-sm font-headline-sm text-on-surface">Recent Assessments</h4>
                        </div>
                        <div class="p-0">
                            ${listHTML}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
    `;
}
