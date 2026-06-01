export function getLandingView() {
    return `
    <!-- Hero Section -->
    <section class="relative pt-2xl pb-3xl px-gutter lg:pt-3xl lg:pb-3xl overflow-hidden bg-gradient-to-br from-surface-bright to-surface-container-low">
    <div class="max-w-container-max mx-auto grid grid-cols-1 lg:grid-cols-2 gap-2xl items-center relative z-10">
    <div class="flex flex-col gap-lg z-20">
    <div class="inline-flex items-center gap-2 bg-secondary-container text-on-secondary-container px-3 py-1 rounded-full w-max text-label-sm font-label-sm border border-secondary/20">
    <span class="material-symbols-outlined text-sm">verified</span>
                            Clinical-Grade Assessment Tool
                        </div>
    <h1 class="text-headline-lg-mobile font-headline-lg-mobile md:text-headline-xl md:font-headline-xl text-on-background max-w-2xl">
                            Empowering Safer Motherhood Through Early Warning
                        </h1>
    <p class="text-body-lg font-body-lg text-on-surface-variant max-w-xl">
                            Matra helps healthcare providers identify and manage maternal risks in real-time with clinical-grade assessment tools, connecting clinics and hospitals for seamless care.
                        </p>
    <div class="flex flex-col sm:flex-row gap-md mt-md">
    <a href="/triage" data-nav class="bg-primary text-on-primary font-label-md rounded-lg px-xl py-3 hover:shadow-lg transition-all duration-200 text-center">
                                Start Assessment
                            </a>
    <a href="/dashboard" data-nav class="border border-primary text-primary font-label-md rounded-lg px-xl py-3 hover:bg-surface-container transition-all duration-200 text-center flex items-center justify-center gap-2">
    <span class="material-symbols-outlined">dashboard</span>
                                View Dashboard
                            </a>
    </div>
    <div class="mt-lg flex items-center gap-md text-sm text-on-surface-variant">
    <div class="flex -space-x-2">
    <img class="w-8 h-8 rounded-full border-2 border-surface object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCbTc1lQ4s78SSGM4zXb08WPb_XcHGlbUNA-1uNfEec_QXqM31KlCQiqlILcGTgI73SSdgsbjZizsOFo_8Pa_2s3TJcAJYPS1EqRCDhWTDxosTIQOgzQTzTaeX8iD6jgiV4d1mznZkLYmUE2-2y3BMZ-aRBKlfTpmWnfx3Euf6xKqf7DYUXcICvuh1S2c3tsNMgQ5qEJNydUXHSQ8io7eXWEML13rhiym2w1QxoGeCmCNCeLYJZ4cFqKJwqsUlq7hECSUNH-0EOOJjX" />
    <img class="w-8 h-8 rounded-full border-2 border-surface object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDELjEomdVA3gXzZn6Q6kiJBuf3_0EB705PnUyKG7RVlFqWXW5vkXS1a1QdzKwIye-hhOnxkQTOYHCFblPB0UumI6BzFukZscom7rb1kjCED4ILaadnOzZ2EF1U0Jz2AC2jKr09oskn8Ha3ghbWAAWcoFAfZkyYZBmEFoMp3FB710iDr4z1zvgPA7NsjfDZIluMhiMyuAihrrB19wCE81yfPwN_nZ_zQ-_LeY-GQt531a0YWGM2slSkQ9oxlIz3jhwvlRTCq47eFOXI" />
    <img class="w-8 h-8 rounded-full border-2 border-surface object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuD_BzLcgw2-jU2Awxbj4eQyZBqcCi6ETeZRuGAVxyb8bSdOv9XwcdF5cmzr7yt1XafTDLmTlkRafF0AQpfiWxxGRSXWIQiAil-2t-M8OUDeRZb4_umx2YQBtHXiOiLYRYL9FY7jbFeUVxkIqR-eKlPXuzyddsez9zRE7JmJfLLmGyyEJt7vx8vc7pXVAetDfjS7ntmltXIxIpTYD4EXZPougZc0dPj7Fc4MrrikAqVq5wm3yItfnHUjWdB02oC-MZLG6ctMPBRIHx2p" />
    </div>
    <span>Designed for clinical precision, built for human empathy.</span>
    </div>
    </div>
    <div class="relative w-full h-[500px] lg:h-[600px] rounded-2xl overflow-hidden shadow-2xl z-10 border border-outline-variant/30">
    <img class="absolute inset-0 w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCKjTsVP7acKhG_kiuXgWQI5okQN0Um5K56rJxtM6E6bIwPth5xSclL0x7llRiHauD7HoLKjRVaTWTDLTggWgOqgIVgWspGif8-xf3Uj6KiO1_W9kKKJa0aPThpZPUkvrNEpp1rL9gCZiaU1WzwT8cljWu1bWPrZJKrn70EwUuA65sErgPuOc6p_imuWUHaFG4Onyip-MD85rLFNVkiawX-1Uil0oVkj4rq4eGiJSBLDw8ip2S7tGPH8143IDsnl03r6Ro9jQNPerEd" />
    <!-- Floating UI Element -->
    <div class="absolute bottom-lg left-lg right-lg glass-panel rounded-xl p-md shadow-lg flex items-center gap-md">
    <div class="bg-error-container text-on-error-container rounded-full w-12 h-12 flex items-center justify-center shrink-0">
    <span class="material-symbols-outlined" data-weight="fill">vital_signs</span>
    </div>
    <div>
    <p class="text-label-sm font-label-sm text-on-surface-variant uppercase tracking-wider">Alert Detected</p>
    <p class="text-headline-sm font-headline-sm text-on-surface">Elevated Blood Pressure</p>
    </div>
    <a href="/triage" data-nav class="ml-auto bg-primary text-on-primary text-sm px-4 py-2 rounded-lg font-medium">Review</a>
    </div>
    </div>
    </div>
    <!-- Decorative background elements -->
    <div class="absolute top-0 right-0 -mr-[20%] -mt-[10%] w-[50%] h-[80%] rounded-full bg-primary-fixed/20 blur-3xl -z-0"></div>
    <div class="absolute bottom-0 left-0 -ml-[10%] -mb-[10%] w-[40%] h-[60%] rounded-full bg-secondary-fixed/20 blur-3xl -z-0"></div>
    </section>
    
    <!-- Value Proposition (Bento Grid) -->
    <section class="py-3xl px-gutter bg-surface-lowest" id="features">
    <div class="max-w-container-max mx-auto">
    <div class="text-center mb-2xl">
    <h2 class="text-headline-lg-mobile font-headline-lg-mobile md:text-headline-lg md:font-headline-lg text-on-surface mb-sm">Comprehensive Maternal Care</h2>
    <p class="text-body-lg font-body-lg text-on-surface-variant max-w-2xl mx-auto">Engineered to address WHO SDG 3.1: Reducing global maternal mortality.</p>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-lg">
    <!-- Pillar 1 -->
    <div class="bg-surface rounded-2xl p-lg card-shadow hover-shadow transition-shadow duration-300 border border-surface-variant flex flex-col md:col-span-2">
    <div class="bg-primary-container text-on-primary-container w-12 h-12 rounded-xl flex items-center justify-center mb-md">
    <span class="material-symbols-outlined text-2xl">ecg</span>
    </div>
    <h3 class="text-headline-md font-headline-md text-on-surface mb-sm">Early Risk Detection</h3>
    <p class="text-body-md font-body-md text-on-surface-variant mb-lg max-w-md">Utilize sophisticated clinical algorithms to identify potential complications before they become critical. Our system continuously monitors vitals and historical data to flag subtle changes.</p>
    <div class="mt-auto bg-surface-container-low rounded-xl p-md border border-outline-variant/50">
    <div class="flex items-center gap-sm mb-xs">
    <span class="w-2 h-2 rounded-full bg-error"></span>
    <span class="text-label-sm font-label-sm font-bold text-on-surface">High Risk Indicator</span>
    </div>
    <div class="h-2 bg-surface-variant rounded-full overflow-hidden">
    <div class="h-full bg-error w-3/4 rounded-full"></div>
    </div>
    </div>
    </div>
    <!-- Pillar 2 -->
    <div class="bg-surface rounded-2xl p-lg card-shadow hover-shadow transition-shadow duration-300 border border-surface-variant flex flex-col">
    <div class="bg-secondary-container text-on-secondary-container w-12 h-12 rounded-xl flex items-center justify-center mb-md">
    <span class="material-symbols-outlined text-2xl">share</span>
    </div>
    <h3 class="text-headline-md font-headline-md text-on-surface mb-sm">Seamless Referrals</h3>
    <p class="text-body-md font-body-md text-on-surface-variant">Connect rural clinics directly with specialized hospitals. Ensure patient data travels instantly with the referral.</p>
    </div>
    <!-- Pillar 3 -->
    <div class="bg-surface rounded-2xl p-lg card-shadow hover-shadow transition-shadow duration-300 border border-surface-variant flex flex-col md:col-span-3 lg:col-span-1">
    <div class="bg-tertiary-container text-on-tertiary-container w-12 h-12 rounded-xl flex items-center justify-center mb-md">
    <span class="material-symbols-outlined text-2xl">wifi_off</span>
    </div>
    <h3 class="text-headline-md font-headline-md text-on-surface mb-sm">Offline Support</h3>
    <p class="text-body-md font-body-md text-on-surface-variant">Engineered for low-connectivity environments. Continue assessments offline and sync automatically.</p>
    </div>
    </div>
    </div>
    </section>
    
    <!-- Stats / Impact Section -->
    <section class="py-3xl px-gutter bg-primary text-on-primary" id="impact">
    <div class="max-w-container-max mx-auto">
    <div class="text-center mb-xl">
        <h2 class="text-headline-md font-headline-md text-primary-fixed">The Global Challenge (WHO Data)</h2>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-xl text-center divide-y md:divide-y-0 md:divide-x divide-primary-fixed/30">
    <div class="py-md md:py-0">
    <p class="text-headline-xl font-headline-xl mb-xs">800</p>
    <p class="text-body-lg font-body-lg text-primary-fixed">Women Die Every Day<br/><span class="text-sm opacity-75">from preventable causes (2020)</span></p>
    </div>
    <div class="py-md md:py-0">
    <p class="text-headline-xl font-headline-xl mb-xs">95%</p>
    <p class="text-body-lg font-body-lg text-primary-fixed">Occur in LMICs<br/><span class="text-sm opacity-75">Low & lower-middle income countries</span></p>
    </div>
    <div class="py-md md:py-0">
    <p class="text-headline-xl font-headline-xl mb-xs">SDG 3.1</p>
    <p class="text-body-lg font-body-lg text-primary-fixed">Reduce Mortality<br/><span class="text-sm opacity-75">to < 70 per 100,000 births by 2030</span></p>
    </div>
    </div>
    </div>
    </section>
    `
}
