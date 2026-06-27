<script setup>
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import { Head, Link } from '@inertiajs/vue3';
import { ref } from 'vue';

const props = defineProps({
    record: Object,
    history: Array,
    rulesStatus: Array,
    mlApiAvailable: Boolean,
    aiCommentary: String,
    
    // Model B
    mlModelBProbability: Number,
    mlModelBPrediction: Number,
    featuresImpactB: Array,

    // Model A
    mlModelAProbability: Number,
    mlModelAPrediction: Number,
    featuresImpactA: Array,
});

const activeTab = ref('financial');
const activeShapModel = ref('B');

// Helper to determine badge colors
const getRiskStatusClass = (status) => {
    switch (status) {
        case 'High':
            return 'bg-rose-500/10 text-rose-600 border-rose-200 dark:bg-rose-900/30 dark:text-rose-400 dark:border-rose-900/50';
        case 'Medium':
            return 'bg-amber-500/10 text-amber-600 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-900/50';
        default:
            return 'bg-emerald-500/10 text-emerald-600 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-900/50';
    }
};

const formatNumber = (num) => {
    if (num === null || num === undefined || isNaN(num)) return '-';
    return new Intl.NumberFormat('id-ID').format(Math.round(num));
};

const formatDouble = (num, decimals = 4) => {
    if (num === null || num === undefined || isNaN(num)) return '-';
    return Number(num).toFixed(decimals);
};
</script>

<template>
    <Head :title="`Audit ${record.kode} (${record.tahun})`" />

    <AuthenticatedLayout>
        <template #header>
            <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div class="flex items-center gap-3">
                    <Link :href="route('dashboard')" class="p-2 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-xl transition dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-300">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
                    </Link>
                    <div>
                        <div class="flex items-center gap-2">
                            <h2 class="text-2xl font-bold leading-tight text-slate-800 dark:text-slate-100">
                                {{ record.nama_perusahaan }}
                            </h2>
                            <span class="text-sm font-extrabold px-2.5 py-0.5 rounded-lg bg-indigo-50/80 dark:bg-indigo-500/10 text-indigo-500 border border-indigo-100 dark:border-indigo-500/20 shadow-sm">
                                {{ record.kode }}
                            </span>
                        </div>
                        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
                            Sektor: {{ record.sektor }} &bull; Fiscal Year: {{ record.tahun }}
                        </p>
                    </div>
                </div>

                <!-- History Year Selector tabs -->
                <div class="flex items-center gap-1.5 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl border border-slate-200/50 dark:border-slate-700/50">
                    <span class="text-[10px] font-bold text-slate-400 px-2 uppercase">Years:</span>
                    <Link 
                        v-for="h in history" 
                        :key="h.id"
                        :href="route('ews.show', h.id)"
                        :class="`px-3 py-1 rounded-lg text-xs font-bold transition duration-200 ${h.tahun === record.tahun ? 'bg-white text-indigo-600 shadow dark:bg-slate-900 dark:text-slate-100' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}`"
                    >
                        {{ h.tahun }}
                    </Link>
                </div>
            </div>
        </template>

        <div class="py-6">
            <div class="mx-auto max-w-7xl sm:px-6 lg:px-8 space-y-6">

                <!-- 1. RISK SCORE SUMMARY BANNER -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    
                    <!-- Combined Score Card -->
                    <div class="bg-white dark:bg-slate-800 rounded-2xl p-5 border border-slate-100 dark:border-slate-700/50 shadow-sm flex flex-col justify-between md:col-span-2">
                        <div>
                            <div class="flex items-center justify-between">
                                <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Combined EWS Fraud Score</span>
                                <span :class="`text-xs font-bold px-3 py-0.5 rounded-full border ${getRiskStatusClass(record.combined_fraud_status)}`">
                                    {{ record.combined_fraud_status }} Risk
                                </span>
                            </div>
                            <div class="flex items-baseline gap-3 mt-4">
                                <h1 class="text-5xl font-black text-slate-800 dark:text-slate-50">
                                    {{ formatDouble(record.combined_fraud_score, 1) }}%
                                </h1>
                                <p class="text-xs text-slate-500 leading-relaxed max-w-[240px]">
                                    Calculated as 70% Financial Risk score and 30% Narrative Text Risk score.
                                </p>
                            </div>
                        </div>
                        
                        <!-- Combined Score Visual slider bar -->
                        <div class="mt-4">
                            <div class="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-3 overflow-hidden relative">
                                <div class="absolute inset-y-0 left-0 bg-emerald-500" style="width: 35%"></div>
                                <div class="absolute inset-y-0 left-[35%] bg-amber-500" style="width: 25%"></div>
                                <div class="absolute inset-y-0 left-[60%] bg-rose-500" style="width: 40%"></div>
                                <div class="absolute top-0 bottom-0 w-1 bg-slate-900 dark:bg-white ring-2 ring-indigo-500 h-full rounded transition-all duration-500" :style="`left: ${record.combined_fraud_score}%`"></div>
                            </div>
                            <div class="flex justify-between text-[9px] text-slate-400 mt-1.5 font-bold">
                                <span>LOW (0-35)</span>
                                <span>MEDIUM (35-60)</span>
                                <span>HIGH (60-100)</span>
                            </div>
                        </div>

                        <!-- FastAPI XGBoost Model Live Integration Status -->
                        <div v-if="mlApiAvailable" class="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div class="p-3 bg-indigo-50/50 dark:bg-indigo-900/10 rounded-xl border border-indigo-100 dark:border-indigo-900/30 flex items-center justify-between shadow-sm">
                                <div>
                                    <span class="text-[9px] font-bold text-slate-400 block uppercase">Model B (t2 >= 2)</span>
                                    <span class="text-xs font-bold text-slate-800 dark:text-slate-100">
                                        {{ mlModelBPrediction === 1 ? '🔴 High Risk Outlier' : '🟢 Low Risk Normal' }}
                                    </span>
                                </div>
                                <div class="text-right">
                                    <span class="text-[9px] font-bold text-slate-400 block uppercase">Probability</span>
                                    <span class="text-xs font-extrabold text-indigo-600 dark:text-indigo-400">
                                        {{ mlModelBProbability }}%
                                    </span>
                                </div>
                            </div>

                            <div class="p-3 bg-fuchsia-50/50 dark:bg-fuchsia-900/10 rounded-xl border border-fuchsia-100 dark:border-fuchsia-900/30 flex items-center justify-between shadow-sm">
                                <div>
                                    <span class="text-[9px] font-bold text-slate-400 block uppercase">Model A (t3 >= 3)</span>
                                    <span class="text-xs font-bold text-slate-800 dark:text-slate-100">
                                        {{ mlModelAPrediction === 1 ? '🔴 High Risk Outlier' : '🟢 Low Risk Normal' }}
                                    </span>
                                </div>
                                <div class="text-right">
                                    <span class="text-[9px] font-bold text-slate-400 block uppercase">Probability</span>
                                    <span class="text-xs font-extrabold text-fuchsia-600 dark:text-fuchsia-400">
                                        {{ mlModelAProbability }}%
                                    </span>
                                </div>
                            </div>
                        </div>
                        <div v-else class="mt-4 p-3 bg-slate-50 dark:bg-slate-850 rounded-xl border border-slate-200/50 dark:border-slate-700/50 flex items-center justify-between">
                            <div>
                                <span class="text-[9px] font-bold text-slate-400 block uppercase">XGBoost ML Models A & B prediction</span>
                                <span class="text-xs text-slate-500 font-bold">
                                    FastAPI Prediction Server Offline (Using DB Fallbacks)
                                </span>
                            </div>
                            <span class="text-[9px] font-bold px-2 py-0.5 rounded bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300">
                                DB Fallback
                            </span>
                        </div>
                    </div>

                    <!-- Financial score weight -->
                    <div class="bg-white dark:bg-slate-800 rounded-2xl p-5 border border-slate-100 dark:border-slate-700/50 shadow-sm relative overflow-hidden">
                        <span class="text-xs font-bold text-slate-400 uppercase tracking-wider block">Financial Risk Score</span>
                        <div class="mt-3 flex items-baseline gap-2">
                            <h2 class="text-3xl font-extrabold text-slate-800 dark:text-slate-100">
                                {{ formatDouble(record.financial_risk_score, 1) }}%
                            </h2>
                            <span class="text-[10px] text-slate-400">70% Weight</span>
                        </div>
                        <p class="text-[10px] text-slate-500 mt-2 leading-relaxed">
                            Aggregated from Beneish M-Score probability and Isolation Forest anomaly labels.
                        </p>
                    </div>

                    <!-- Narrative score weight -->
                    <div class="bg-white dark:bg-slate-800 rounded-2xl p-5 border border-slate-100 dark:border-slate-700/50 shadow-sm relative overflow-hidden">
                        <span class="text-xs font-bold text-slate-400 uppercase tracking-wider block">Narrative Risk Score</span>
                        <div class="mt-3 flex items-baseline gap-2">
                            <h2 class="text-3xl font-extrabold text-slate-800 dark:text-slate-100">
                                {{ formatDouble(record.narrative_risk_score, 1) }}%
                            </h2>
                            <span class="text-[10px] text-slate-400">30% Weight</span>
                        </div>
                        <p class="text-[10px] text-slate-500 mt-2 leading-relaxed">
                            Composed of Sentiment (40%), Risk Words (30%), and Readability (30%) text index.
                        </p>
                    </div>
                </div>

                <!-- 2. AUDIT TABS & DETAILS PANELS -->
                <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700/50 shadow-sm overflow-hidden">
                    
                    <!-- Tab buttons -->
                    <div class="flex border-b border-slate-100 dark:border-slate-700/50 bg-slate-50/50 dark:bg-slate-900/20 p-1">
                        <button 
                            @click="activeTab = 'financial'"
                            :class="`flex-1 py-3 text-center text-xs font-bold rounded-xl transition duration-200 flex items-center justify-center gap-1.5 ${activeTab === 'financial' ? 'bg-white text-indigo-600 shadow dark:bg-slate-900 dark:text-indigo-400' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}`"
                        >
                            <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                            Financial statement & Beneish Indices
                        </button>
                        <button 
                            @click="activeTab = 'narrative'"
                            :class="`flex-1 py-3 text-center text-xs font-bold rounded-xl transition duration-200 flex items-center justify-center gap-1.5 ${activeTab === 'narrative' ? 'bg-white text-indigo-600 shadow dark:bg-slate-900 dark:text-indigo-400' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}`"
                        >
                            <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                            Narrative report sentiment
                        </button>
                        <button 
                            @click="activeTab = 'audit'"
                            :class="`flex-1 py-3 text-center text-xs font-bold rounded-xl transition duration-200 flex items-center justify-center gap-1.5 ${activeTab === 'audit' ? 'bg-white text-indigo-600 shadow dark:bg-slate-900 dark:text-indigo-400' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}`"
                        >
                            <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"></path></svg>
                            Weak label audit & SHAP Local
                        </button>
                        <button 
                            @click="activeTab = 'commentary'"
                            :class="`flex-1 py-3 text-center text-xs font-bold rounded-xl transition duration-200 flex items-center justify-center gap-1.5 ${activeTab === 'commentary' ? 'bg-white text-indigo-600 shadow dark:bg-slate-900 dark:text-indigo-400' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}`"
                        >
                            <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
                            AI Commentary (Gemini LLM)
                        </button>
                        <button 
                            @click="activeTab = 'export'"
                            :class="`flex-1 py-3 text-center text-xs font-bold rounded-xl transition duration-200 flex items-center justify-center gap-1.5 ${activeTab === 'export' ? 'bg-white text-indigo-600 shadow dark:bg-slate-900 dark:text-indigo-400' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}`"
                        >
                            <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                            Export Report
                        </button>
                    </div>

                    <!-- Panel 1: Financial & Beneish -->
                    <div v-if="activeTab === 'financial'" class="p-6 space-y-6">
                        
                        <!-- Top Beneish Overview -->
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                            
                            <div class="md:col-span-2 space-y-4">
                                <h4 class="text-sm font-bold text-slate-800 dark:text-slate-200">Beneish M-Score Analysis</h4>
                                <p class="text-xs text-slate-500 leading-relaxed">
                                    The Beneish M-Score is a mathematical model that uses 8 financial ratios to identify whether a company has manipulated its earnings. Ratios significantly exceeding 1.0 or indicating abnormal asset, expense, or accrual growth represent red flags.
                                </p>
                                
                                <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
                                    <!-- DSRI -->
                                    <div class="p-3 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700/30 rounded-xl">
                                        <span class="text-[9px] font-bold text-slate-400 block uppercase">DSRI (Receivables)</span>
                                        <span :class="`text-base font-mono font-bold mt-1 block ${record.dsri > 1.2 ? 'text-rose-500' : 'text-slate-850 dark:text-slate-100'}`">
                                            {{ formatDouble(record.dsri) }}
                                        </span>
                                    </div>
                                    
                                    <!-- GMI -->
                                    <div class="p-3 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700/30 rounded-xl">
                                        <span class="text-[9px] font-bold text-slate-400 block uppercase">GMI (Gross Margin)</span>
                                        <span :class="`text-base font-mono font-bold mt-1 block ${record.gmi > 1.1 ? 'text-rose-500' : 'text-slate-800 dark:text-slate-100'}`">
                                            {{ formatDouble(record.gmi) }}
                                        </span>
                                    </div>
                                    
                                    <!-- AQI -->
                                    <div class="p-3 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700/30 rounded-xl">
                                        <span class="text-[9px] font-bold text-slate-400 block uppercase">AQI (Asset Quality)</span>
                                        <span :class="`text-base font-mono font-bold mt-1 block ${record.aqi > 1.1 ? 'text-rose-500' : 'text-slate-800 dark:text-slate-100'}`">
                                            {{ formatDouble(record.aqi) }}
                                        </span>
                                    </div>
                                    
                                    <!-- SGI -->
                                    <div class="p-3 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700/30 rounded-xl">
                                        <span class="text-[9px] font-bold text-slate-400 block uppercase">SGI (Sales Growth)</span>
                                        <span :class="`text-base font-mono font-bold mt-1 block ${record.sgi > 1.15 ? 'text-rose-500' : 'text-slate-800 dark:text-slate-100'}`">
                                            {{ formatDouble(record.sgi) }}
                                        </span>
                                    </div>
 
                                    <!-- LVGI -->
                                    <div class="p-3 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700/30 rounded-xl">
                                        <span class="text-[9px] font-bold text-slate-400 block uppercase">LVGI (Leverage)</span>
                                        <span :class="`text-base font-mono font-bold mt-1 block ${record.lvgi > 1.05 ? 'text-rose-500' : 'text-slate-800 dark:text-slate-100'}`">
                                            {{ formatDouble(record.lvgi) }}
                                        </span>
                                    </div>
 
                                    <!-- DEPI -->
                                    <div class="p-3 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700/30 rounded-xl">
                                        <span class="text-[9px] font-bold text-slate-400 block uppercase">DEPI (Depreciation)</span>
                                        <span :class="`text-base font-mono font-bold mt-1 block ${record.depi > 1.0 ? 'text-rose-500' : 'text-slate-800 dark:text-slate-100'}`">
                                            {{ formatDouble(record.depi) }}
                                        </span>
                                    </div>
 
                                    <!-- SGAI -->
                                    <div class="p-3 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700/30 rounded-xl">
                                        <span class="text-[9px] font-bold text-slate-400 block uppercase">SGAI (Sales Admin)</span>
                                        <span :class="`text-base font-mono font-bold mt-1 block ${record.sgai > 1.0 ? 'text-rose-500' : 'text-slate-800 dark:text-slate-100'}`">
                                            {{ formatDouble(record.sgai) }}
                                        </span>
                                    </div>
 
                                    <!-- TATA -->
                                    <div class="p-3 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700/30 rounded-xl">
                                        <span class="text-[9px] font-bold text-slate-400 block uppercase">TATA (Accruals)</span>
                                        <span :class="`text-base font-mono font-bold mt-1 block ${Math.abs(record.tata) > 0.05 ? 'text-rose-500' : 'text-slate-800 dark:text-slate-100'}`">
                                            {{ formatDouble(record.tata) }}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- M-Score calculation summary card -->
                            <div class="bg-slate-50 dark:bg-slate-900 p-5 rounded-2xl border border-slate-100 dark:border-slate-700/30 flex flex-col justify-between">
                                <div>
                                    <span class="text-xs font-bold text-slate-400 uppercase tracking-wider block">Beneish M-Score Value</span>
                                    <div class="mt-2 flex items-baseline gap-2">
                                        <h2 :class="`text-4xl font-extrabold ${record.m_score > -2.22 ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400'}`">
                                            {{ formatDouble(record.m_score, 2) }}
                                        </h2>
                                    </div>
                                    <div class="mt-2">
                                        <span v-if="record.m_score > -2.22" class="inline-flex items-center gap-1 text-[10px] font-bold text-rose-600 bg-rose-500/10 px-2 py-0.5 rounded">
                                            High Risk (manipulator likelihood)
                                        </span>
                                        <span v-else class="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-600 bg-emerald-500/10 px-2 py-0.5 rounded">
                                            Low Risk (non-manipulator)
                                        </span>
                                    </div>
                                </div>
                                <p class="text-[10px] text-slate-500 mt-4 leading-relaxed border-t border-slate-200 dark:border-slate-700/50 pt-3">
                                    The standard Beneish threshold is <strong>-2.22</strong>. Scores higher than -2.22 (e.g. -1.5) indicate an elevated probability of accounting irregularities.
                                </p>
                            </div>
                        </div>

                        <!-- Raw financial statements values table -->
                        <div class="pt-4 border-t border-slate-100 dark:border-slate-700/50">
                            <h4 class="text-sm font-bold text-slate-800 dark:text-slate-200 mb-3">Extracted Financial Ratios inputs (IDR)</h4>
                            <div class="overflow-x-auto rounded-xl border border-slate-100 dark:border-slate-700/50">
                                <table class="min-w-full divide-y divide-slate-100 dark:divide-slate-700/50 text-xs">
                                    <thead class="bg-slate-50 dark:bg-slate-800/40">
                                        <tr>
                                            <th class="px-4 py-2.5 text-left font-bold text-slate-400">Financial Metrics</th>
                                            <th class="px-4 py-2.5 text-right font-bold text-slate-400">Current Year ({{ record.tahun }})</th>
                                            <th class="px-4 py-2.5 text-right font-bold text-slate-400">Previous Year ({{ record.tahun - 1 }})</th>
                                            <th class="px-4 py-2.5 text-center font-bold text-slate-400">Trend / Note</th>
                                        </tr>
                                    </thead>
                                    <tbody class="divide-y divide-slate-100 dark:divide-slate-700/50">
                                        <tr>
                                            <td class="px-4 py-2.5 font-medium text-slate-700 dark:text-slate-300">Total Assets</td>
                                            <td class="px-4 py-2.5 text-right font-mono font-bold text-slate-800 dark:text-slate-200">{{ formatNumber(record.total_assets) }}</td>
                                            <td class="px-4 py-2.5 text-right font-mono text-slate-400">{{ formatNumber(record.total_assets_lag) }}</td>
                                            <td class="px-4 py-2.5 text-center">
                                                <span :class="`font-bold ${record.asset_growth > 0 ? 'text-emerald-500' : 'text-slate-400'}`">
                                                    {{ record.asset_growth !== null ? formatDouble(record.asset_growth * 100, 1) + '%' : '-' }}
                                                </span>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td class="px-4 py-2.5 font-medium text-slate-700 dark:text-slate-300">Revenue / Sales</td>
                                            <td class="px-4 py-2.5 text-right font-mono font-bold text-slate-800 dark:text-slate-200">{{ formatNumber(record.revenue) }}</td>
                                            <td class="px-4 py-2.5 text-right font-mono text-slate-400">{{ formatNumber(record.revenue_lag) }}</td>
                                            <td class="px-4 py-2.5 text-center">
                                                <span :class="`font-bold ${record.revenue_growth > 0.3 ? 'text-rose-500' : (record.revenue_growth > 0 ? 'text-emerald-500' : 'text-slate-400')}`">
                                                    {{ record.revenue_growth !== null ? formatDouble(record.revenue_growth * 100, 1) + '%' : '-' }}
                                                </span>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td class="px-4 py-2.5 font-medium text-slate-700 dark:text-slate-300">Receivables</td>
                                            <td class="px-4 py-2.5 text-right font-mono font-bold text-slate-800 dark:text-slate-200">{{ formatNumber(record.receivables) }}</td>
                                            <td class="px-4 py-2.5 text-right font-mono text-slate-400">{{ formatNumber(record.receivables_lag) }}</td>
                                            <td class="px-4 py-2.5 text-center text-slate-400 font-medium">
                                                DSRI: {{ formatDouble(record.dsri) }}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td class="px-4 py-2.5 font-medium text-slate-700 dark:text-slate-300">Net Income</td>
                                            <td class="px-4 py-2.5 text-right font-mono font-bold text-slate-800 dark:text-slate-200">{{ formatNumber(record.net_income) }}</td>
                                            <td class="px-4 py-2.5 text-right font-mono text-slate-400">{{ formatNumber(record.net_income_lag) }}</td>
                                            <td class="px-4 py-2.5 text-center">
                                                <span :class="`font-bold ${record.net_income > record.net_income_lag ? 'text-emerald-500' : 'text-rose-500'}`">
                                                    {{ record.net_income_lag ? formatDouble(((record.net_income - record.net_income_lag) / Math.abs(record.net_income_lag)) * 100, 1) + '%' : '-' }}
                                                </span>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td class="px-4 py-2.5 font-medium text-slate-700 dark:text-slate-300">Cash Flow from Operations (CFO)</td>
                                            <td class="px-4 py-2.5 text-right font-mono font-bold text-slate-800 dark:text-slate-200">{{ formatNumber(record.cfo) }}</td>
                                            <td class="px-4 py-2.5 text-right font-mono text-slate-400">-</td>
                                            <td class="px-4 py-2.5 text-center">
                                                <span :class="`font-bold px-2 py-0.5 rounded text-[10px] ${record.cfo_quality_flag === 'Normal' ? 'bg-emerald-500/10 text-emerald-600' : 'bg-rose-500/10 text-rose-600'}`">
                                                    {{ record.cfo_quality_flag || 'Normal' }}
                                                </span>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>

                    </div>

                    <!-- Panel 2: Narrative Report Sentiment -->
                    <div v-if="activeTab === 'narrative'" class="p-6 space-y-6">
                        
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                            
                            <div class="md:col-span-2 space-y-4">
                                <h4 class="text-sm font-bold text-slate-800 dark:text-slate-200">Annual Report Narrative Features</h4>
                                <p class="text-xs text-slate-500 leading-relaxed">
                                    Text metrics are extracted from the MD&A (Management Discussion and Analysis) sections of corporate annual reports. Negative sentiments, high frequency of risk-oriented disclosures, and bad readability are indicative of potential management cover-ups of financial issues.
                                </p>
                                
                                <div class="grid grid-cols-2 gap-4">
                                    <!-- Sentiment metric -->
                                    <div class="p-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700/30 rounded-xl flex flex-col justify-between">
                                        <div>
                                            <span class="text-[10px] font-bold text-slate-400 block uppercase">Sentiment Score</span>
                                            <span class="text-2xl font-black text-slate-800 dark:text-slate-100 mt-1 block">
                                                {{ formatDouble(record.sentiment, 3) }}
                                            </span>
                                        </div>
                                        
                                        <!-- sentiment visualization bar -->
                                        <div class="mt-3">
                                            <div class="w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full relative">
                                                <div class="absolute inset-y-0 left-1/2 w-0.5 bg-slate-400"></div>
                                                <div class="absolute w-2.5 h-2.5 bg-indigo-500 rounded-full top-1/2 transform -translate-y-1/2" :style="`left: ${((record.sentiment + 1) / 2) * 100}%`"></div>
                                            </div>
                                            <div class="flex justify-between text-[8px] text-slate-400 mt-1">
                                                <span>Negative (-1)</span>
                                                <span>Positive (+1)</span>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <!-- Risk Words density -->
                                    <div class="p-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700/30 rounded-xl flex flex-col justify-between">
                                        <div>
                                            <span class="text-[10px] font-bold text-slate-400 block uppercase">Risk Words Density</span>
                                            <span class="text-2xl font-black text-slate-800 dark:text-slate-100 mt-1 block">
                                                {{ formatNumber(record.risk_words) }}
                                            </span>
                                        </div>
                                        <p class="text-[10px] text-slate-400 mt-2">
                                            Number of words indicating uncertainty, risk, litigation, or regulatory threats.
                                        </p>
                                    </div>

                                    <!-- Readability Index -->
                                    <div class="p-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700/30 rounded-xl flex flex-col justify-between">
                                        <div>
                                            <span class="text-[10px] font-bold text-slate-400 block uppercase">Readability Index</span>
                                            <span class="text-2xl font-black text-slate-800 dark:text-slate-100 mt-1 block">
                                                {{ formatDouble(record.readability, 2) }}
                                            </span>
                                        </div>
                                        <p class="text-[10px] text-slate-400 mt-2">
                                            Higher scores imply more complex, obfuscated language.
                                        </p>
                                    </div>

                                    <!-- Text length -->
                                    <div class="p-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700/30 rounded-xl flex flex-col justify-between">
                                        <div>
                                            <span class="text-[10px] font-bold text-slate-400 block uppercase">MD&A Text Length</span>
                                            <span class="text-2xl font-black text-slate-800 dark:text-slate-100 mt-1 block">
                                                {{ formatNumber(record.text_length) }} ch
                                            </span>
                                        </div>
                                        <p class="text-[10px] text-slate-400 mt-2">
                                            Total number of characters extracted from the report.
                                        </p>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Narrative formula weighting card -->
                            <div class="bg-slate-50 dark:bg-slate-900 p-5 rounded-2xl border border-slate-100 dark:border-slate-700/30 flex flex-col justify-between">
                                <div>
                                    <span class="text-xs font-bold text-slate-400 uppercase tracking-wider block">Narrative Risk Weighting</span>
                                    <div class="mt-4 space-y-3 text-xs">
                                        <div>
                                            <div class="flex justify-between font-semibold">
                                                <span>Sentiment (40%)</span>
                                                <span>{{ formatDouble(record.sentiment_scaled ?? 0, 1) }}</span>
                                            </div>
                                            <div class="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-1.5 mt-1">
                                                <div class="bg-indigo-500 h-1.5 rounded-full" :style="`width: ${record.sentiment_scaled ?? 0}%`"></div>
                                            </div>
                                        </div>
                                        <div>
                                            <div class="flex justify-between font-semibold">
                                                <span>Risk Words (30%)</span>
                                                <span>{{ formatDouble(record.risk_words_scaled ?? 0, 1) }}</span>
                                            </div>
                                            <div class="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-1.5 mt-1">
                                                <div class="bg-fuchsia-500 h-1.5 rounded-full" :style="`width: ${record.risk_words_scaled ?? 0}%`"></div>
                                            </div>
                                        </div>
                                        <div>
                                            <div class="flex justify-between font-semibold">
                                                <span>Readability (30%)</span>
                                                <span>{{ formatDouble(record.readability_scaled ?? 0, 1) }}</span>
                                            </div>
                                            <div class="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-1.5 mt-1">
                                                <div class="bg-sky-500 h-1.5 rounded-full" :style="`width: ${record.readability_scaled ?? 0}%`"></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="border-t border-slate-200 dark:border-slate-700/50 pt-3 mt-4 text-[10px] text-slate-500 leading-relaxed">
                                    The Narrative Risk Score is calculated as:<br/>
                                    <strong>40% Sentiment + 30% Risk Words + 30% Readability</strong>.
                                </div>
                            </div>
                        </div>

                    </div>

                    <!-- Panel 3: Weak Label Rules Audit & SHAP Local -->
                    <div v-if="activeTab === 'audit'" class="p-6 space-y-6">
                        
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            
                            <!-- Weak Label Rules Checklist -->
                            <div class="space-y-4">
                                <h4 class="text-sm font-bold text-slate-800 dark:text-slate-200">Rule-based Audit Checklist</h4>
                                <p class="text-xs text-slate-500 leading-relaxed">
                                    To establish a high-confidence ground truth without manual labels, the EWS uses 5 distinct financial and narrative rules to construct a weak label score.
                                </p>
                                
                                <div class="space-y-3">
                                    <div v-for="(rule, idx) in rulesStatus" :key="idx" class="p-3 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700/30 rounded-xl">
                                        <div class="flex items-start justify-between">
                                            <div class="flex-1">
                                                <span class="text-xs font-bold text-slate-800 dark:text-slate-200 block">{{ rule.name }}</span>
                                                <p class="text-[10px] text-slate-500 mt-1 leading-relaxed">{{ rule.description }}</p>
                                            </div>
                                            <span :class="`text-[9px] font-bold px-2 py-0.5 rounded-lg border ${rule.triggered ? 'bg-rose-500/10 text-rose-600 border-rose-200' : 'bg-emerald-500/10 text-emerald-600 border-emerald-200'}`">
                                                {{ rule.triggered ? 'TRIGGERED' : 'PASS' }}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                <!-- Summary of weak flags -->
                                <div class="p-4 bg-indigo-50/50 dark:bg-indigo-900/10 rounded-xl border border-indigo-100 dark:border-indigo-900/50 flex justify-between items-center text-xs">
                                    <div>
                                        <span class="text-[10px] font-bold text-slate-400 block uppercase">Weak Flags count</span>
                                        <p class="text-lg font-black text-slate-800 dark:text-slate-100 mt-0.5">
                                            {{ record.weak_score }} / 5 Rules Triggered
                                        </p>
                                    </div>
                                    <div class="flex gap-2">
                                        <div class="flex flex-col items-center">
                                            <span class="text-[8px] font-bold text-slate-400 uppercase">Model A (T3)</span>
                                            <span :class="`text-[9px] font-bold px-2 py-0.5 rounded mt-1 border ${record.weak_label_t3 === 1 ? 'bg-rose-500/10 text-rose-600 border-rose-200' : 'bg-slate-100 text-slate-500 border-slate-200'}`">
                                                {{ record.weak_label_t3 === 1 ? 'FLAGGED' : 'NORMAL' }}
                                            </span>
                                        </div>
                                        <div class="flex flex-col items-center">
                                            <span class="text-[8px] font-bold text-slate-400 uppercase">Model B (T2)</span>
                                            <span :class="`text-[9px] font-bold px-2 py-0.5 rounded mt-1 border ${record.weak_label_t2 === 1 ? 'bg-amber-500/10 text-amber-600 border-amber-200' : 'bg-slate-100 text-slate-500 border-slate-200'}`">
                                                {{ record.weak_label_t2 === 1 ? 'FLAGGED' : 'NORMAL' }}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- SHAP Local Explainability plot (waterfall mockup) -->
                            <div class="space-y-4">
                                <div class="flex items-center justify-between">
                                    <h4 class="text-sm font-bold text-slate-800 dark:text-slate-200">SHAP Local Explainability</h4>
                                    <span v-if="mlApiAvailable" class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-250 dark:bg-emerald-950/30 dark:text-emerald-450 dark:border-emerald-900/30">
                                        <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span>
                                        FastAPI Connected
                                    </span>
                                    <span v-else class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-250 dark:bg-amber-950/30 dark:text-amber-450 dark:border-amber-900/30">
                                        FastAPI Offline
                                    </span>
                                </div>
                                <p class="text-xs text-slate-500 leading-relaxed">
                                    SHAP (SHapley Additive exPlanations) values provide local explanations for the XGBoost model predictions. The plot below shows how individual features pushed the risk prediction relative to the base value.
                                </p>
                                
                                <div class="bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-750/30 rounded-xl p-5 space-y-4">
                                    <div class="flex items-center justify-between border-b border-slate-200/50 dark:border-slate-750/50 pb-2">
                                        <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Feature Impact (Waterfall)</div>
                                        <div class="flex items-center gap-1.5 p-0.5 bg-slate-200 dark:bg-slate-800 rounded-lg">
                                            <button 
                                                @click="activeShapModel = 'B'" 
                                                :class="`px-2.5 py-1 text-[9px] font-bold rounded-md transition duration-200 ${activeShapModel === 'B' ? 'bg-white text-indigo-600 shadow dark:bg-slate-900 dark:text-indigo-400' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'}`"
                                            >
                                                Model B (t2)
                                            </button>
                                            <button 
                                                @click="activeShapModel = 'A'" 
                                                :class="`px-2.5 py-1 text-[9px] font-bold rounded-md transition duration-200 ${activeShapModel === 'A' ? 'bg-white text-indigo-600 shadow dark:bg-slate-900 dark:text-indigo-400' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'}`"
                                            >
                                                Model A (t3)
                                            </button>
                                        </div>
                                    </div>
                                    
                                    <div class="space-y-3">
                                        <div v-for="(feat, idx) in (activeShapModel === 'B' ? featuresImpactB : featuresImpactA)" :key="idx" class="flex flex-col gap-1 text-xs">
                                            <div class="flex justify-between">
                                                <span class="font-medium text-slate-700 dark:text-slate-300">{{ feat.name }}</span>
                                                <span :class="`font-bold ${feat.direction === 'up' ? 'text-rose-500' : 'text-emerald-500'}`">
                                                    {{ feat.direction === 'up' ? '+' : '-' }}{{ formatDouble(feat.weight, 2) }}
                                                </span>
                                            </div>
                                            
                                            <!-- impact bar indicator -->
                                            <div class="w-full flex items-center h-4 relative">
                                                <div class="absolute inset-y-0 left-1/2 w-0.5 bg-slate-300 dark:bg-slate-600"></div>
                                                
                                                <!-- positive impact (pushes risk up) -->
                                                <div v-if="feat.direction === 'up'" 
                                                    class="absolute bg-rose-500 h-2.5 rounded-r"
                                                    :style="`left: 50%; width: ${Math.min(feat.weight * 2, 48)}%`"
                                                ></div>
                                                
                                                <!-- negative impact (pushes risk down) -->
                                                <div v-else 
                                                    class="absolute bg-emerald-500 h-2.5 rounded-l"
                                                    :style="`right: 50%; width: ${Math.min(feat.weight * 2, 48)}%`"
                                                ></div>
                                            </div>
                                            
                                            <div class="flex justify-between text-[9px] text-slate-400">
                                                <span>Value: {{ feat.value }}</span>
                                                <span>Status: {{ feat.impact }}</span>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="text-[9px] text-slate-400 mt-2 border-t border-slate-200 dark:border-slate-700/50 pt-2 text-center">
                                        &larr; Pushes Risk Down (Emerald) | Pushes Risk Up (Rose) &rarr;
                                    </div>
                                </div>
                            </div>
                        </div>

                    </div>

                    <!-- Panel 4: AI Commentary -->
                    <div v-if="activeTab === 'commentary'" class="p-6 space-y-6">
                        <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-700/50 pb-4">
                            <div>
                                <h4 class="text-base font-bold text-slate-800 dark:text-slate-100">AI Executive Commentary</h4>
                                <p class="text-xs text-slate-500 mt-1">
                                     Narasi otomatis yang dihasilkan oleh Google Gemini 1.5 Pro berdasarkan metrik kuantitatif dan analisis teks.
                                </p>
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-indigo-50 text-indigo-600 border border-indigo-100 dark:bg-indigo-950/30 dark:text-indigo-400 dark:border-indigo-900/35">
                                    Gemini 1.5 Pro
                                </span>
                            </div>
                        </div>

                        <!-- Card Commentary -->
                        <div class="relative overflow-hidden bg-gradient-to-br from-indigo-50/50 via-white to-purple-50/30 dark:from-slate-800/40 dark:via-slate-800/80 dark:to-purple-950/10 rounded-2xl border border-slate-100 dark:border-slate-700/50 p-6 shadow-sm">
                            <!-- Background glow -->
                            <div class="absolute -right-24 -top-24 w-48 h-48 rounded-full bg-indigo-500/10 blur-3xl pointer-events-none"></div>
                            
                            <div class="flex items-start gap-4">
                                <!-- AI Icon -->
                                <div class="flex-shrink-0 w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-md shadow-indigo-200 dark:shadow-none">
                                    <svg class="w-6 h-6 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path></svg>
                                </div>
                                
                                <div class="flex-1 space-y-4">
                                    <div class="text-xs text-indigo-600 dark:text-indigo-400 font-bold uppercase tracking-widest">
                                        Executive Fraud Risk Report
                                    </div>
                                    
                                    <div v-if="aiCommentary" class="prose prose-slate dark:prose-invert max-w-none text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-sans space-y-4 whitespace-pre-wrap">
                                        <div class="whitespace-pre-wrap select-all selection:bg-indigo-100 dark:selection:bg-indigo-950">{{ aiCommentary }}</div>
                                    </div>
                                    
                                    <div v-else class="p-8 text-center text-slate-500 dark:text-slate-400">
                                        <svg class="w-12 h-12 text-slate-400 dark:text-slate-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                                        <span class="text-sm font-bold block">AI Commentary Belum Dihasilkan</span>
                                        <span class="text-xs mt-1 block">Silakan periksa koneksi ke server FastAPI dan lakukan refresh untuk menghasilkan.</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Info Alert -->
                        <div class="p-4 bg-indigo-50/30 dark:bg-slate-900 border border-indigo-100/30 dark:border-slate-800 rounded-xl flex gap-3 text-xs text-slate-500 dark:text-slate-400">
                            <svg class="w-5 h-5 text-indigo-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                            <div>
                                <strong class="font-bold text-slate-700 dark:text-slate-300">Catatan Model AI:</strong>
                                Analisis ini mengintegrasikan metrik Beneish M-Score, Anomaly Score dari Isolation Forest, sentimen dari laporan tahunan (Annual Report), rasio CFO-to-Net Income, serta penjelasan SHAP kontribusi fitur dari Model A dan Model B. Hasil interpretasi ini ditujukan sebagai alat bantu pengambilan keputusan dan harus selalu diverifikasi dengan kertas kerja audit lapangan.
                            </div>
                        </div>
                    </div>

                    <!-- Panel 5: Export Report -->
                    <div v-if="activeTab === 'export'" class="p-6 space-y-6">
                        <div class="max-w-2xl mx-auto text-center py-12 space-y-6">
                            <div class="w-20 h-20 bg-rose-50 dark:bg-rose-950/20 text-rose-500 rounded-full flex items-center justify-center mx-auto border border-rose-100 dark:border-rose-900/30 shadow-sm">
                                <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                            </div>
                            <div class="space-y-2">
                                <h3 class="text-xl font-bold text-slate-800 dark:text-slate-100">Export Fraud Risk Detection Report</h3>
                                <p class="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto leading-relaxed">
                                    Download a comprehensive PDF report containing the Fraud Risk Score calculation, Beneish M-Score indices, narrative risk details, and the global SHAP feature importance visualization.
                                </p>
                            </div>
                            <div>
                                <a :href="route('ews.export', record.id)" target="_blank" class="inline-flex items-center gap-2 py-3 px-6 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-sm font-bold shadow-md transition duration-200">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                                    Download PDF Report
                                </a>
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </AuthenticatedLayout>
</template>
