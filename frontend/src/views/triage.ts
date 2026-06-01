export function getTriageView() {
    return `
    <section class="py-xl px-gutter bg-surface-container-lowest min-h-screen flex items-center justify-center">
        <div class="max-w-xl w-full bg-surface rounded-2xl shadow-xl border border-outline-variant p-lg">
            <div class="mb-lg border-b border-outline-variant pb-md">
                <h2 class="text-headline-md font-headline-md text-on-surface flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">edit_document</span>
                    New Triage Assessment
                </h2>
                <p class="text-body-sm font-body-sm text-on-surface-variant mt-1">Data is saved locally when offline.</p>
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
