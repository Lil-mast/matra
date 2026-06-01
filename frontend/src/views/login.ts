export function getLoginView() {
    return `
    <section class="py-xl px-gutter bg-surface-container-lowest min-h-screen flex items-center justify-center">
        <div class="max-w-md w-full bg-surface rounded-2xl shadow-xl border border-outline-variant p-lg">
            <div class="mb-lg border-b border-outline-variant pb-md text-center">
                <h2 class="text-headline-md font-headline-md text-on-surface">Secure Access</h2>
                <p class="text-body-sm font-body-sm text-on-surface-variant mt-1">Sign in to Matra Health</p>
            </div>
            
            <form id="login-form" class="flex flex-col gap-md">
                <div>
                    <label class="block text-label-md text-on-surface mb-1">Email</label>
                    <input type="email" name="email" required class="w-full rounded-lg border-outline-variant shadow-sm focus:border-primary focus:ring-primary" placeholder="clinician@matra.health">
                </div>
                <div>
                    <label class="block text-label-md text-on-surface mb-1">Password</label>
                    <input type="password" name="password" required class="w-full rounded-lg border-outline-variant shadow-sm focus:border-primary focus:ring-primary" placeholder="••••••••">
                </div>
                
                <div class="mt-md flex flex-col gap-3">
                    <button type="submit" class="w-full py-2 bg-primary text-on-primary rounded-lg font-label-md hover:opacity-90 shadow-sm flex justify-center items-center gap-2">
                        <span class="material-symbols-outlined text-sm">login</span> Sign In
                    </button>
                    <button type="button" id="signup-btn" class="w-full py-2 border border-primary text-primary rounded-lg font-label-md hover:bg-surface-container transition-colors">
                        Create Account
                    </button>
                </div>
            </form>
        </div>
    </section>
    `;
}
