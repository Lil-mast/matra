import { db, auth } from '../firebase';
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';
import { router, showToast, getApiToken } from '../main';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

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

            <section class="mt-xl p-lg border border-outline-variant rounded-2xl bg-surface-container-lowest">
                <div class="flex flex-col gap-md">
                    <div class="flex flex-wrap items-center justify-between gap-4">
                        <div>
                            <h3 class="text-label-md font-headline-small text-on-surface">Voice Assistant</h3>
                            <p class="text-body-sm font-body-sm text-on-surface-variant mt-1">Record patient responses and let Matra extract triage values automatically.</p>
                        </div>
                        <button id="voice-toggle-btn" type="button" class="px-4 py-2 bg-primary text-on-primary rounded-lg font-label-md hover:opacity-90 transition-colors">Start voice session</button>
                    </div>

                    <div id="voice-status" class="text-body-sm text-on-surface-variant">Voice session inactive.</div>
                    <div id="voice-transcript" class="text-body-sm text-on-surface-variant"></div>
                    <audio id="voice-response-player" controls class="w-full hidden mt-md"></audio>
                    <div id="voice-extracted" class="grid grid-cols-2 gap-sm mt-md"></div>
                </div>
            </section>
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

    setupVoiceAssistant();
}

async function setupVoiceAssistant() {
    const voiceToggleBtn = document.getElementById('voice-toggle-btn') as HTMLButtonElement | null;
    const voiceStatus = document.getElementById('voice-status');
    const voiceTranscript = document.getElementById('voice-transcript');
    const voicePlayer = document.getElementById('voice-response-player') as HTMLAudioElement | null;
    const voiceExtracted = document.getElementById('voice-extracted');
    if (!voiceToggleBtn || !voiceStatus || !voiceTranscript || !voicePlayer || !voiceExtracted) return;

    let mediaRecorder: MediaRecorder | null = null;
    let audioChunks: BlobPart[] = [];
    let voiceSessionId = '';
    let activeStream: MediaStream | null = null;

    const setStatus = (text: string) => {
        voiceStatus.textContent = text;
    };

    const setTranscript = (text: string) => {
        voiceTranscript.textContent = text;
    };

    const setExtracted = (data: Record<string, unknown> | null) => {
        voiceExtracted.innerHTML = '';
        if (!data) {
            voiceExtracted.innerHTML = '<div class="text-body-sm text-on-surface-variant">No extracted values yet.</div>';
            return;
        }

        const fields = [
            ['age', 'Age'],
            ['parity', 'Parity'],
            ['systolic_bp', 'Systolic BP'],
            ['diastolic_bp', 'Diastolic BP'],
            ['pulse', 'Pulse'],
            ['bleeding', 'Bleeding'],
            ['fever', 'Fever'],
            ['convulsions', 'Convulsions'],
            ['reduced_fetal_movement', 'Reduced movement'],
            ['anemia', 'Anemia'],
            ['risk_level', 'Risk level'],
            ['recommended_action', 'Recommended action']
        ];

        fields.forEach(([key, label]) => {
            if (data[key] !== undefined && data[key] !== null) {
                voiceExtracted.insertAdjacentHTML('beforeend', `
                    <div class="rounded-lg border border-outline-variant bg-surface p-sm">
                        <div class="text-label-sm text-on-surface-variant">${label}</div>
                        <div class="text-body-sm font-bold text-on-surface">${String(data[key])}</div>
                    </div>
                `);
            }
        });
    };

    const fillFormFields = (data: Record<string, unknown> | null) => {
        if (!data) return;

        const setField = (name: string, value: string | number | boolean) => {
            const input = document.querySelector(`[name="${name}"]`) as HTMLInputElement | HTMLSelectElement | null;
            if (!input) return;
            if (input.type === 'checkbox') {
                (input as HTMLInputElement).checked = Boolean(value);
            } else {
                input.value = String(value);
            }
        };

        const mapping: Array<[string, string]> = [
            ['age', 'age'],
            ['parity', 'parity'],
            ['systolic_bp', 'systolic_bp'],
            ['diastolic_bp', 'diastolic_bp'],
            ['pulse', 'pulse'],
            ['bleeding', 'bleeding'],
            ['fever', 'fever'],
            ['convulsions', 'convulsions'],
            ['reduced_fetal_movement', 'reduced_fetal_movement'],
            ['anemia', 'anemia']
        ];

        mapping.forEach(([source, target]) => {
            if (data[source] !== undefined) {
                setField(target, data[source] as string | number | boolean);
            }
        });
    };

    const getAuthHeaders = () => {
        const token = getApiToken();
        const headers: Record<string, string> = {};
        if (token) {
            headers.Authorization = `Bearer ${token}`;
        }
        return headers;
    };

    const ensureVoiceSession = async () => {
        if (!getApiToken()) {
            throw new Error('Voice assistant requires backend authentication. Please login again.');
        }
        if (voiceSessionId) return voiceSessionId;
        const response = await fetch(`${API_BASE_URL}/api/voice/session`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        if (!response.ok) {
            throw new Error('Unable to create voice session');
        }
        const payload = await response.json();
        voiceSessionId = payload.session_id;
        return voiceSessionId;
    };

    const createAudioUrl = (base64: string) => {
        const bytes = Uint8Array.from(atob(base64), c => c.charCodeAt(0));
        return URL.createObjectURL(new Blob([bytes], { type: 'audio/mpeg' }));
    };

    const stopRecording = () => {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        }
        if (activeStream) {
            activeStream.getTracks().forEach((track) => track.stop());
            activeStream = null;
        }
    };

    voiceToggleBtn.addEventListener('click', async () => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            setStatus('Stopping recording...');
            stopRecording();
            voiceToggleBtn.textContent = 'Start voice session';
            return;
        }

        try {
            await ensureVoiceSession();
            setStatus('Listening for patient audio...');
            audioChunks = [];
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            activeStream = stream;
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };
            mediaRecorder.onstop = async () => {
                setStatus('Sending audio for transcription...');
                const blob = new Blob(audioChunks, { type: 'audio/webm' });
                const formData = new FormData();
                formData.append('audio', blob, 'voice.webm');

                const response = await fetch(`${API_BASE_URL}/api/voice/session/${voiceSessionId}/audio`, {
                    method: 'POST',
                    headers: {
                        ...getAuthHeaders()
                    },
                    body: formData
                });

                if (!response.ok) {
                    const error = await response.json().catch(() => null);
                    setStatus('Voice request failed.');
                    showToast(error?.error || 'Voice request failed', true);
                    return;
                }

                const data = await response.json();
                setStatus('Voice response received.');
                setTranscript(`Transcript: ${data.transcript}`);
                setExtracted(data.extracted_data ?? null);
                fillFormFields(data.extracted_data ?? null);

                if (data.audio_base64) {
                    voicePlayer.src = createAudioUrl(data.audio_base64);
                    voicePlayer.classList.remove('hidden');
                    voicePlayer.play().catch(() => {
                        /* ignore playback policy errors */
                    });
                }

                voiceToggleBtn.textContent = 'Start voice session';
            };
            mediaRecorder.start();
            voiceToggleBtn.textContent = 'Stop recording';
        } catch (err: any) {
            setStatus('Unable to start voice session.');
            showToast(err.message || 'Microphone access denied', true);
        }
    });
}
