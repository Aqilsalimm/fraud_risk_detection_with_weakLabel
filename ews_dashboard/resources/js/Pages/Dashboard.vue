<script setup>
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import { Head, Link, router } from '@inertiajs/vue3';
import { ref, watch } from 'vue';

const props = defineProps({
    records: Object,
    stats: Object,
    charts: Object,
    filters: Object,
    availableYears: Array,
    availableSectors: Array,
});

// Reactivity for search and filters
const search = ref(props.filters.search || '');
const year = ref(props.filters.year || '');
const status = ref(props.filters.status || '');
const weakT3 = ref(props.filters.weak_t3 !== null && props.filters.weak_t3 !== undefined ? props.filters.weak_t3 : '');
const weakT2 = ref(props.filters.weak_t2 !== null && props.filters.weak_t2 !== undefined ? props.filters.weak_t2 : '');

// Handle filter submission
const applyFilters = () => {
    router.get(route('dashboard'), {
        search: search.value,
        year: year.value,
        status: status.value,
        weak_t3: weakT3.value,
        weak_t2: weakT2.value,
    }, {
        preserveState: true,
        replace: true
    });
};

const resetFilters = () => {
    search.value = '';
    year.value = '';
    status.value = '';
    weakT3.value = '';
    weakT2.value = '';
    applyFilters();
};

// Auto apply filters on some change
watch([year, status, weakT3, weakT2], () => {
    applyFilters();
});

// For SVG circular progress calculations
const calculateCircumference = (radius) => 2 * Math.PI * radius;
const calculateStrokeOffset = (score, radius) => {
    const circumference = calculateCircumference(radius);
    return circumference - (score / 100) * circumference;
};
</script>

<template>
    <Head title="EWS Fraud Risk Dashboard" />

    <AuthenticatedLayout>
        <template #header>
            <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h2 class="text-2xl font-bold leading-tight text-slate-800 dark:text-slate-100 flex items-center gap-2">
                        <span class="p-2 bg-indigo-500/10 text-indigo-500 rounded-lg dark:bg-indigo-500/20">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z"></path>
                            </svg>
                        </span>
                        Early Warning System (EWS) Dashboard
                    </h2>
                    <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
                        Corporate Fraud Risk Detection using Weak Labeling & Machine Learning Explainability
                    </p>
                </div>
                
                <div class="flex items-center gap-2">
                    <span class="text-xs px-2.5 py-1 rounded-full font-semibold bg-emerald-500/10 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400 flex items-center gap-1">
                        <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                        Data Pipeline Synced
                    </span>
                </div>
            </div>
        </template>

        <div class="py-6">
            <div class="mx-auto max-w-7xl sm:px-6 lg:px-8 space-y-6">
                
                <!-- 1. STATS OVERVIEW GRID -->
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    
                    <!-- Stats Card 1: Total Dataset -->
                    <div class="bg-white dark:bg-slate-800 rounded-2xl p-5 border border-slate-100 dark:border-slate-700/50 shadow-sm relative overflow-hidden transition hover:-translate-y-1 hover:shadow-md duration-300">
                        <div class="absolute -right-6 -bottom-6 text-slate-100 dark:text-slate-700/30 opacity-50">
                            <svg class="w-28 h-28" fill="currentColor" viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2M9 17H7v-7h2zm4 0h-2V7h2zm4 0h-2v-4h2z"/></svg>
                        </div>
                        <div class="flex items-start justify-between">
                            <div>
                                <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Coverage</p>
                                <h3 class="text-3xl font-extrabold text-slate-800 dark:text-slate-100 mt-2">
                                    {{ stats.total_companies }}
                                </h3>
                                <p class="text-xs text-slate-500 mt-1 font-medium">
                                    Companies across {{ stats.total_records }} annual records
                                </p>
                            </div>
                            <div class="p-3 bg-indigo-50 dark:bg-indigo-500/10 rounded-xl text-indigo-500">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
                            </div>
                        </div>
                    </div>

                    <!-- Stats Card 2: Average Risk Score -->
                    <div class="bg-white dark:bg-slate-800 rounded-2xl p-5 border border-slate-100 dark:border-slate-700/50 shadow-sm relative overflow-hidden transition hover:-translate-y-1 hover:shadow-md duration-300">
                        <div class="flex items-start justify-between">
                            <div>
                                <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Avg Combined Score</p>
                                <div class="flex items-baseline gap-2 mt-2">
                                    <h3 class="text-3xl font-extrabold text-slate-800 dark:text-slate-100">
                                        {{ stats.avg_combined_score }}%
                                    </h3>
                                </div>
                                <div class="flex gap-2 mt-2 text-[10px] text-slate-400 font-medium">
                                    <span class="px-1.5 py-0.5 bg-sky-500/10 text-sky-600 rounded">Fin: {{ stats.avg_financial_risk }}%</span>
                                    <span class="px-1.5 py-0.5 bg-fuchsia-500/10 text-fuchsia-600 rounded">Narr: {{ stats.avg_narrative_risk }}%</span>
                                </div>
                            </div>
                            <!-- Circular Progress -->
                            <div class="relative flex items-center justify-center">
                                <svg class="w-16 h-16 transform -rotate-90">
                                    <circle cx="32" cy="32" r="26" stroke-width="5" stroke="currentColor" class="text-slate-100 dark:text-slate-700" fill="transparent" />
                                    <circle cx="32" cy="32" r="26" stroke-width="5" stroke="currentColor" class="text-indigo-500" fill="transparent"
                                        :stroke-dasharray="calculateCircumference(26)"
                                        :stroke-dashoffset="calculateStrokeOffset(stats.avg_combined_score, 26)" />
                                </svg>
                                <span class="absolute text-[10px] font-bold text-slate-700 dark:text-slate-200">EWS</span>
                            </div>
                        </div>
                    </div>

                    <!-- Stats Card 3: High Risk Cases -->
                    <div class="bg-white dark:bg-slate-800 rounded-2xl p-5 border border-slate-100 dark:border-slate-700/50 shadow-sm relative overflow-hidden transition hover:-translate-y-1 hover:shadow-md duration-300">
                        <div class="absolute -right-6 -bottom-6 text-rose-500/5 dark:text-rose-500/10">
                            <svg class="w-28 h-28" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>
                        </div>
                        <div class="flex items-start justify-between">
                            <div>
                                <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider text-rose-500 dark:text-rose-400">High Risk Status</p>
                                <h3 class="text-3xl font-extrabold text-rose-600 dark:text-rose-400 mt-2">
                                    {{ stats.high_risk_count }}
                                </h3>
                                <p class="text-xs text-slate-500 mt-1 font-medium">
                                    Flagged as High Risk in combined score
                                </p>
                            </div>
                            <div class="p-3 bg-rose-50 dark:bg-rose-500/10 rounded-xl text-rose-500">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                            </div>
                        </div>
                    </div>

                    <!-- Stats Card 4: Weak Label Flags -->
                    <div class="bg-white dark:bg-slate-800 rounded-2xl p-5 border border-slate-100 dark:border-slate-700/50 shadow-sm relative overflow-hidden transition hover:-translate-y-1 hover:shadow-md duration-300">
                        <div class="flex items-start justify-between">
                            <div>
                                <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider text-amber-500">Weak Label Warnings</p>
                                <div class="grid grid-cols-2 gap-4 mt-2">
                                    <div>
                                        <span class="text-[10px] font-semibold text-slate-400">Threshold 3</span>
                                        <p class="text-xl font-bold text-amber-600 dark:text-amber-400">{{ stats.weak_t3_count }}</p>
                                    </div>
                                    <div class="border-l border-slate-100 dark:border-slate-700 pl-3">
                                        <span class="text-[10px] font-semibold text-slate-400">Threshold 2</span>
                                        <p class="text-xl font-bold text-amber-600 dark:text-amber-400">{{ stats.weak_t2_count }}</p>
                                    </div>
                                </div>
                                <p class="text-[10px] text-slate-500 mt-2 font-medium">
                                    Rule-based multi-metric flags
                                </p>
                            </div>
                            <div class="p-3 bg-amber-50 dark:bg-amber-500/10 rounded-xl text-amber-500">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 2. ANALYTICS & CHARTS PANEL -->
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    
                    <!-- Widget: Risk Classification -->
                    <div class="bg-white dark:bg-slate-800 rounded-2xl p-5 border border-slate-100 dark:border-slate-700/50 shadow-sm flex flex-col justify-between">
                        <div>
                            <h4 class="text-sm font-bold text-slate-800 dark:text-slate-200">Risk Classification Distribution</h4>
                            <p class="text-[11px] text-slate-400 mt-0.5">Distribution based on combined fraud score thresholds</p>
                            
                            <div class="flex items-center justify-center py-6">
                                <!-- Pure SVG Pie Chart representation of Distribution -->
                                <svg class="w-32 h-32" viewBox="0 0 36 36">
                                    <!-- Gray BG Circle -->
                                    <circle cx="18" cy="18" r="15.915" fill="none" stroke="#f1f5f9" stroke-width="3" />
                                    
                                    <!-- Low segment (Green) -->
                                    <circle cx="18" cy="18" r="15.915" fill="none" stroke="#10b981" stroke-width="3.5"
                                        :stroke-dasharray="`${(charts.riskDistribution.Low / stats.total_records) * 100} ${100 - (charts.riskDistribution.Low / stats.total_records) * 100}`"
                                        stroke-dashoffset="25" />
                                    
                                    <!-- Medium segment (Orange) -->
                                    <circle cx="18" cy="18" r="15.915" fill="none" stroke="#f59e0b" stroke-width="3.5"
                                        :stroke-dasharray="`${(charts.riskDistribution.Medium / stats.total_records) * 100} ${100 - (charts.riskDistribution.Medium / stats.total_records) * 100}`"
                                        :stroke-dashoffset="100 - (charts.riskDistribution.Low / stats.total_records) * 100 + 25" />

                                    <!-- High segment (Red) -->
                                    <circle cx="18" cy="18" r="15.915" fill="none" stroke="#ef4444" stroke-width="3.5"
                                        :stroke-dasharray="`${(charts.riskDistribution.High / stats.total_records) * 100} ${100 - (charts.riskDistribution.High / stats.total_records) * 100}`"
                                        :stroke-dashoffset="100 - (charts.riskDistribution.Low / stats.total_records) * 100 - (charts.riskDistribution.Medium / stats.total_records) * 100 + 25" />
                                </svg>
                            </div>
                        </div>

                        <div class="space-y-2">
                            <div class="flex items-center justify-between text-xs">
                                <div class="flex items-center gap-2">
                                    <span class="w-3 h-3 rounded-full bg-rose-500"></span>
                                    <span class="text-slate-600 dark:text-slate-300 font-medium">High Risk (combined &gt; 60)</span>
                                </div>
                                <span class="font-bold text-slate-800 dark:text-slate-100">{{ charts.riskDistribution.High }} records ({{ round((charts.riskDistribution.High / stats.total_records) * 100, 1) }}%)</span>
                            </div>
                            <div class="flex items-center justify-between text-xs">
                                <div class="flex items-center gap-2">
                                    <span class="w-3 h-3 rounded-full bg-amber-500"></span>
                                    <span class="text-slate-600 dark:text-slate-300 font-medium">Medium Risk (35-60)</span>
                                </div>
                                <span class="font-bold text-slate-800 dark:text-slate-100">{{ charts.riskDistribution.Medium }} records ({{ round((charts.riskDistribution.Medium / stats.total_records) * 100, 1) }}%)</span>
                            </div>
                            <div class="flex items-center justify-between text-xs">
                                <div class="flex items-center gap-2">
                                    <span class="w-3 h-3 rounded-full bg-emerald-500"></span>
                                    <span class="text-slate-600 dark:text-slate-300 font-medium">Low Risk (&lt; 35)</span>
                                </div>
                                <span class="font-bold text-slate-800 dark:text-slate-100">{{ charts.riskDistribution.Low }} records ({{ round((charts.riskDistribution.Low / stats.total_records) * 100, 1) }}%)</span>
                            </div>
                        </div>
                    </div>

                    <!-- Widget: Weak Label Model Comparison -->
                    <div class="bg-white dark:bg-slate-800 rounded-2xl p-5 border border-slate-100 dark:border-slate-700/50 shadow-sm flex flex-col justify-between">
                        <div>
                            <h4 class="text-sm font-bold text-slate-800 dark:text-slate-200">Weak Labels Model Comparison</h4>
                            <p class="text-[11px] text-slate-400 mt-0.5">Model A (T3) vs Model B (T2) audit flag comparison</p>
                            
                            <div class="py-6 flex flex-col justify-center space-y-4">
                                <!-- Horizontal comparison bars -->
                                <div>
                                    <div class="flex justify-between text-xs font-semibold mb-1">
                                        <span class="text-slate-600 dark:text-slate-300">Model A (weak_label_t3 >= 3)</span>
                                        <span class="text-amber-600 dark:text-amber-400 font-bold">{{ stats.weak_t3_count }} flagged ({{ round((stats.weak_t3_count / stats.total_records) * 100, 1) }}%)</span>
                                    </div>
                                    <div class="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-3">
                                        <div class="bg-gradient-to-r from-amber-400 to-amber-500 h-3 rounded-full" :style="`width: ${(stats.weak_t3_count / stats.total_records) * 100}%`"></div>
                                    </div>
                                </div>
                                
                                <div>
                                    <div class="flex justify-between text-xs font-semibold mb-1">
                                        <span class="text-slate-600 dark:text-slate-300">Model B (weak_label_t2 >= 2)</span>
                                        <span class="text-amber-600 dark:text-amber-400 font-bold">{{ stats.weak_t2_count }} flagged ({{ round((stats.weak_t2_count / stats.total_records) * 100, 1) }}%)</span>
                                    </div>
                                    <div class="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-3">
                                        <div class="bg-gradient-to-r from-orange-400 to-orange-500 h-3 rounded-full" :style="`width: ${(stats.weak_t2_count / stats.total_records) * 100}%`"></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="p-3 bg-slate-50 dark:bg-slate-700/30 rounded-xl text-[10px] text-slate-500 leading-relaxed border border-slate-100 dark:border-slate-700/50">
                            <strong>Note:</strong> Weak labels combine 5 rules (Beneish M-Score, Isolation Forest, Narrative Risk, CFO Quality, and Revenue Growth). Model B is more sensitive and yields a higher flag rate suitable for early audits, whereas Model A is highly focused on severe risk cases.
                        </div>
                    </div>

                    <!-- Widget: Top High Risk Sectors -->
                    <div class="bg-white dark:bg-slate-800 rounded-2xl p-5 border border-slate-100 dark:border-slate-700/50 shadow-sm flex flex-col justify-between">
                        <div>
                            <h4 class="text-sm font-bold text-slate-800 dark:text-slate-200">Top High Risk Sectors</h4>
                            <p class="text-[11px] text-slate-400 mt-0.5">Sectors ordered by average combined risk score</p>
                            
                            <div class="mt-4 space-y-3">
                                <div v-for="(sector, idx) in charts.sectorAnalysis" :key="idx" class="flex flex-col gap-1">
                                    <div class="flex justify-between text-xs">
                                        <span class="font-medium text-slate-700 dark:text-slate-300 truncate max-w-[180px]">{{ sector.sektor }}</span>
                                        <span class="font-bold text-slate-900 dark:text-slate-200">{{ sector.avg_score }}% risk</span>
                                    </div>
                                    <div class="w-full bg-slate-50 dark:bg-slate-700 rounded-full h-1.5 overflow-hidden flex">
                                        <div class="bg-rose-500 h-full" :style="`width: ${sector.avg_score}%`"></div>
                                    </div>
                                    <div class="flex justify-between text-[9px] text-slate-400">
                                        <span>Total: {{ sector.total }} reports</span>
                                        <span class="text-rose-500 font-semibold">{{ sector.high_risk }} High Risk</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 3. DIRECTORY TABLE & FILTER BAR -->
                <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700/50 shadow-sm overflow-hidden">
                    
                    <!-- Search & Filter Controls -->
                    <div class="p-5 border-b border-slate-100 dark:border-slate-700/50 bg-slate-50/50 dark:bg-slate-800/20 space-y-4">
                        <div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
                            <h4 class="text-base font-bold text-slate-800 dark:text-slate-200">Company Risk Directory</h4>
                            
                            <!-- Search Bar -->
                            <div class="relative max-w-md w-full">
                                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                                    <svg class="h-4.5 w-4.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                                </div>
                                <input v-model="search" @keyup.enter="applyFilters" type="text" placeholder="Search code, name, sector..." class="block w-full pl-9 pr-3 py-1.5 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-indigo-500 focus:border-indigo-500 dark:text-slate-200 shadow-inner" />
                            </div>
                        </div>

                        <!-- Dropdown filters -->
                        <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3">
                            <!-- Year Filter -->
                            <div>
                                <label class="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Fiscal Year</label>
                                <select v-model="year" class="block w-full py-1.5 px-3 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl dark:text-slate-200">
                                    <option value="">All Years</option>
                                    <option v-for="yr in availableYears" :key="yr" :value="yr">{{ yr }}</option>
                                </select>
                            </div>

                            <!-- Risk Status Filter -->
                            <div>
                                <label class="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Combined Status</label>
                                <select v-model="status" class="block w-full py-1.5 px-3 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl dark:text-slate-200">
                                    <option value="">All Risks</option>
                                    <option value="Low">Low Risk</option>
                                    <option value="Medium">Medium Risk</option>
                                    <option value="High">High Risk</option>
                                </select>
                            </div>

                            <!-- Weak Label T3 Filter -->
                            <div>
                                <label class="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Model A (T3 >= 3)</label>
                                <select v-model="weakT3" class="block w-full py-1.5 px-3 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl dark:text-slate-200">
                                    <option value="">All</option>
                                    <option value="1">Flagged (1)</option>
                                    <option value="0">Normal (0)</option>
                                </select>
                            </div>

                            <!-- Weak Label T2 Filter -->
                            <div>
                                <label class="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Model B (T2 >= 2)</label>
                                <select v-model="weakT2" class="block w-full py-1.5 px-3 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl dark:text-slate-200">
                                    <option value="">All</option>
                                    <option value="1">Flagged (1)</option>
                                    <option value="0">Normal (0)</option>
                                </select>
                            </div>

                            <!-- Action buttons -->
                            <div class="col-span-2 sm:col-span-4 lg:col-span-1 flex items-end gap-2">
                                <button @click="applyFilters" class="flex-1 py-1.5 px-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow transition duration-200">
                                    Apply
                                </button>
                                <button @click="resetFilters" class="py-1.5 px-3 bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-xl text-xs font-semibold transition duration-200">
                                    Reset
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Directory Table -->
                    <div class="overflow-x-auto">
                        <table class="min-w-full divide-y divide-slate-100 dark:divide-slate-700/50">
                            <thead class="bg-slate-50 dark:bg-slate-800/40">
                                <tr>
                                    <th scope="col" class="px-6 py-3.5 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">Company</th>
                                    <th scope="col" class="px-4 py-3.5 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">Year</th>
                                    <th scope="col" class="px-6 py-3.5 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">Sector</th>
                                    <th scope="col" class="px-4 py-3.5 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">Beneish M-Score</th>
                                    <th scope="col" class="px-4 py-3.5 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">Financial Risk</th>
                                    <th scope="col" class="px-4 py-3.5 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">Narrative Risk</th>
                                    <th scope="col" class="px-4 py-3.5 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">Combined Risk</th>
                                    <th scope="col" class="px-4 py-3.5 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">Model A (T3)</th>
                                    <th scope="col" class="px-4 py-3.5 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">Model B (T2)</th>
                                    <th scope="col" class="relative px-6 py-3.5">
                                        <span class="sr-only">Actions</span>
                                    </th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-100 dark:divide-slate-700/50 bg-white dark:bg-slate-800">
                                <tr v-for="record in records.data" :key="record.id" class="hover:bg-slate-50/50 dark:hover:bg-slate-700/30 transition duration-150">
                                    <!-- Company Details -->
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        <div class="flex items-center gap-3">
                                            <span class="w-10 h-10 rounded-xl bg-indigo-50/80 dark:bg-indigo-500/10 text-indigo-500 font-extrabold flex items-center justify-center text-sm border border-indigo-100/50 dark:border-indigo-500/20 shadow-sm">
                                                {{ record.kode }}
                                            </span>
                                            <div>
                                                <div class="text-sm font-bold text-slate-800 dark:text-slate-100">{{ record.nama_perusahaan }}</div>
                                                <div class="text-[10px] text-slate-400 mt-0.5">Code: {{ record.kode }}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <!-- Year -->
                                    <td class="px-4 py-4 whitespace-nowrap text-center text-sm font-bold text-slate-700 dark:text-slate-300">
                                        {{ record.tahun }}
                                    </td>
                                    <!-- Sector -->
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">
                                        {{ record.sektor || '-' }}
                                    </td>
                                    <!-- Beneish M-Score -->
                                    <td class="px-4 py-4 whitespace-nowrap text-center">
                                        <span :class="`text-xs font-mono font-semibold px-2 py-0.5 rounded-full ${record.m_score > -2.22 ? 'bg-rose-100 text-rose-700 dark:bg-rose-900/35 dark:text-rose-400' : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300'}`">
                                            {{ record.m_score !== null ? round(record.m_score, 2) : '-' }}
                                        </span>
                                    </td>
                                    <!-- Financial Risk Score -->
                                    <td class="px-4 py-4 whitespace-nowrap text-center text-sm font-medium text-slate-700 dark:text-slate-300">
                                        {{ record.financial_risk_score !== null ? round(record.financial_risk_score, 1) + '%' : '-' }}
                                    </td>
                                    <!-- Narrative Risk Score -->
                                    <td class="px-4 py-4 whitespace-nowrap text-center text-sm font-medium text-slate-700 dark:text-slate-300">
                                        {{ record.narrative_risk_score !== null ? round(record.narrative_risk_score, 1) + '%' : '-' }}
                                    </td>
                                    <!-- Combined Risk Score & Badge -->
                                    <td class="px-4 py-4 whitespace-nowrap text-center">
                                        <div class="flex flex-col items-center gap-1">
                                            <span class="text-sm font-black text-slate-800 dark:text-slate-100">
                                                {{ record.combined_fraud_score !== null ? round(record.combined_fraud_score, 1) + '%' : '-' }}
                                            </span>
                                            <!-- Combined Badge -->
                                            <span v-if="record.combined_fraud_status === 'High'" class="text-[9px] px-2 py-0.5 rounded-full font-bold bg-rose-500/10 text-rose-600 dark:bg-rose-500/20 dark:text-rose-400 uppercase tracking-wider">High</span>
                                            <span v-else-if="record.combined_fraud_status === 'Medium'" class="text-[9px] px-2 py-0.5 rounded-full font-bold bg-amber-500/10 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400 uppercase tracking-wider">Medium</span>
                                            <span v-else class="text-[9px] px-2 py-0.5 rounded-full font-bold bg-emerald-500/10 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400 uppercase tracking-wider">Low</span>
                                        </div>
                                    </td>
                                    <!-- Weak Label T3 (Model A) -->
                                    <td class="px-4 py-4 whitespace-nowrap text-center">
                                        <span v-if="record.weak_label_t3 === 1" class="inline-flex items-center justify-center px-2 py-1 text-[10px] font-bold leading-none bg-rose-100 text-rose-700 dark:bg-rose-900/35 dark:text-rose-400 rounded-lg border border-rose-200/50 dark:border-rose-900/50">
                                            FLAGGED
                                        </span>
                                        <span v-else class="text-xs text-slate-400 dark:text-slate-600">-</span>
                                    </td>
                                    <!-- Weak Label T2 (Model B) -->
                                    <td class="px-4 py-4 whitespace-nowrap text-center">
                                        <span v-if="record.weak_label_t2 === 1" class="inline-flex items-center justify-center px-2 py-1 text-[10px] font-bold leading-none bg-amber-100 text-amber-700 dark:bg-amber-900/35 dark:text-amber-400 rounded-lg border border-amber-200/50 dark:border-amber-900/50">
                                            FLAGGED
                                        </span>
                                        <span v-else class="text-xs text-slate-400 dark:text-slate-600">-</span>
                                    </td>
                                    <!-- View Action -->
                                    <td class="px-6 py-4 whitespace-nowrap text-right text-xs font-semibold">
                                        <Link :href="route('ews.show', record.id)" class="inline-flex items-center gap-1 py-1.5 px-3 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-indigo-600 dark:text-indigo-400 rounded-lg transition duration-150">
                                            View Audit
                                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                                        </Link>
                                    </td>
                                </tr>
                                <tr v-if="records.data.length === 0">
                                    <td colspan="10" class="px-6 py-10 text-center text-slate-400 text-sm font-semibold">
                                        No companies found matching the specified filters.
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Pagination -->
                    <div class="px-6 py-4 bg-slate-50 dark:bg-slate-800/40 border-t border-slate-100 dark:border-slate-700/50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
                        <div class="text-slate-500 font-medium">
                            Showing {{ records.from || 0 }} to {{ records.to || 0 }} of {{ records.total }} records
                        </div>
                        <div class="flex items-center gap-1.5">
                            <span v-for="(link, idx) in records.links" :key="idx">
                                <Link 
                                    v-if="link.url"
                                    :href="link.url"
                                    v-html="link.label"
                                    :class="`px-3 py-1.5 rounded-lg border font-semibold transition duration-150 ${link.active ? 'bg-indigo-600 border-indigo-600 text-white shadow' : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800'}`"
                                />
                                <span 
                                    v-else
                                    v-html="link.label"
                                    class="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-400 dark:border-slate-700 dark:text-slate-600 cursor-not-allowed font-semibold"
                                />
                            </span>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </AuthenticatedLayout>
</template>

<script>
// Non-setup helper functions
export default {
    methods: {
        round(value, decimals = 2) {
            if (value === null || value === undefined) return '';
            return Number(value).toFixed(decimals);
        }
    }
}
</script>
