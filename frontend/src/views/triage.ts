import { db, auth } from '../firebase';
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';
import { router, showToast } from '../main';

// Basic client-side triage logic (mimics backend for immediate feedback)
function evaluateRisk(data: any): { risk_level: 'high' | 'intermediate' | 'low', recommended_action: string } {
    let score = 0;
    
    if (data.convulsions || data.bleeding == 2 || data.systolic_bp >= 160 || data.diastolic_bp >= 110) {
        return { risk_level: 'high', recommended_action: 'IMMEDIATE REFERRAL TO HOSPITAL' };
    }
    
    if (data.fever) score += 2;
    if (data.reduced_fetal_movement) score += 2;
    if (data.bleeding == 1) score += 2;
    if (data.anemia) score += 1;
    if (data.systolic_bp >= 140 || data.diastolic_bp >= 90) score += 2;
    if (data.pulse > 100) score += 1;
    
    if (score >= 3) {
        return { risk_level: 'high', recommended_action: 'REFER TO HOSPITAL' };
    } else if (score >= 1) {
        return { risk_level: 'intermediate', recommended_action: 'OBSERVE AND REASSESS IN 4 HOURS' };
    }
    
    return { risk_level: 'low', recommended_action: 'ROUTINE ANTENATAL CARE' };
}

export function getTriageView() {
    setTimeout(setupTriageForm, 0); // Setup after render

    return `
    <section class="py-xl px-gutter bg-surface-container-lowest min-h-screen flex items-center justify-center">
        <div class="max-w-xl w-full bg-surface rounded-2xl shadow-xl border border-outline-variant p-lg">
            <div class="mb-lg border-b border-outline-variant pb-md">
                <h2 class="text-headline-md font-headline-md text-on-surface flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">edit_document</span>
                    New Triage Assessment
                </h2>
                <p class="text-body-sm font-body-sm text-on-surface-variant mt-1">Data is securely synced to Firestore.</p>
            </div>
            
            <form id="triage-form" class="flex flex-col gap-md">
                <div class="grid grid-cols-2 gap-md">
                    <div>
                        <label class="block text-label-md text-on-surface mb-1">Age</label>
                        <input type="number" name="age" required min="10" max="60" class="w-full rounded-lg border-outline-variant shadow-sm focus:border-primary focus:ring-primary" placeholder="Years">
                    </div>
                    <div>
                        <label class="block text-label-md text-on-surface mb-1">Parity</label>
                        <input type="number" name="parity" required min="0" class="w-full rounded-lg border-outline-variant shadow-sm focus:border-primary focus:ring-primary" placeholder="Number of previous births">
                    </div>
                </div>

                <div class="mt-sm">
                    <h3 class="text-label-md font-bold text-on-surface-variant uppercase tracking-wider mb-sm">Vitals</h3>
                    <div class="grid grid-cols-3 gap-sm">
                        <div>
                            <label class="block text-label-sm text-on-surface mb-1">Systolic BP</label>
                            <input type="number" name="systolic_bp" required placeholder="mmHg" class="w-full rounded-lg border-outline-variant shadow-sm focus:border-primary focus:ring-primary">
                        </div>
                        <div>
                            <label class="block text-label-sm text-on-surface mb-1">Diastolic BP</label>
                            <input type="number" name="diastolic_bp" required placeholder="mmHg" class="w-full rounded-lg border-outline-variant shadow-sm focus:border-primary focus:ring-primary">
                        </div>
                        <div>
                            <label class="block text-label-sm text-on-surface mb-1">Pulse</label>
                            <input type="number" name="pulse" required placeholder="bpm" class="w-full rounded-lg border-outline-variant shadow-sm focus:border-primary focus:ring-primary">
                        </div>
                    </div>
                </div>

                <div class="mt-sm border-t border-outline-variant pt-md">
                    <h3 class="text-label-md font-bold text-on-surface-variant uppercase tracking-wider mb-sm">Danger Signs</h3>
                    
                    <div class="mb-sm">
                        <label class="block text-label-sm text-on-surface mb-1">Bleeding</label>
                        <select name="bleeding" class="w-full rounded-lg border-outline-variant shadow-sm focus:border-primary focus:ring-primary">
                            <option value="0">None</option>
                            <option value="1">Light/Moderate</option>
                            <option value="2">Severe</option>
                        </select>
                    </div>

                    <div class="grid grid-cols-2 gap-sm">
                        <label class="flex items-center gap-2 text-body-sm text-on-surface cursor-pointer">
                            <input type="checkbox" name="fever" class="rounded text-primary focus:ring-primary">
                            Fever
                        </label>
                        <label class="flex items-center gap-2 text-body-sm text-on-surface cursor-pointer">
                            <input type="checkbox" name="convulsions" class="rounded text-error focus:ring-error">
                            Convulsions
                        </label>
                        <label class="flex items-center gap-2 text-body-sm text-on-surface cursor-pointer">
                            <input type="checkbox" name="reduced_fetal_movement" class="rounded text-primary focus:ring-primary">
                            Reduced Fetal Movement
                        </label>
                        <label class="flex items-center gap-2 text-body-sm text-on-surface cursor-pointer">
                            <input type="checkbox" name="anemia" class="rounded text-primary focus:ring-primary">
                            Severe Anemia / Pallor
                        </label>
                    </div>
                </div>

                <div class="mt-lg pt-md border-t border-outline-variant flex justify-end gap-3">
                    <button type="button" onclick="window.history.back()" class="px-6 py-2 border border-outline rounded-lg text-on-surface-variant font-label-md hover:bg-surface-variant transition-colors">Cancel</button>
                    <button type="submit" class="px-6 py-2 bg-primary text-on-primary rounded-lg font-label-md hover:opacity-90 shadow-sm flex items-center gap-2">
                        <span class="material-symbols-outlined text-sm">save</span> Save Assessment
                    </button>
                </div>
            </form>
        </div>
    </section>
    `;
}

function setupTriageForm() {
    const form = document.getElementById('triage-form') as HTMLFormElement;
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!auth.currentUser) {
            showToast('You must be logged in', true);
            return;
        }

        const formData = new FormData(form);
        const data = {
            age: parseInt(formData.get('age') as string) || 0,
            parity: parseInt(formData.get('parity') as string) || 0,
            systolic_bp: parseInt(formData.get('systolic_bp') as string) || 0,
            diastolic_bp: parseInt(formData.get('diastolic_bp') as string) || 0,
            pulse: parseInt(formData.get('pulse') as string) || 0,
            bleeding: parseInt(formData.get('bleeding') as string) || 0,
            fever: formData.get('fever') === 'on',
            convulsions: formData.get('convulsions') === 'on',
            reduced_fetal_movement: formData.get('reduced_fetal_movement') === 'on',
            anemia: formData.get('anemia') === 'on',
        };

        if (data.age <= 0 || data.systolic_bp <= 0 || data.diastolic_bp <= 0) {
            showToast('Please provide valid numbers for Age and Vitals', true);
            return;
        }

        const evalResult = evaluateRisk(data);

        try {
            await addDoc(collection(db, "assessments"), {
                ...data,
                ...evalResult,
                userId: auth.currentUser.uid,
                createdAt: serverTimestamp()
            });
            showToast(`Assessment saved. Risk: ${evalResult.risk_level.toUpperCase()}`);
            router.navigate('/dashboard');
        } catch (err: any) {
            showToast('Error saving assessment', true);
            console.error(err);
        }
    });
}
