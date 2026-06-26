<script setup>
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import { Head, useForm } from '@inertiajs/vue3';
import { ref, watch } from 'vue';

const props = defineProps({
    companies: Array
});

// Autocomplete and search state
const selectedCompany = ref('');
const showDropdown = ref(false);
const filteredCompanies = ref([]);

const searchCompany = () => {
    if (!selectedCompany.value) {
        filteredCompanies.value = props.companies;
    } else {
        const query = selectedCompany.value.toLowerCase();
        filteredCompanies.value = props.companies.filter(c => 
            c.nama_perusahaan.toLowerCase().includes(query) || 
            c.kode.toLowerCase().includes(query)
        );
    }
};

const selectCompany = (company) => {
    selectedCompany.value = `${company.kode} - ${company.nama_perusahaan}`;
    form.kode = company.kode;
    form.nama_perusahaan = company.nama_perusahaan;
    form.sektor = company.sektor || '';
    showDropdown.value = false;
    triggerLagCheck();
};

const handleNewCompanyInput = () => {
    form.kode = '';
    form.nama_perusahaan = selectedCompany.value;
    form.sektor = '';
};

// Form state
const form = useForm({
    kode: '',
    year: 2024,
    sektor: '',
    nama_perusahaan: '',
    financial_statement: null,
    annual_report: null,
    
    // Lag variables
    total_assets_lag: 0,
    revenue_lag: 0,
    receivables_lag: 0,
    net_income_lag: 0,
    total_liabilities_lag: 0,
    current_assets_lag: 0,
    ppe_lag: 0,
    depreciation_lag: 0,
    selling_expense_lag: 0,
    ga_expense_lag: 0,
    gross_profit_lag: 0
});

// Lag check states
const lagChecked = ref(false);
const lagFound = ref(false);
const checkingLag = ref(false);
const lagDataSummary = ref(null);
const showLagFields = ref(false);

const triggerLagCheck = async () => {
    if (!form.kode || !form.year) {
        lagChecked.value = false;
        lagFound.value = false;
        return;
    }
    
    checkingLag.value = true;
    try {
        const res = await fetch(route('ews.check-lag', { kode: form.kode, year: form.year }));
        const data = await res.json();
        
        lagChecked.value = true;
        if (data.found && data.data) {
            lagFound.value = true;
            lagDataSummary.value = data.data;
            
            // Populate lag variables from found record
            form.total_assets_lag = data.data.total_assets || 0;
            form.revenue_lag = data.data.revenue || 0;
            form.receivables_lag = data.data.receivables || 0;
            form.net_income_lag = data.data.net_income || 0;
            form.total_liabilities_lag = data.data.total_liabilities || 0;
            form.current_assets_lag = data.data.current_assets || 0;
            form.ppe_lag = data.data.ppe || 0;
            form.depreciation_lag = data.data.depreciation || 0;
            form.selling_expense_lag = data.data.selling_expense || 0;
            form.ga_expense_lag = data.data.ga_expense || 0;
            form.gross_profit_lag = data.data.gross_profit || 0;
        } else {
            lagFound.value = false;
            lagDataSummary.value = null;
            
            // Reset lag variables
            form.total_assets_lag = 0;
            form.revenue_lag = 0;
            form.receivables_lag = 0;
            form.net_income_lag = 0;
            form.total_liabilities_lag = 0;
            form.current_assets_lag = 0;
            form.ppe_lag = 0;
            form.depreciation_lag = 0;
            form.selling_expense_lag = 0;
            form.ga_expense_lag = 0;
            form.gross_profit_lag = 0;
        }
    } catch (e) {
        console.error("Error checking lag data:", e);
    } finally {
        checkingLag.value = false;
    }
};

watch(() => form.year, () => {
    triggerLagCheck();
});

const handleFileChange = (field, event) => {
    form[field] = event.target.files[0];
};

const submitForm = () => {
    form.post(route('prediction.process'), {
        forceFormData: true,
        onSuccess: () => {
            // success is handled by redirect
        }
    });
};
</script>

<template>
    <Head title="Upload & Predict" />

    <AuthenticatedLayout>
        <template #header>
            <div>
                <h2 class="text-2xl font-bold leading-tight text-slate-800 dark:text-slate-100 flex items-center gap-2">
                    <span class="p-2 bg-indigo-500/10 text-indigo-500 rounded-lg dark:bg-indigo-500/20">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                        </svg>
                    </span>
                    Upload & Predict EWS
                </h2>
                <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    Unggah Laporan Keuangan (PDF) dan Laporan Tahunan (PDF) untuk deteksi fraud berbasis AI.
                </p>
            </div>
        </template>

        <div class="py-6">
            <div class="mx-auto max-w-4xl sm:px-6 lg:px-8">
                <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700/50 shadow-sm overflow-hidden p-6 sm:p-8">
                    
                    <form @submit.prevent="submitForm" class="space-y-6">
                        <!-- Validation Errors -->
                        <div v-if="form.errors.error" class="p-4 bg-rose-500/15 border border-rose-500/20 text-rose-600 dark:text-rose-400 rounded-xl text-sm font-semibold">
                            {{ form.errors.error }}
                        </div>

                        <!-- Grid Section: Company Metadata -->
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
                            
                            <!-- Search / Choose Company -->
                            <div class="relative">
                                <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Pilih/Cari Emiten</label>
                                <input 
                                    v-model="selectedCompany" 
                                    @focus="showDropdown = true" 
                                    @input="searchCompany"
                                    type="text" 
                                    placeholder="Ketik kode saham atau nama..." 
                                    class="block w-full py-2 px-3 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl dark:text-slate-200 focus:ring-indigo-500 focus:border-indigo-500" 
                                />
                                
                                <!-- Autocomplete Dropdown -->
                                <div v-if="showDropdown && filteredCompanies.length > 0" class="absolute z-10 w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl mt-1 shadow-lg max-h-60 overflow-y-auto">
                                    <button 
                                        v-for="c in filteredCompanies" 
                                        :key="c.kode" 
                                        type="button" 
                                        @click="selectCompany(c)" 
                                        class="w-full text-left py-2.5 px-4 text-xs hover:bg-indigo-500 hover:text-white transition duration-150 border-b border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300"
                                    >
                                        <strong>{{ c.kode }}</strong> - {{ c.nama_perusahaan }}
                                    </button>
                                </div>
                            </div>

                            <!-- Year Picker -->
                            <div>
                                <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Tahun Buku</label>
                                <select v-model="form.year" class="block w-full py-2 px-3 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl dark:text-slate-200 focus:ring-indigo-500 focus:border-indigo-500">
                                    <option v-for="yr in [2021, 2022, 2023, 2024, 2025, 2026]" :key="yr" :value="yr">{{ yr }}</option>
                                </select>
                            </div>
                        </div>

                        <!-- Grid Section: Manual Input Fields (Optional if company chosen) -->
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
                            <div>
                                <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Kode Emiten</label>
                                <input v-model="form.kode" required type="text" placeholder="Contoh: AALI" class="block w-full py-2 px-3 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl dark:text-slate-200 focus:ring-indigo-500 focus:border-indigo-500" />
                            </div>

                            <div class="sm:col-span-2">
                                <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Nama Perusahaan</label>
                                <input v-model="form.nama_perusahaan" required type="text" placeholder="Contoh: Astra Agro Lestari Tbk" class="block w-full py-2 px-3 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl dark:text-slate-200 focus:ring-indigo-500 focus:border-indigo-500" />
                            </div>
                        </div>

                        <div>
                            <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Sektor Industri</label>
                            <input v-model="form.sektor" required type="text" placeholder="Contoh: Consumer Non-Cyclicals" class="block w-full py-2 px-3 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl dark:text-slate-200 focus:ring-indigo-500 focus:border-indigo-500" />
                        </div>

                        <!-- Lag Status Notification -->
                        <div v-if="checkingLag" class="p-4 bg-slate-50 dark:bg-slate-900 rounded-xl flex items-center justify-center gap-2">
                            <span class="w-4 h-4 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin"></span>
                            <span class="text-xs text-slate-500">Memeriksa data pembanding (lag) di database...</span>
                        </div>

                        <div v-else-if="lagChecked">
                            <!-- Lag Found -->
                            <div v-if="lagFound" class="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-600 dark:text-emerald-400 space-y-2">
                                <div class="flex items-center gap-2 text-sm font-bold">
                                    <svg class="w-5 h-5 text-emerald-500" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>
                                    Data Pembanding (Lag t-1) tahun {{ form.year - 1 }} ditemukan!
                                </div>
                                <p class="text-xs">
                                    Data keuangan pembanding untuk emiten <strong>{{ form.kode }}</strong> tahun buku <strong>{{ form.year - 1 }}</strong> sudah dimuat secara otomatis. Parameter lag akan digunakan untuk menghitung Beneish Index.
                                </p>
                            </div>

                            <!-- Lag Not Found -->
                            <div v-else class="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl text-amber-600 dark:text-amber-400 space-y-2">
                                <div class="flex items-center gap-2 text-sm font-bold">
                                    <svg class="w-5 h-5 text-amber-500" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>
                                    Data Pembanding (Lag t-1) tahun {{ form.year - 1 }} tidak ditemukan.
                                </div>
                                <p class="text-xs">
                                    Parameter keuangan tahun pembanding <strong>{{ form.year - 1 }}</strong> harus dimasukkan secara manual pada bagian override di bawah.
                                </p>
                            </div>
                        </div>

                        <!-- Lag Overrides (Collapsible) -->
                        <div class="border border-slate-200 dark:border-slate-700 rounded-2xl overflow-hidden">
                            <button 
                                type="button" 
                                @click="showLagFields = !showLagFields" 
                                class="w-full flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800/40 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider hover:bg-slate-100/50 transition duration-150"
                            >
                                <span>Override / Input Parameter Lag Keuangan (t-1)</span>
                                <svg class="w-4 h-4 transform transition-transform duration-200" :class="{'rotate-180': showLagFields}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                            </button>
                            
                            <div v-show="showLagFields" class="p-5 grid grid-cols-1 sm:grid-cols-3 gap-4 border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900/20">
                                <div>
                                    <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1">Total Assets (t-1)</label>
                                    <input v-model.number="form.total_assets_lag" type="number" step="any" class="block w-full py-1.5 px-2.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-slate-200" />
                                </div>
                                <div>
                                    <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1">Revenue (t-1)</label>
                                    <input v-model.number="form.revenue_lag" type="number" step="any" class="block w-full py-1.5 px-2.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-slate-200" />
                                </div>
                                <div>
                                    <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1">Receivables (t-1)</label>
                                    <input v-model.number="form.receivables_lag" type="number" step="any" class="block w-full py-1.5 px-2.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-slate-200" />
                                </div>
                                <div>
                                    <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1">Net Income (t-1)</label>
                                    <input v-model.number="form.net_income_lag" type="number" step="any" class="block w-full py-1.5 px-2.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-slate-200" />
                                </div>
                                <div>
                                    <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1">Total Liabilities (t-1)</label>
                                    <input v-model.number="form.total_liabilities_lag" type="number" step="any" class="block w-full py-1.5 px-2.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-slate-200" />
                                </div>
                                <div>
                                    <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1">Current Assets (t-1)</label>
                                    <input v-model.number="form.current_assets_lag" type="number" step="any" class="block w-full py-1.5 px-2.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-slate-200" />
                                </div>
                                <div>
                                    <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1">PPE (t-1)</label>
                                    <input v-model.number="form.ppe_lag" type="number" step="any" class="block w-full py-1.5 px-2.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-slate-200" />
                                </div>
                                <div>
                                    <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1">Depreciation (t-1)</label>
                                    <input v-model.number="form.depreciation_lag" type="number" step="any" class="block w-full py-1.5 px-2.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-slate-200" />
                                </div>
                                <div>
                                    <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1">Selling Expense (t-1)</label>
                                    <input v-model.number="form.selling_expense_lag" type="number" step="any" class="block w-full py-1.5 px-2.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-slate-200" />
                                </div>
                                <div>
                                    <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1">G&A Expense (t-1)</label>
                                    <input v-model.number="form.ga_expense_lag" type="number" step="any" class="block w-full py-1.5 px-2.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-slate-200" />
                                </div>
                                <div>
                                    <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1">Gross Profit (t-1)</label>
                                    <input v-model.number="form.gross_profit_lag" type="number" step="any" class="block w-full py-1.5 px-2.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-slate-200" />
                                </div>
                            </div>
                        </div>

                        <!-- File Upload Section -->
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
                            
                            <!-- Financial Statement Upload -->
                            <div class="border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-indigo-500 rounded-2xl p-5 text-center transition duration-150 bg-slate-50/30 dark:bg-slate-900/10">
                                <label class="cursor-pointer block">
                                    <svg class="mx-auto h-10 w-10 text-slate-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                                    <span class="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">Financial Statement (Laporan Keuangan)</span>
                                    <span class="text-[10px] text-slate-400 block mb-3">Hanya file PDF (Wajib)</span>
                                    <input required type="file" accept="application/pdf" @change="handleFileChange('financial_statement', $event)" class="hidden" />
                                    <span class="py-1 px-3 bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-500/10 dark:hover:bg-indigo-500/20 text-indigo-500 dark:text-indigo-400 rounded-xl text-xs font-bold transition">
                                        {{ form.financial_statement ? form.financial_statement.name : 'Pilih File PDF' }}
                                    </span>
                                </label>
                            </div>

                            <!-- Annual Report Upload -->
                            <div class="border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-indigo-500 rounded-2xl p-5 text-center transition duration-150 bg-slate-50/30 dark:bg-slate-900/10">
                                <label class="cursor-pointer block">
                                    <svg class="mx-auto h-10 w-10 text-slate-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
                                    <span class="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">Annual Report (Laporan Tahunan)</span>
                                    <span class="text-[10px] text-slate-400 block mb-3">Hanya file PDF (Opsional)</span>
                                    <input type="file" accept="application/pdf" @change="handleFileChange('annual_report', $event)" class="hidden" />
                                    <span class="py-1 px-3 bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-500/10 dark:hover:bg-indigo-500/20 text-indigo-500 dark:text-indigo-400 rounded-xl text-xs font-bold transition">
                                        {{ form.annual_report ? form.annual_report.name : 'Pilih File PDF' }}
                                    </span>
                                </label>
                            </div>
                        </div>

                        <!-- Progress Bar for uploading -->
                        <div v-if="form.progress" class="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-2 overflow-hidden">
                            <div class="bg-indigo-600 h-full transition-all duration-300" :style="`width: ${form.progress.percentage}%`"></div>
                        </div>

                        <!-- Submit Button -->
                        <div class="flex justify-end gap-3 border-t border-slate-100 dark:border-slate-700 pt-6">
                            <button 
                                type="submit" 
                                :disabled="form.processing"
                                class="w-full sm:w-auto py-2.5 px-6 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-bold shadow flex items-center justify-center gap-2 disabled:opacity-50 transition"
                            >
                                <span v-if="form.processing" class="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin"></span>
                                {{ form.processing ? 'Sedang Memproses...' : 'Proses & Prediksi Fraud' }}
                            </button>
                        </div>
                    </form>

                </div>
            </div>
        </div>
    </AuthenticatedLayout>
</template>
