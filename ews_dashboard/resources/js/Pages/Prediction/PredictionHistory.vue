<script setup>
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import { Head, Link, router } from '@inertiajs/vue3';
import { ref } from 'vue';

const props = defineProps({
    histories: Object,
    filters: Object,
});

const search = ref(props.filters.search || '');

const applySearch = () => {
    router.get(route('prediction.history'), {
        search: search.value,
    }, {
        preserveState: true,
        replace: true
    });
};

const resetSearch = () => {
    search.value = '';
    applySearch();
};
</script>

<template>
    <Head title="Prediction History" />

    <AuthenticatedLayout>
        <template #header>
            <div>
                <h2 class="text-2xl font-bold leading-tight text-slate-800 dark:text-slate-100 flex items-center gap-2">
                    <span class="p-2 bg-indigo-500/10 text-indigo-500 rounded-lg dark:bg-indigo-500/20">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </span>
                    AI Model Prediction History
                </h2>
                <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    Log audit prediksi algoritma XGBoost (Model B - t2) terhadap laporan keuangan emiten.
                </p>
            </div>
        </template>

        <div class="py-6">
            <div class="mx-auto max-w-7xl sm:px-6 lg:px-8 space-y-6">
                <!-- Directory Table & Filter Bar -->
                <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700/50 shadow-sm overflow-hidden">
                    
                    <!-- Search Controls -->
                    <div class="p-5 border-b border-slate-100 dark:border-slate-700/50 bg-slate-50/50 dark:bg-slate-850/20 flex flex-col sm:flex-row items-center justify-between gap-4">
                        <h4 class="text-base font-bold text-slate-800 dark:text-slate-200">Prediction Logs</h4>
                        
                        <div class="flex items-center gap-2 w-full sm:w-auto">
                            <!-- Search Bar -->
                            <div class="relative w-full sm:w-80">
                                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                                    <svg class="h-4.5 w-4.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                                </div>
                                <input v-model="search" @keyup.enter="applySearch" type="text" placeholder="Cari nama perusahaan atau kode..." class="block w-full pl-9 pr-3 py-1.5 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-indigo-500 focus:border-indigo-500 dark:text-slate-200 shadow-inner" />
                            </div>
                            <button @click="applySearch" class="py-1.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow transition duration-200">
                                Cari
                            </button>
                            <button @click="resetSearch" class="py-1.5 px-3 bg-slate-200 hover:bg-slate-350 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-xl text-xs font-semibold transition duration-200">
                                Reset
                            </button>
                        </div>
                    </div>

                    <!-- Directory Table -->
                    <div class="overflow-x-auto">
                        <table class="min-w-full divide-y divide-slate-100 dark:divide-slate-700/50">
                            <thead class="bg-slate-50 dark:bg-slate-800/40">
                                <tr>
                                    <th scope="col" class="px-6 py-3.5 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">Emiten / Perusahaan</th>
                                    <th scope="col" class="px-4 py-3.5 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">Tahun Buku</th>
                                    <th scope="col" class="px-4 py-3.5 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">XGBoost Probability</th>
                                    <th scope="col" class="px-4 py-3.5 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">XGBoost Prediction</th>
                                    <th scope="col" class="px-4 py-3.5 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">Risk Level</th>
                                    <th scope="col" class="px-6 py-3.5 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">Tanggal Prediksi</th>
                                    <th scope="col" class="relative px-6 py-3.5">
                                        <span class="sr-only">Aksi</span>
                                    </th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-100 dark:divide-slate-700/50 bg-white dark:bg-slate-800">
                                <tr v-for="log in histories.data" :key="log.id" class="hover:bg-slate-50/50 dark:hover:bg-slate-700/30 transition duration-150">
                                    <!-- Company Details -->
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        <div class="flex items-center gap-3">
                                            <span class="w-10 h-10 rounded-xl bg-indigo-50/80 dark:bg-indigo-500/10 text-indigo-500 font-extrabold flex items-center justify-center text-sm border border-indigo-100/50 dark:border-indigo-500/20 shadow-sm">
                                                {{ log.kode }}
                                            </span>
                                            <div>
                                                <div class="text-sm font-bold text-slate-800 dark:text-slate-100">{{ log.company_name }}</div>
                                                <div class="text-[10px] text-slate-400 mt-0.5">Kode: {{ log.kode }}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <!-- Year -->
                                    <td class="px-4 py-4 whitespace-nowrap text-center text-sm font-bold text-slate-700 dark:text-slate-300">
                                        {{ log.year }}
                                    </td>
                                    <!-- Probability -->
                                    <td class="px-4 py-4 whitespace-nowrap text-center">
                                        <div class="flex flex-col items-center gap-1.5">
                                            <div class="flex items-center gap-2">
                                                <span class="text-[10px] font-bold text-slate-400">Model B (T2):</span>
                                                <span class="text-xs font-black text-slate-800 dark:text-slate-100">
                                                    {{ round((log.model_b_probability !== null ? log.model_b_probability : log.fraud_probability) * 100, 1) }}%
                                                </span>
                                            </div>
                                            <div v-if="log.model_a_probability !== null" class="flex items-center gap-2">
                                                <span class="text-[10px] font-bold text-slate-400">Model A (T3):</span>
                                                <span class="text-xs font-black text-slate-800 dark:text-slate-100">
                                                    {{ round(log.model_a_probability * 100, 1) }}%
                                                </span>
                                            </div>
                                        </div>
                                    </td>
                                    <!-- Prediction -->
                                    <td class="px-4 py-4 whitespace-nowrap text-center">
                                        <div class="flex flex-col items-center gap-1">
                                            <div>
                                                <span class="text-[9px] font-semibold text-slate-500 mr-1">Model B:</span>
                                                <span v-if="(log.model_b_prediction !== null ? log.model_b_prediction : log.prediction) === 1" class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-500/10 text-rose-600 dark:bg-rose-500/20 dark:text-rose-400">
                                                    FRAUD
                                                </span>
                                                <span v-else class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-500/10 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400">
                                                    NORMAL
                                                </span>
                                            </div>
                                            <div v-if="log.model_a_prediction !== null">
                                                <span class="text-[9px] font-semibold text-slate-500 mr-1">Model A:</span>
                                                <span v-if="log.model_a_prediction === 1" class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-500/10 text-rose-600 dark:bg-rose-500/20 dark:text-rose-400">
                                                    FRAUD
                                                </span>
                                                <span v-else class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-500/10 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400">
                                                    NORMAL
                                                </span>
                                            </div>
                                        </div>
                                    </td>
                                    <!-- Combined Risk Level -->
                                    <td class="px-4 py-4 whitespace-nowrap text-center">
                                        <span v-if="log.risk_level === 'High' || log.risk_level === 'Critical'" class="text-[9px] px-2 py-0.5 rounded-full font-bold bg-rose-500/10 text-rose-600 dark:bg-rose-500/20 dark:text-rose-400 uppercase tracking-wider">
                                            {{ log.risk_level }}
                                        </span>
                                        <span v-else-if="log.risk_level === 'Medium'" class="text-[9px] px-2 py-0.5 rounded-full font-bold bg-amber-500/10 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400 uppercase tracking-wider">
                                            {{ log.risk_level }}
                                        </span>
                                        <span v-else class="text-[9px] px-2 py-0.5 rounded-full font-bold bg-emerald-500/10 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400 uppercase tracking-wider">
                                            {{ log.risk_level }}
                                        </span>
                                    </td>
                                    <!-- Created At -->
                                    <td class="px-6 py-4 whitespace-nowrap text-center text-xs text-slate-500 dark:text-slate-400">
                                        {{ formatDate(log.created_at) }}
                                    </td>
                                    <!-- View Action -->
                                    <td class="px-6 py-4 whitespace-nowrap text-right text-xs font-semibold">
                                        <Link v-if="log.ews_record_id" :href="route('ews.show', log.ews_record_id)" class="inline-flex items-center gap-1 py-1.5 px-3 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-indigo-600 dark:text-indigo-400 rounded-lg transition duration-150">
                                            Lihat Audit
                                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                                        </Link>
                                        <span v-else class="text-slate-400 text-xs">-</span>
                                    </td>
                                </tr>
                                <tr v-if="histories.data.length === 0">
                                    <td colspan="7" class="px-6 py-10 text-center text-slate-400 text-sm font-semibold">
                                        Belum ada riwayat hasil prediksi model.
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Pagination -->
                    <div class="px-6 py-4 bg-slate-50 dark:bg-slate-800/40 border-t border-slate-100 dark:border-slate-700/50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
                        <div class="text-slate-500 font-medium">
                            Menampilkan {{ histories.from || 0 }} sampai {{ histories.to || 0 }} dari {{ histories.total }} riwayat
                        </div>
                        <div class="flex items-center gap-1.5">
                            <span v-for="(link, idx) in histories.links" :key="idx">
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
export default {
    methods: {
        round(value, decimals = 2) {
            if (value === null || value === undefined) return '';
            return Number(value).toFixed(decimals);
        },
        formatDate(dateStr) {
            if (!dateStr) return '-';
            const date = new Date(dateStr);
            return date.toLocaleString('id-ID', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }
}
</script>
