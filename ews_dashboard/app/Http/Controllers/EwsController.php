<?php

namespace App\Http\Controllers;

use App\Models\EwsRecord;
use Illuminate\Http\Request;
use Inertia\Inertia;
use Inertia\Response;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Http;
use Barryvdh\DomPDF\Facade\Pdf;

class EwsController extends Controller
{
    /**
     * Display EWS dashboard and paginated directory.
     */
    public function index(Request $request): Response
    {
        // 1. Base Query for Directory
        $query = EwsRecord::query();

        // Filters
        $search = $request->input('search');
        if ($search) {
            $query->where(function ($q) use ($search) {
                $q->where('nama_perusahaan', 'like', "%{$search}%")
                  ->orWhere('kode', 'like', "%{$search}%")
                  ->orWhere('sektor', 'like', "%{$search}%");
            });
        }

        $year = $request->input('year');
        if ($year) {
            $query->where('tahun', $year);
        }

        $status = $request->input('status');
        if ($status) {
            $query->where('combined_fraud_status', $status);
        }

        $weakT3 = $request->input('weak_t3');
        if ($weakT3 !== null && $weakT3 !== '') {
            $query->where('weak_label_t3', $weakT3);
        }

        $weakT2 = $request->input('weak_t2');
        if ($weakT2 !== null && $weakT2 !== '') {
            $query->where('weak_label_t2', $weakT2);
        }

        // Pagination
        $records = $query->orderBy('combined_fraud_score', 'desc')
            ->paginate(12)
            ->withQueryString();

        // 2. High-Level Summary Stats (cached/pre-calculated from total dataset or filtered depending on view, let's use global statistics for general context)
        $stats = [
            'total_companies' => EwsRecord::distinct('kode')->count('kode'),
            'total_records' => EwsRecord::count(),
            'high_risk_count' => EwsRecord::where('combined_fraud_status', 'High')->count(),
            'avg_combined_score' => round(EwsRecord::avg('combined_fraud_score') ?? 0, 2),
            'avg_narrative_risk' => round(EwsRecord::avg('narrative_risk_score') ?? 0, 2),
            'avg_financial_risk' => round(EwsRecord::avg('financial_risk_score') ?? 0, 2),
            'weak_t3_count' => EwsRecord::where('weak_label_t3', 1)->count(),
            'weak_t2_count' => EwsRecord::where('weak_label_t2', 1)->count(),
        ];

        // 3. Analytics for Charts
        $riskDistribution = EwsRecord::select('combined_fraud_status', DB::raw('count(*) as count'))
            ->groupBy('combined_fraud_status')
            ->get()
            ->pluck('count', 'combined_fraud_status')
            ->toArray();

        // Ensure all keys exist
        $riskDistribution = array_merge([
            'Low' => 0,
            'Medium' => 0,
            'High' => 0,
        ], $riskDistribution);

        $sectorAnalysis = EwsRecord::select('sektor')
            ->selectRaw('count(*) as total')
            ->selectRaw('sum(case when combined_fraud_status = "High" then 1 else 0 end) as high_risk')
            ->selectRaw('avg(combined_fraud_score) as avg_score')
            ->groupBy('sektor')
            ->orderBy('avg_score', 'desc')
            ->limit(8)
            ->get()
            ->map(function ($item) {
                return [
                    'sektor' => $item->sektor ?? 'Other',
                    'total' => (int) $item->total,
                    'high_risk' => (int) $item->high_risk,
                    'avg_score' => round($item->avg_score, 2),
                ];
            });

        $yearlyTrends = EwsRecord::select('tahun')
            ->selectRaw('avg(combined_fraud_score) as avg_combined')
            ->selectRaw('avg(financial_risk_score) as avg_financial')
            ->selectRaw('avg(narrative_risk_score) as avg_narrative')
            ->groupBy('tahun')
            ->orderBy('tahun', 'asc')
            ->get();

        $availableYears = EwsRecord::distinct()->orderBy('tahun', 'desc')->pluck('tahun');
        $availableSectors = EwsRecord::distinct()->whereNotNull('sektor')->orderBy('sektor')->pluck('sektor');

        return Inertia::render('Dashboard', [
            'records' => $records,
            'stats' => $stats,
            'charts' => [
                'riskDistribution' => $riskDistribution,
                'sectorAnalysis' => $sectorAnalysis,
                'yearlyTrends' => $yearlyTrends,
            ],
            'filters' => [
                'search' => $search,
                'year' => $year,
                'status' => $status,
                'weak_t3' => $weakT3,
                'weak_t2' => $weakT2,
            ],
            'availableYears' => $availableYears,
            'availableSectors' => $availableSectors,
        ]);
    }

    /**
     * Display specific company's risk profile details.
     */
    public function show(int $id): Response
    {
        $record = EwsRecord::findOrFail($id);

        // Fetch historical records for the same company to show trends
        $history = EwsRecord::where('kode', $record->kode)
            ->orderBy('tahun', 'asc')
            ->get(['id', 'tahun', 'combined_fraud_score', 'financial_risk_score', 'narrative_risk_score', 'weak_score']);

        // Check weak label rules breakdown for audit display
        $rule1 = $record->m_score !== null && $record->m_score > -2.22;
        $rule2 = $record->anomaly_score_05 !== null && $record->anomaly_score_05 > 0.3; 
        $rule3 = $record->narrative_risk_score !== null && $record->narrative_risk_score > 60;
        $rule4 = $record->cfo_quality_flag !== null && ($record->cfo_quality_flag === 'Low Quality' || $record->cfo_quality_flag === '1' || $record->cfo_quality_flag === 1);
        $rule5 = $record->revenue_growth !== null && $record->revenue_growth > 0.3;

        // Build features payload for FastAPI XGBoost & SHAP model (16 features)
        $payload = [
            'dsri' => (double) ($record->dsri ?? 1.0),
            'gmi' => (double) ($record->gmi ?? 1.0),
            'aqi' => (double) ($record->aqi ?? 1.0),
            'sgi' => (double) ($record->sgi ?? 1.0),
            'lvgi' => (double) ($record->lvgi ?? 1.0),
            'tata' => (double) ($record->tata ?? 0.0),
            'sgai' => (double) ($record->sgai ?? 1.0),
            'revenue_growth' => (double) ($record->revenue_growth ?? 0.0),
            'asset_growth' => (double) ($record->asset_growth ?? 0.0),
            'net_income_growth_assets' => (double) ($record->net_income_growth_assets ?? 0.0),
            'cfo_to_net_income' => (double) ($record->cfo_to_net_income ?? 0.0),
            'sentiment' => (double) ($record->sentiment ?? 0.0),
            'risk_words' => (double) ($record->risk_words ?? 0.0),
            'readability' => (double) ($record->readability ?? 0.0),
            'text_length' => (double) ($record->text_length ?? 0.0),
            'anomaly_score_05' => (double) ($record->anomaly_score_05 ?? 0.0),
        ];

        // Only request AI Commentary generation if it does not already exist in DB
        if (empty($record->ai_commentary)) {
            $payload['nama_perusahaan'] = $record->nama_perusahaan ?? '';
            $payload['kode'] = $record->kode ?? '';
            $payload['year'] = (int) ($record->tahun ?? 0);
            $payload['sektor'] = $record->sektor ?? '';
        }

        // Call FastAPI (Defaulting to host.docker.internal inside Docker container)
        $fastapi_url = env('FASTAPI_API_URL', 'http://host.docker.internal:8000');
        $ml_api_available = false;
        
        $ml_model_b_probability = null;
        $ml_model_b_prediction = null;
        $featuresImpactB = [];
        
        $ml_model_a_probability = null;
        $ml_model_a_prediction = null;
        $featuresImpactA = [];

        try {
            $response = Http::timeout(30)->post($fastapi_url . '/predict', $payload);
            if ($response->successful()) {
                $data = $response->json();
                $ml_api_available = true;
                
                // Save AI Commentary if returned and not cached in DB
                if (!empty($data['ai_commentary']) && empty($record->ai_commentary)) {
                    $record->ai_commentary = $data['ai_commentary'];
                    $record->save();
                }
                
                $featureLabels = [
                    'dsri' => 'DSRI (Days Sales in Receivables Index)',
                    'gmi' => 'GMI (Gross Margin Index)',
                    'aqi' => 'AQI (Asset Quality Index)',
                    'sgi' => 'SGI (Sales Growth Index)',
                    'lvgi' => 'LVGI (Leverage Index)',
                    'tata' => 'TATA (Total Accruals to Total Assets)',
                    'sgai' => 'SGAI (Sales General & Admin Index)',
                    'revenue_growth' => 'Revenue Growth Rate',
                    'asset_growth' => 'Asset Growth Rate',
                    'net_income_growth_assets' => 'Net Income Growth / Assets',
                    'cfo_to_net_income' => 'CFO to Net Income Ratio',
                    'sentiment' => 'Narrative Sentiment',
                    'risk_words' => 'Risk Words Frequency',
                    'readability' => 'Readability Index',
                    'text_length' => 'Text Length',
                    'anomaly_score_05' => 'Anomaly Score (Isolation Forest)',
                ];

                // Parse Model B (t2)
                $modelBData = $data['model_b'] ?? $data;
                $ml_model_b_probability = round(($modelBData['fraud_probability'] ?? 0) * 100, 2);
                $ml_model_b_prediction = $modelBData['fraud_prediction'] ?? 0;
                
                $driversB = $modelBData['top_drivers'] ?? [];
                foreach ($driversB as $driver) {
                    $featKey = $driver['feature'];
                    $shapVal = $driver['shap_value'];
                    $featuresImpactB[] = [
                        'name' => $featureLabels[$featKey] ?? $featKey,
                        'value' => round($record->{$featKey} ?? 0, 4),
                        'impact' => $shapVal > 0 ? 'Pushes Risk Up' : 'Pushes Risk Down',
                        'direction' => $shapVal > 0 ? 'up' : 'down',
                        'weight' => abs($shapVal),
                    ];
                }

                // Parse Model A (t3)
                $modelAData = $data['model_a'] ?? [];
                if (!empty($modelAData)) {
                    $ml_model_a_probability = round(($modelAData['fraud_probability'] ?? 0) * 100, 2);
                    $ml_model_a_prediction = $modelAData['fraud_prediction'] ?? 0;
                    
                    $driversA = $modelAData['top_drivers'] ?? [];
                    foreach ($driversA as $driver) {
                        $featKey = $driver['feature'];
                        $shapVal = $driver['shap_value'];
                        $featuresImpactA[] = [
                            'name' => $featureLabels[$featKey] ?? $featKey,
                            'value' => round($record->{$featKey} ?? 0, 4),
                            'impact' => $shapVal > 0 ? 'Pushes Risk Up' : 'Pushes Risk Down',
                            'direction' => $shapVal > 0 ? 'up' : 'down',
                            'weight' => abs($shapVal),
                        ];
                    }
                }
            }
        } catch (\Exception $e) {
            \Log::warning("FastAPI Prediction Server connection failed: " . $e->getMessage());
        }

        // Fallback if API is offline or returns error
        if (!$ml_api_available) {
            $ml_model_b_probability = round($record->combined_fraud_score ?? 0, 2);
            $ml_model_b_prediction = $record->weak_label_t2 ?? 0;

            $ml_model_a_probability = round($record->combined_fraud_score ?? 0, 2);
            $ml_model_a_prediction = $record->weak_label_t3 ?? 0;

            $dummyImpacts = [
                [
                    'name' => 'TATA (Total Accruals to Total Assets)',
                    'value' => round($record->tata ?? 0, 4),
                    'impact' => $record->tata > 0.05 ? 'High Accruals Risk' : 'Normal',
                    'direction' => $record->tata > 0.02 ? 'up' : 'down',
                    'weight' => abs($record->tata ?? 0) * 15,
                ],
                [
                    'name' => 'CFO to Net Income Ratio',
                    'value' => round($record->cfo_to_net_income ?? 0, 4),
                    'impact' => $record->cfo_quality_flag === 'Low Quality' ? 'Low Quality CFO' : 'Normal',
                    'direction' => $record->cfo_quality_flag === 'Low Quality' ? 'up' : 'down',
                    'weight' => $record->cfo_quality_flag === 'Low Quality' ? 22.5 : 5.0,
                ],
                [
                    'name' => 'SGI (Sales Growth Index)',
                    'value' => round($record->sgi ?? 0, 4),
                    'impact' => $record->sgi > 1.2 ? 'Extreme Sales Growth' : 'Normal',
                    'direction' => $record->sgi > 1.15 ? 'up' : 'down',
                    'weight' => abs(($record->sgi ?? 1) - 1) * 10 + 2,
                ],
                [
                    'name' => 'Risk Words (Narrative Density)',
                    'value' => $record->risk_words ?? 0,
                    'impact' => $record->risk_words > 80 ? 'High Risk Words Density' : 'Normal',
                    'direction' => $record->risk_words > 60 ? 'up' : 'down',
                    'weight' => ($record->risk_words ?? 0) / 10,
                ],
                [
                    'name' => 'Anomaly Score (Isolation Forest)',
                    'value' => round($record->anomaly_score_05 ?? 0, 4),
                    'impact' => $record->anomaly_score_05 > 0.3 ? 'High Anomaly Outlier' : 'Normal',
                    'direction' => $record->anomaly_score_05 > 0.35 ? 'up' : 'down',
                    'weight' => ($record->anomaly_score_05 ?? 0) * 45,
                ],
            ];

            usort($dummyImpacts, function ($a, $b) {
                return $b['weight'] <=> $a['weight'];
            });

            $featuresImpactB = $dummyImpacts;
            $featuresImpactA = $dummyImpacts;
        }

        $rulesStatus = [
            [
                'name' => 'Rule 1: Beneish M-Score Tinggi (> -2.22)',
                'triggered' => $rule1,
                'description' => 'M-Score is ' . round($record->m_score ?? 0, 2) . ', which indicates ' . ($rule1 ? 'high probability of manipulation.' : 'low probability of manipulation.'),
                'badge' => $rule1 ? 'danger' : 'success',
            ],
            [
                'name' => 'Rule 2: Isolation Forest Outlier',
                'triggered' => $rule2,
                'description' => 'Isolation Forest anomaly score is ' . round($record->anomaly_score_05 ?? 0, 4) . ' (> 0.3), meaning ' . ($rule2 ? 'company is a multivariate financial outlier.' : 'company exhibits normal patterns.'),
                'badge' => $rule2 ? 'danger' : 'success',
            ],
            [
                'name' => 'Rule 3: Narrative Risk Tinggi (> 60)',
                'triggered' => $rule3,
                'description' => 'Narrative risk score is ' . round($record->narrative_risk_score ?? 0, 2) . ', reflecting ' . ($rule3 ? 'aberrations in annual report sentiment, readability, and risk disclosures.' : 'normal report readability and sentiment.'),
                'badge' => $rule3 ? 'danger' : 'success',
            ],
            [
                'name' => 'Rule 4: CFO Quality Buruk',
                'triggered' => $rule4,
                'description' => 'CFO Quality Flag is ' . ($record->cfo_quality_flag ?? 'Normal') . '. Net Income is ' . number_format($record->net_income ?? 0) . ' but Operating Cash Flow is ' . number_format($record->cfo ?? 0) . '.',
                'badge' => $rule4 ? 'danger' : 'success',
            ],
            [
                'name' => 'Rule 5: Revenue Growth Extreme (> 30%)',
                'triggered' => $rule5,
                'description' => 'Revenue growth rate is ' . round(($record->revenue_growth ?? 0) * 100, 2) . '%, exceeding normal operating parameters.',
                'badge' => $rule5 ? 'danger' : 'success',
            ],
        ];

        return Inertia::render('Ews/Show', [
            'record' => $record,
            'history' => $history,
            'rulesStatus' => $rulesStatus,
            'mlApiAvailable' => $ml_api_available,
            'aiCommentary' => $record->ai_commentary,
            
            // Model B props
            'mlModelBProbability' => $ml_model_b_probability,
            'mlModelBPrediction' => $ml_model_b_prediction,
            'featuresImpactB' => $featuresImpactB,

            // Model A props
            'mlModelAProbability' => $ml_model_a_probability,
            'mlModelAPrediction' => $ml_model_a_prediction,
            'featuresImpactA' => $featuresImpactA,
        ]);
    }

    /**
     * Export EWS Fraud Report to PDF.
     */
    public function export(int $id)
    {
        $record = EwsRecord::findOrFail($id);

        // Fetch historical records for the same company to show trends
        $history = EwsRecord::where('kode', $record->kode)
            ->orderBy('tahun', 'asc')
            ->get(['id', 'tahun', 'combined_fraud_score', 'financial_risk_score', 'narrative_risk_score', 'weak_score']);

        // Check weak label rules breakdown for audit display
        $rule1 = $record->m_score !== null && $record->m_score > -2.22;
        $rule2 = $record->anomaly_score_05 !== null && $record->anomaly_score_05 > 0.3; 
        $rule3 = $record->narrative_risk_score !== null && $record->narrative_risk_score > 60;
        $rule4 = $record->cfo_quality_flag !== null && ($record->cfo_quality_flag === 'Low Quality' || $record->cfo_quality_flag === '1' || $record->cfo_quality_flag === 1);
        $rule5 = $record->revenue_growth !== null && $record->revenue_growth > 0.3;

        // Build features payload for FastAPI XGBoost & SHAP model (16 features)
        $payload = [
            'dsri' => (double) ($record->dsri ?? 1.0),
            'gmi' => (double) ($record->gmi ?? 1.0),
            'aqi' => (double) ($record->aqi ?? 1.0),
            'sgi' => (double) ($record->sgi ?? 1.0),
            'lvgi' => (double) ($record->lvgi ?? 1.0),
            'tata' => (double) ($record->tata ?? 0.0),
            'sgai' => (double) ($record->sgai ?? 1.0),
            'revenue_growth' => (double) ($record->revenue_growth ?? 0.0),
            'asset_growth' => (double) ($record->asset_growth ?? 0.0),
            'net_income_growth_assets' => (double) ($record->net_income_growth_assets ?? 0.0),
            'cfo_to_net_income' => (double) ($record->cfo_to_net_income ?? 0.0),
            'sentiment' => (double) ($record->sentiment ?? 0.0),
            'risk_words' => (double) ($record->risk_words ?? 0.0),
            'readability' => (double) ($record->readability ?? 0.0),
            'text_length' => (double) ($record->text_length ?? 0.0),
            'anomaly_score_05' => (double) ($record->anomaly_score_05 ?? 0.0),
        ];

        // Only request AI Commentary generation if it does not already exist in DB
        if (empty($record->ai_commentary)) {
            $payload['nama_perusahaan'] = $record->nama_perusahaan ?? '';
            $payload['kode'] = $record->kode ?? '';
            $payload['year'] = (int) ($record->tahun ?? 0);
            $payload['sektor'] = $record->sektor ?? '';
        }

        // Call FastAPI (Defaulting to host.docker.internal inside Docker container)
        $fastapi_url = env('FASTAPI_API_URL', 'http://host.docker.internal:8000');
        $ml_api_available = false;
        
        $ml_model_b_probability = null;
        $ml_model_b_prediction = null;
        $featuresImpactB = [];
        
        $ml_model_a_probability = null;
        $ml_model_a_prediction = null;
        $featuresImpactA = [];

        try {
            $response = Http::timeout(30)->post($fastapi_url . '/predict', $payload);
            if ($response->successful()) {
                $data = $response->json();
                $ml_api_available = true;
                
                // Save AI Commentary if returned and not cached in DB
                if (!empty($data['ai_commentary']) && empty($record->ai_commentary)) {
                    $record->ai_commentary = $data['ai_commentary'];
                    $record->save();
                }
                
                $featureLabels = [
                    'dsri' => 'DSRI (Days Sales in Receivables Index)',
                    'gmi' => 'GMI (Gross Margin Index)',
                    'aqi' => 'AQI (Asset Quality Index)',
                    'sgi' => 'SGI (Sales Growth Index)',
                    'lvgi' => 'LVGI (Leverage Index)',
                    'tata' => 'TATA (Total Accruals to Total Assets)',
                    'sgai' => 'SGAI (Sales General & Admin Index)',
                    'revenue_growth' => 'Revenue Growth Rate',
                    'asset_growth' => 'Asset Growth Rate',
                    'net_income_growth_assets' => 'Net Income Growth / Assets',
                    'cfo_to_net_income' => 'CFO to Net Income Ratio',
                    'sentiment' => 'Narrative Sentiment',
                    'risk_words' => 'Risk Words Frequency',
                    'readability' => 'Readability Index',
                    'text_length' => 'Text Length',
                    'anomaly_score_05' => 'Anomaly Score (Isolation Forest)',
                ];

                // Parse Model B (t2)
                $modelBData = $data['model_b'] ?? $data;
                $ml_model_b_probability = round(($modelBData['fraud_probability'] ?? 0) * 100, 2);
                $ml_model_b_prediction = $modelBData['fraud_prediction'] ?? 0;
                
                $driversB = $modelBData['top_drivers'] ?? [];
                foreach ($driversB as $driver) {
                    $featKey = $driver['feature'];
                    $shapVal = $driver['shap_value'];
                    $featuresImpactB[] = [
                        'name' => $featureLabels[$featKey] ?? $featKey,
                        'value' => round($record->{$featKey} ?? 0, 4),
                        'impact' => $shapVal > 0 ? 'Pushes Risk Up' : 'Pushes Risk Down',
                        'direction' => $shapVal > 0 ? 'up' : 'down',
                        'weight' => abs($shapVal),
                    ];
                }

                // Parse Model A (t3)
                $modelAData = $data['model_a'] ?? [];
                if (!empty($modelAData)) {
                    $ml_model_a_probability = round(($modelAData['fraud_probability'] ?? 0) * 100, 2);
                    $ml_model_a_prediction = $modelAData['fraud_prediction'] ?? 0;
                    
                    $driversA = $modelAData['top_drivers'] ?? [];
                    foreach ($driversA as $driver) {
                        $featKey = $driver['feature'];
                        $shapVal = $driver['shap_value'];
                        $featuresImpactA[] = [
                            'name' => $featureLabels[$featKey] ?? $featKey,
                            'value' => round($record->{$featKey} ?? 0, 4),
                            'impact' => $shapVal > 0 ? 'Pushes Risk Up' : 'Pushes Risk Down',
                            'direction' => $shapVal > 0 ? 'up' : 'down',
                            'weight' => abs($shapVal),
                        ];
                    }
                }
            }
        } catch (\Exception $e) {
            \Log::warning("FastAPI Prediction Server connection failed: " . $e->getMessage());
        }

        // Fallback if API is offline or returns error
        if (!$ml_api_available) {
            $ml_model_b_probability = round($record->combined_fraud_score ?? 0, 2);
            $ml_model_b_prediction = $record->weak_label_t2 ?? 0;

            $ml_model_a_probability = round($record->combined_fraud_score ?? 0, 2);
            $ml_model_a_prediction = $record->weak_label_t3 ?? 0;

            $dummyImpacts = [
                [
                    'name' => 'TATA (Total Accruals to Total Assets)',
                    'value' => round($record->tata ?? 0, 4),
                    'impact' => $record->tata > 0.05 ? 'High Accruals Risk' : 'Normal',
                    'direction' => $record->tata > 0.02 ? 'up' : 'down',
                    'weight' => abs($record->tata ?? 0) * 15,
                ],
                [
                    'name' => 'CFO to Net Income Ratio',
                    'value' => round($record->cfo_to_net_income ?? 0, 4),
                    'impact' => $record->cfo_quality_flag === 'Low Quality' ? 'Low Quality CFO' : 'Normal',
                    'direction' => $record->cfo_quality_flag === 'Low Quality' ? 'up' : 'down',
                    'weight' => $record->cfo_quality_flag === 'Low Quality' ? 22.5 : 5.0,
                ],
                [
                    'name' => 'SGI (Sales Growth Index)',
                    'value' => round($record->sgi ?? 0, 4),
                    'impact' => $record->sgi > 1.2 ? 'Extreme Sales Growth' : 'Normal',
                    'direction' => $record->sgi > 1.15 ? 'up' : 'down',
                    'weight' => abs(($record->sgi ?? 1) - 1) * 10 + 2,
                ],
                [
                    'name' => 'Risk Words (Narrative Density)',
                    'value' => $record->risk_words ?? 0,
                    'impact' => $record->risk_words > 80 ? 'High Risk Words Density' : 'Normal',
                    'direction' => $record->risk_words > 60 ? 'up' : 'down',
                    'weight' => ($record->risk_words ?? 0) / 10,
                ],
                [
                    'name' => 'Anomaly Score (Isolation Forest)',
                    'value' => round($record->anomaly_score_05 ?? 0, 4),
                    'impact' => $record->anomaly_score_05 > 0.3 ? 'High Anomaly Outlier' : 'Normal',
                    'direction' => $record->anomaly_score_05 > 0.35 ? 'up' : 'down',
                    'weight' => ($record->anomaly_score_05 ?? 0) * 45,
                ],
            ];

            usort($dummyImpacts, function ($a, $b) {
                return $b['weight'] <=> $a['weight'];
            });

            $featuresImpactB = $dummyImpacts;
            $featuresImpactA = $dummyImpacts;
        }

        $rulesStatus = [
            [
                'name' => 'Rule 1: Beneish M-Score Tinggi (> -2.22)',
                'triggered' => $rule1,
                'description' => 'M-Score is ' . round($record->m_score ?? 0, 2) . ', which indicates ' . ($rule1 ? 'high probability of manipulation.' : 'low probability of manipulation.'),
                'badge' => $rule1 ? 'danger' : 'success',
            ],
            [
                'name' => 'Rule 2: Isolation Forest Outlier',
                'triggered' => $rule2,
                'description' => 'Isolation Forest anomaly score is ' . round($record->anomaly_score_05 ?? 0, 4) . ' (> 0.3), meaning ' . ($rule2 ? 'company is a multivariate financial outlier.' : 'company exhibits normal patterns.'),
                'badge' => $rule2 ? 'danger' : 'success',
            ],
            [
                'name' => 'Rule 3: Narrative Risk Tinggi (> 60)',
                'triggered' => $rule3,
                'description' => 'Narrative risk score is ' . round($record->narrative_risk_score ?? 0, 2) . ', reflecting ' . ($rule3 ? 'aberrations in annual report sentiment, readability, and risk disclosures.' : 'normal report readability and sentiment.'),
                'badge' => $rule3 ? 'danger' : 'success',
            ],
            [
                'name' => 'Rule 4: CFO Quality Buruk',
                'triggered' => $rule4,
                'description' => 'CFO Quality Flag is ' . ($record->cfo_quality_flag ?? 'Normal') . '. Net Income is ' . number_format($record->net_income ?? 0) . ' but Operating Cash Flow is ' . number_format($record->cfo ?? 0) . '.',
                'badge' => $rule4 ? 'danger' : 'success',
            ],
            [
                'name' => 'Rule 5: Revenue Growth Extreme (> 30%)',
                'triggered' => $rule5,
                'description' => 'Revenue growth rate is ' . round(($record->revenue_growth ?? 0) * 100, 2) . '%, exceeding normal operating parameters.',
                'badge' => $rule5 ? 'danger' : 'success',
            ],
        ];

        // Global SHAP lists
        $globalShapModelA = [
            ['feature' => 'anomaly_score_05', 'name' => 'Anomaly Score (Isolation Forest)', 'importance' => 0.308738],
            ['feature' => 'risk_words', 'name' => 'Risk Words Frequency', 'importance' => 0.172333],
            ['feature' => 'sgi', 'name' => 'SGI (Sales Growth Index)', 'importance' => 0.148532],
            ['feature' => 'tata', 'name' => 'TATA (Total Accruals to Total Assets)', 'importance' => 0.087434],
            ['feature' => 'sentiment', 'name' => 'Narrative Sentiment', 'importance' => 0.053890],
            ['feature' => 'text_length', 'name' => 'Text Length', 'importance' => 0.044062],
            ['feature' => 'cfo_to_net_income', 'name' => 'CFO to Net Income Ratio', 'importance' => 0.041392],
            ['feature' => 'asset_growth', 'name' => 'Asset Growth Rate', 'importance' => 0.037867],
            ['feature' => 'readability', 'name' => 'Readability Index', 'importance' => 0.022627],
            ['feature' => 'dsri', 'name' => 'DSRI (Days Sales in Receivables Index)', 'importance' => 0.021408],
            ['feature' => 'gmi', 'name' => 'GMI (Gross Margin Index)', 'importance' => 0.019350],
            ['feature' => 'net_income_growth_assets', 'name' => 'Net Income Growth / Assets', 'importance' => 0.014231],
            ['feature' => 'lvgi', 'name' => 'LVGI (Leverage Index)', 'importance' => 0.011238],
            ['feature' => 'sgai', 'name' => 'SGAI (Sales General & Admin Index)', 'importance' => 0.009093],
            ['feature' => 'aqi', 'name' => 'AQI (Asset Quality Index)', 'importance' => 0.007805],
            ['feature' => 'revenue_growth', 'name' => 'Revenue Growth Rate', 'importance' => 0.000000],
        ];

        $globalShapModelB = [
            ['feature' => 'tata', 'name' => 'TATA (Total Accruals to Total Assets)', 'importance' => 0.189024],
            ['feature' => 'cfo_to_net_income', 'name' => 'CFO to Net Income Ratio', 'importance' => 0.181863],
            ['feature' => 'sgi', 'name' => 'SGI (Sales Growth Index)', 'importance' => 0.154076],
            ['feature' => 'anomaly_score_05', 'name' => 'Anomaly Score (Isolation Forest)', 'importance' => 0.108183],
            ['feature' => 'risk_words', 'name' => 'Risk Words Frequency', 'importance' => 0.056944],
            ['feature' => 'revenue_growth', 'name' => 'Revenue Growth Rate', 'importance' => 0.054025],
            ['feature' => 'dsri', 'name' => 'DSRI (Days Sales in Receivables Index)', 'importance' => 0.046694],
            ['feature' => 'sentiment', 'name' => 'Narrative Sentiment', 'importance' => 0.040925],
            ['feature' => 'aqi', 'name' => 'AQI (Asset Quality Index)', 'importance' => 0.031598],
            ['feature' => 'text_length', 'name' => 'Text Length', 'importance' => 0.030194],
            ['feature' => 'gmi', 'name' => 'GMI (Gross Margin Index)', 'importance' => 0.029379],
            ['feature' => 'readability', 'name' => 'Readability Index', 'importance' => 0.023423],
            ['feature' => 'lvgi', 'name' => 'LVGI (Leverage Index)', 'importance' => 0.018400],
            ['feature' => 'sgai', 'name' => 'SGAI (Sales General & Admin Index)', 'importance' => 0.015965],
            ['feature' => 'net_income_growth_assets', 'name' => 'Net Income Growth / Assets', 'importance' => 0.010057],
            ['feature' => 'asset_growth', 'name' => 'Asset Growth Rate', 'importance' => 0.009250],
        ];

        $pdf = Pdf::loadView('ews.report_pdf', [
            'record' => $record,
            'history' => $history,
            'rulesStatus' => $rulesStatus,
            'mlApiAvailable' => $ml_api_available,
            'aiCommentary' => $record->ai_commentary,
            
            // Model B props
            'mlModelBProbability' => $ml_model_b_probability,
            'mlModelBPrediction' => $ml_model_b_prediction,
            'featuresImpactB' => $featuresImpactB,

            // Model A props
            'mlModelAProbability' => $ml_model_a_probability,
            'mlModelAPrediction' => $ml_model_a_prediction,
            'featuresImpactA' => $featuresImpactA,

            // Global SHAP lists
            'globalShapModelA' => $globalShapModelA,
            'globalShapModelB' => $globalShapModelB,
        ]);

        return $pdf->download("EWS_Fraud_Report_{$record->kode}_{$record->tahun}.pdf");
    }

    public function history(Request $request): Response
    {
        $search = $request->input('search');
        $query = \App\Models\PredictionHistory::query();
        
        if ($search) {
            $query->where(function($q) use ($search) {
                $q->where('prediction_history.company_name', 'like', "%{$search}%")
                  ->orWhere('prediction_history.kode', 'like', "%{$search}%");
            });
        }
        
        $histories = $query->leftJoin('ews_records', function($join) {
                $join->on('prediction_history.kode', '=', 'ews_records.kode')
                     ->on('prediction_history.year', '=', 'ews_records.tahun');
            })
            ->select('prediction_history.*', 'ews_records.id as ews_record_id')
            ->orderBy('prediction_history.created_at', 'desc')
            ->paginate(15)
            ->withQueryString();
        
        return Inertia::render('Prediction/PredictionHistory', [
            'histories' => $histories,
            'filters' => [
                'search' => $search
            ]
        ]);
    }
    
    public function uploadForm(): Response
    {
        $companies = EwsRecord::select('kode', 'nama_perusahaan', 'sektor')
            ->orderBy('kode')
            ->get()
            ->unique('kode')
            ->values();
            
        return Inertia::render('Prediction/UploadPredict', [
            'companies' => $companies
        ]);
    }
    
    public function checkLag(Request $request)
    {
        $kode = $request->input('kode');
        $year = intval($request->input('year'));
        
        $lagRecord = EwsRecord::where('kode', $kode)
            ->where('tahun', $year - 1)
            ->first();
            
        return response()->json([
            'found' => $lagRecord !== null,
            'data' => $lagRecord
        ]);
    }
    
    public function processUploadPredict(Request $request)
    {
        $request->validate([
            'kode' => 'required|string',
            'year' => 'required|integer|between:2021,2026',
            'sektor' => 'required|string',
            'nama_perusahaan' => 'required|string',
            'financial_statement' => 'required|file|mimes:pdf',
            'annual_report' => 'nullable|file|mimes:pdf',
        ]);
        
        $kode = strtoupper(trim($request->input('kode')));
        $year = intval($request->input('year'));
        $sektor = trim($request->input('sektor'));
        $nama_perusahaan = trim($request->input('nama_perusahaan'));
        
        // Find lag metrics in DB if not manually overridden
        $lagRecord = EwsRecord::where('kode', $kode)->where('tahun', $year - 1)->first();
        
        $lagData = [
            'total_assets_lag' => $request->input('total_assets_lag', $lagRecord->total_assets ?? 0.0),
            'revenue_lag' => $request->input('revenue_lag', $lagRecord->revenue ?? 0.0),
            'receivables_lag' => $request->input('receivables_lag', $lagRecord->receivables ?? 0.0),
            'net_income_lag' => $request->input('net_income_lag', $lagRecord->net_income ?? 0.0),
            'total_liabilities_lag' => $request->input('total_liabilities_lag', $lagRecord->total_liabilities ?? 0.0),
            'current_assets_lag' => $request->input('current_assets_lag', $lagRecord->current_assets ?? 0.0),
            'ppe_lag' => $request->input('ppe_lag', $lagRecord->ppe ?? 0.0),
            'depreciation_lag' => $request->input('depreciation_lag', $lagRecord->depreciation ?? 0.0),
            'selling_expense_lag' => $request->input('selling_expense_lag', $lagRecord->selling_expense ?? 0.0),
            'ga_expense_lag' => $request->input('ga_expense_lag', $lagRecord->ga_expense ?? 0.0),
            'gross_profit_lag' => $request->input('gross_profit_lag', $lagRecord->gross_profit ?? 0.0),
        ];
        
        $fsFile = $request->file('financial_statement');
        $arFile = $request->file('annual_report');
        
        // Prepare attachment post to FastAPI
        $apiPost = Http::attach(
            'financial_statement',
            file_get_contents($fsFile->getRealPath()),
            $fsFile->getClientOriginalName()
        );
        
        if ($arFile) {
            $apiPost = $apiPost->attach(
                'annual_report',
                file_get_contents($arFile->getRealPath()),
                $arFile->getClientOriginalName()
            );
        }
        
        // Merge text fields and lag values
        $postData = array_merge([
            'kode' => $kode,
            'year' => $year,
            'sektor' => $sektor,
            'nama_perusahaan' => $nama_perusahaan,
        ], $lagData);
        
        // Call FastAPI
        try {
            $response = $apiPost->timeout(60)->post('http://host.docker.internal:8000/upload-predict', $postData);
        } catch (\Exception $e) {
            return back()->withErrors(['error' => 'Gagal menghubungi server FastAPI ML: ' . $e->getMessage()]);
        }
        
        if (!$response->successful()) {
            return back()->withErrors(['error' => 'API ML mengembalikan error: ' . $response->body()]);
        }
        
        $resData = $response->json();
        
        // Save files locally
        $fsPath = $fsFile->storeAs('uploads/financial_statements', "FinancialStatement-{$year}-{$kode}.pdf", 'public');
        $arPath = $arFile ? $arFile->storeAs('uploads/annual_reports', "AnnualReport-{$year}-{$kode}.pdf", 'public') : null;
        
        // Map all returned properties to EwsRecord schema
        $recordData = [
            'nama_perusahaan' => $resData['nama_perusahaan'],
            'sektor' => $resData['sektor'],
            'file' => $fsFile->getClientOriginalName(),
            'path' => $fsPath,
            
            // Financials
            'total_assets' => $resData['extracted_financials']['total_assets'],
            'total_liabilities' => $resData['extracted_financials']['total_liabilities'],
            'total_equity' => $resData['extracted_financials']['total_equity'],
            'current_assets' => $resData['extracted_financials']['current_assets'],
            'ppe' => $resData['extracted_financials']['ppe'],
            'depreciation' => $resData['extracted_financials']['depreciation'],
            'revenue' => $resData['extracted_financials']['revenue'],
            'receivables' => $resData['extracted_financials']['receivables'],
            'gross_profit' => $resData['extracted_financials']['gross_profit'],
            'selling_expense' => $resData['extracted_financials']['selling_expense'],
            'ga_expense' => $resData['extracted_financials']['ga_expense'],
            'net_income' => $resData['extracted_financials']['net_income'],
            'cfo' => $resData['extracted_financials']['cfo'],
            
            // Beneish & M-score
            'dsri' => $resData['calculated_ratios']['dsri'],
            'gmi' => $resData['calculated_ratios']['gmi'],
            'aqi' => $resData['calculated_ratios']['aqi'],
            'sgi' => $resData['calculated_ratios']['sgi'],
            'lvgi' => $resData['calculated_ratios']['lvgi'],
            'depi' => $resData['calculated_ratios']['depi'],
            'sgai' => $resData['calculated_ratios']['sgai'],
            'tata' => $resData['calculated_ratios']['tata'],
            'm_score' => $resData['calculated_ratios']['m_score'],
            'fraud_flag' => $resData['calculated_ratios']['fraud_flag'],
            
            // Trend/growth
            'revenue_growth' => $resData['calculated_ratios']['revenue_growth'],
            'asset_growth' => $resData['calculated_ratios']['asset_growth'],
            'net_income_growth_assets' => $resData['calculated_ratios']['net_income_growth_assets'],
            'cfo_to_net_income' => $resData['calculated_ratios']['cfo_to_net_income'],
            'cfo_quality_flag' => $resData['calculated_ratios']['cfo_quality_flag'],
            
            // Anomaly & NLP
            'anomaly_score_05' => $resData['scores']['anomaly_score_05'],
            'sentiment' => $resData['extracted_narratives']['sentiment'],
            'risk_words' => $resData['extracted_narratives']['risk_words'],
            'readability' => $resData['extracted_narratives']['readability'],
            'text_length' => $resData['extracted_narratives']['text_length'],
            
            // Composites
            'narrative_risk_score' => $resData['scores']['narrative_risk_score'],
            'financial_risk_score' => $resData['scores']['financial_risk_score'],
            'combined_fraud_score' => $resData['scores']['combined_fraud_score'],
            'combined_fraud_status' => $resData['scores']['combined_fraud_status'],
            
            // Weak Labeling
            'weak_score' => $resData['weak_labeling']['weak_score'],
            'weak_label' => $resData['weak_labeling']['weak_label_t3'], // default general label
            'weak_label_t3' => $resData['weak_labeling']['weak_label_t3'],
            'weak_label_t2' => $resData['weak_labeling']['weak_label_t2'],
            
            // AI Commentary
            'ai_commentary' => $resData['ai_commentary'] ?? null,
        ];
        
        // Update or insert EWS record
        $record = EwsRecord::updateOrCreate(
            ['kode' => $kode, 'tahun' => $year],
            $recordData
        );
        
        // Log in PredictionHistory
        \App\Models\PredictionHistory::create([
            'company_name' => $nama_perusahaan,
            'kode' => $kode,
            'year' => $year,
            'fraud_probability' => $resData['model_b']['fraud_probability'] ?? $resData['prediction']['fraud_probability'],
            'risk_level' => $resData['scores']['combined_fraud_status'],
            'prediction' => $resData['model_b']['fraud_prediction'] ?? $resData['prediction']['fraud_prediction'],
            'model_b_probability' => $resData['model_b']['fraud_probability'] ?? $resData['prediction']['fraud_probability'],
            'model_b_prediction' => $resData['model_b']['fraud_prediction'] ?? $resData['prediction']['fraud_prediction'],
            'model_a_probability' => $resData['model_a']['fraud_probability'] ?? null,
            'model_a_prediction' => $resData['model_a']['fraud_prediction'] ?? null,
        ]);
        
        return redirect()->route('ews.show', $record->id);
    }
}
