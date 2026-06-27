<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>EWS Fraud Report - {{ $record->kode }} ({{ $record->tahun }})</title>
    <style>
        @page {
            margin: 1.2cm 1.5cm;
        }
        body {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: #1e293b;
            font-size: 11px;
            line-height: 1.5;
            background-color: #ffffff;
        }
        h1, h2, h3, h4, h5 {
            color: #0f172a;
            margin: 0;
        }
        .header-table {
            width: 100%;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 12px;
            margin-bottom: 20px;
        }
        .logo-text {
            font-size: 20px;
            font-weight: 800;
            color: #4f46e5;
            letter-spacing: 0.5px;
        }
        .logo-sub {
            font-size: 9px;
            color: #64748b;
            text-transform: uppercase;
            font-weight: bold;
            margin-top: 2px;
        }
        .meta-text {
            text-align: right;
            font-size: 10px;
            color: #64748b;
        }
        .meta-text strong {
            color: #1e293b;
        }
        .section-title {
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
            color: #334155;
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 4px;
        }
        .card-table {
            width: 100%;
            margin-bottom: 15px;
            border-spacing: 10px 0;
            margin-left: -10px;
            margin-right: -10px;
        }
        .card-td {
            vertical-align: top;
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 14px;
        }
        .score-large {
            font-size: 32px;
            font-weight: 800;
            color: #1e293b;
            margin: 8px 0;
            line-height: 1;
        }
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 9px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .badge-high {
            background-color: #ffe4e6;
            color: #b91c1c;
            border: 1px solid #fecdd3;
        }
        .badge-medium {
            background-color: #fef3c7;
            color: #b45309;
            border: 1px solid #fde68a;
        }
        .badge-low {
            background-color: #d1fae5;
            color: #047857;
            border: 1px solid #a7f3d0;
        }
        .badge-trigger {
            background-color: #fee2e2;
            color: #dc2626;
        }
        .badge-ok {
            background-color: #ecfdf5;
            color: #059669;
        }
        .text-muted {
            font-size: 9px;
            color: #64748b;
        }
        .table-data {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        .table-data th {
            background-color: #f1f5f9;
            color: #475569;
            font-weight: bold;
            font-size: 9px;
            text-transform: uppercase;
            padding: 6px 10px;
            border: 1px solid #e2e8f0;
            text-align: left;
        }
        .table-data td {
            padding: 6px 10px;
            border: 1px solid #e2e8f0;
            font-size: 10px;
            vertical-align: middle;
        }
        .bar-container {
            background-color: #e2e8f0;
            border-radius: 4px;
            height: 10px;
            width: 100px;
            display: inline-block;
            vertical-align: middle;
        }
        .bar-fill {
            height: 100%;
            border-radius: 4px;
        }
        .bar-fill-a {
            background-color: #4f46e5;
        }
        .bar-fill-b {
            background-color: #db2777;
        }
        .page-break {
            page-break-before: always;
        }
        .commentary-box {
            background-color: #f8fafc;
            border-left: 4px solid #4f46e5;
            padding: 12px;
            border-radius: 4px;
            margin-top: 10px;
            font-size: 10px;
            line-height: 1.6;
        }
        .alert-box {
            background-color: #fef2f2;
            border: 1px solid #fee2e2;
            color: #991b1b;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 15px;
            font-size: 9.5px;
        }
    </style>
</head>
<body>

    <!-- HEADER SECTION -->
    <table class="header-table">
        <tr>
            <td style="vertical-align: top;">
                <div class="logo-text">EWS FRAUD DETECTION</div>
                <div class="logo-sub">Early Warning System &bull; Risk Audit Report</div>
            </td>
            <td class="meta-text" style="vertical-align: top;">
                <strong>Perusahaan:</strong> {{ $record->nama_perusahaan }} ({{ $record->kode }})<br>
                <strong>Sektor / Fiscal Year:</strong> {{ $record->sektor ?? 'N/A' }} / {{ $record->tahun }}<br>
                <strong>Generated Date:</strong> {{ date('d F Y, H:i') }}
            </td>
        </tr>
    </table>

    <!-- 1. RISK SCORES OVERVIEW -->
    <div class="section-title">Risk Score Summary</div>
    <table class="card-table">
        <tr>
            <td class="card-td" style="width: 50%;">
                <div style="font-weight: bold; font-size: 9px; color: #64748b; text-transform: uppercase;">Combined EWS Fraud Score</div>
                <div class="score-large">{{ number_format($record->combined_fraud_score, 1) }}%</div>
                <div>
                    <span class="badge @if($record->combined_fraud_status === 'High') badge-high @elseif($record->combined_fraud_status === 'Medium') badge-medium @else badge-low @endif">
                        {{ $record->combined_fraud_status }} RISK
                    </span>
                </div>
                <p class="text-muted" style="margin-top: 10px; line-height: 1.4;">
                    Dihitung dengan bobot 70% Financial Risk Score dan 30% Narrative Text Risk Score.
                </p>
            </td>
            <td class="card-td" style="width: 25%;">
                <div style="font-weight: bold; font-size: 9px; color: #64748b; text-transform: uppercase;">Financial Risk Score</div>
                <div class="score-large" style="font-size: 24px; margin: 12px 0;">{{ number_format($record->financial_risk_score, 1) }}%</div>
                <div class="text-muted" style="margin-top: 14px;">Bobot: 70%</div>
                <p class="text-muted" style="margin-top: 4px; line-height: 1.3;">
                    Agregasi dari Beneish M-Score & Isolation Forest.
                </p>
            </td>
            <td class="card-td" style="width: 25%;">
                <div style="font-weight: bold; font-size: 9px; color: #64748b; text-transform: uppercase;">Narrative Risk Score</div>
                <div class="score-large" style="font-size: 24px; margin: 12px 0;">{{ number_format($record->narrative_risk_score, 1) }}%</div>
                <div class="text-muted" style="margin-top: 14px;">Bobot: 30%</div>
                <p class="text-muted" style="margin-top: 4px; line-height: 1.3;">
                    Kombinasi Sentiment, Risk Words, dan Readability.
                </p>
            </td>
        </tr>
    </table>

    <!-- 2. XGBOOST LIVE PREDICTIONS -->
    <div class="section-title">XGBoost ML live Integration</div>
    <table class="card-table" style="margin-bottom: 20px;">
        <tr>
            <td class="card-td" style="width: 50%; padding: 12px; background-color: #f5f3ff; border: 1px solid #ddd6fe;">
                <table style="width: 100%; border: none;">
                    <tr>
                        <td style="font-size: 9px; font-weight: bold; color: #6d28d9; text-transform: uppercase; width: 60%;">Model B (t2 >= 2) Outlier</td>
                        <td style="font-size: 9px; font-weight: bold; color: #6d28d9; text-transform: uppercase; text-align: right; width: 40%;">Probability</td>
                    </tr>
                    <tr>
                        <td style="font-size: 12px; font-weight: bold; color: #1e293b; padding-top: 6px;">
                            {{ $mlModelBPrediction == 1 ? '🔴 High Risk Outlier' : '🟢 Low Risk Normal' }}
                        </td>
                        <td style="font-size: 14px; font-weight: 800; color: #4f46e5; text-align: right; padding-top: 4px;">
                            {{ number_format($mlModelBProbability, 2) }}%
                        </td>
                    </tr>
                </table>
            </td>
            <td class="card-td" style="width: 50%; padding: 12px; background-color: #fdf2f8; border: 1px solid #fbcfe8;">
                <table style="width: 100%; border: none;">
                    <tr>
                        <td style="font-size: 9px; font-weight: bold; color: #be185d; text-transform: uppercase; width: 60%;">Model A (t3 >= 3) Outlier</td>
                        <td style="font-size: 9px; font-weight: bold; color: #be185d; text-transform: uppercase; text-align: right; width: 40%;">Probability</td>
                    </tr>
                    <tr>
                        <td style="font-size: 12px; font-weight: bold; color: #1e293b; padding-top: 6px;">
                            {{ $mlModelAPrediction == 1 ? '🔴 High Risk Outlier' : '🟢 Low Risk Normal' }}
                        </td>
                        <td style="font-size: 14px; font-weight: 800; color: #db2777; text-align: right; padding-top: 4px;">
                            {{ number_format($mlModelAProbability, 2) }}%
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>

    <!-- 3. WEAK LABEL AUDIT -->
    <div class="section-title">Weak Label Rules Evaluation</div>
    @if($record->weak_score >= 2)
        <div class="alert-box">
            <strong>WARNING:</strong> Perusahaan ini terpicu sebanyak <strong>{{ $record->weak_score }} dari 5 Aturan</strong> (Weak Score >= 2).
            Ini menunjukkan adanya anomali data keuangan atau bahasa narasi yang membutuhkan pemeriksaan lebih mendalam.
        </div>
    @endif
    <table class="table-data">
        <thead>
            <tr>
                <th style="width: 45%;">Rule / Indicator</th>
                <th style="width: 15%; text-align: center;">Status</th>
                <th style="width: 40%;">Detail Evaluasi</th>
            </tr>
        </thead>
        <tbody>
            @foreach($rulesStatus as $rule)
            <tr>
                <td style="font-weight: bold; color: #334155;">{{ $rule['name'] }}</td>
                <td style="text-align: center;">
                    <span class="badge @if($rule['triggered']) badge-high @else badge-low @endif">
                        {{ $rule['triggered'] ? 'TRIGGERED' : 'NORMAL' }}
                    </span>
                </td>
                <td style="font-size: 9.5px; color: #475569;">{{ $rule['description'] }}</td>
            </tr>
            @endforeach
        </tbody>
    </table>

    <!-- Page Break to keep it beautiful -->
    <div class="page-break"></div>

    <!-- 4. LOCAL SHAP FEATURE DRIVERS -->
    <div class="section-title">Local SHAP Feature Drivers (Model B - T2)</div>
    <p class="text-muted" style="margin-top: -6px; margin-bottom: 10px;">
        Daftar parameter kontributor utama yang memengaruhi peningkatan atau penurunan risiko secara lokal pada emiten ini.
    </p>
    <table class="table-data">
        <thead>
            <tr>
                <th style="width: 40%;">Parameter</th>
                <th style="width: 15%; text-align: right;">Value</th>
                <th style="width: 25%; text-align: center;">Risk Impact</th>
                <th style="width: 20%; text-align: right;">Shap Influence</th>
            </tr>
        </thead>
        <tbody>
            @foreach($featuresImpactB as $feat)
            <tr>
                <td style="font-weight: bold; color: #334155;">{{ $feat['name'] }}</td>
                <td style="text-align: right;">{{ number_format($feat['value'], 4) }}</td>
                <td style="text-align: center;">
                    <span class="badge @if($feat['direction'] === 'up') badge-high @else badge-low @endif">
                        {{ $feat['impact'] }}
                    </span>
                </td>
                <td style="text-align: right; font-weight: bold; color: @if($feat['direction'] === 'up') #b91c1c @else #047857 @endif">
                    {{ $feat['direction'] === 'up' ? '+' : '-' }}{{ number_format($feat['weight'], 4) }}
                </td>
            </tr>
            @endforeach
        </tbody>
    </table>

    <!-- 5. GLOBAL SHAP FEATURE IMPORTANCE -->
    <div class="section-title">Global SHAP Feature Importance</div>
    <p class="text-muted" style="margin-top: -6px; margin-bottom: 12px;">
        Visualisasi kepentingan fitur global secara agregat yang menunjukkan kontribusi fitur dalam persentase terhadap penentuan Fraud Risk Score.
    </p>
    
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
        <tr>
            <!-- Model A (T3) -->
            <td style="width: 48%; vertical-align: top; padding-right: 15px; border-right: 1px solid #e2e8f0;">
                <div style="font-size: 11px; font-weight: bold; color: #4f46e5; margin-bottom: 8px; text-transform: uppercase;">
                    Model A (T3) - Global Importance
                </div>
                <table style="width: 100%; font-size: 9px; border-collapse: collapse;">
                    @foreach(array_slice($globalShapModelA, 0, 10) as $feat)
                    @php
                        // Scale the bar based on max importance (Model A max is 30.87%)
                        $percent = ($feat['importance'] / 0.308738) * 100;
                    @endphp
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 4px 0; width: 45%; color: #334155; font-weight: bold;">
                            {{ str_replace('Index', 'Idx', str_replace(' (Isolation Forest)', '', str_replace(' (Days Sales in Receivables Index)', '', $feat['name']))) }}
                        </td>
                        <td style="padding: 4px 0; width: 40%;">
                            <div class="bar-container">
                                <div class="bar-fill bar-fill-a" style="width: {{ $percent }}%;"></div>
                            </div>
                        </td>
                        <td style="padding: 4px 0; width: 15%; text-align: right; font-weight: bold; color: #4f46e5;">
                            {{ number_format($feat['importance'] * 100, 2) }}%
                        </td>
                    </tr>
                    @endforeach
                </table>
            </td>
            
            <!-- Model B (T2) -->
            <td style="width: 48%; vertical-align: top; padding-left: 15px;">
                <div style="font-size: 11px; font-weight: bold; color: #db2777; margin-bottom: 8px; text-transform: uppercase;">
                    Model B (T2) - Global Importance
                </div>
                <table style="width: 100%; font-size: 9px; border-collapse: collapse;">
                    @foreach(array_slice($globalShapModelB, 0, 10) as $feat)
                    @php
                        // Scale the bar based on max importance (Model B max is 18.90%)
                        $percent = ($feat['importance'] / 0.189024) * 100;
                    @endphp
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 4px 0; width: 45%; color: #334155; font-weight: bold;">
                            {{ str_replace('Index', 'Idx', str_replace(' (Isolation Forest)', '', str_replace(' (Days Sales in Receivables Index)', '', $feat['name']))) }}
                        </td>
                        <td style="padding: 4px 0; width: 40%;">
                            <div class="bar-container">
                                <div class="bar-fill bar-fill-b" style="width: {{ $percent }}%;"></div>
                            </div>
                        </td>
                        <td style="padding: 4px 0; width: 15%; text-align: right; font-weight: bold; color: #db2777;">
                            {{ number_format($feat['importance'] * 100, 2) }}%
                        </td>
                    </tr>
                    @endforeach
                </table>
            </td>
        </tr>
    </table>

    <!-- 6. AI COMMENTARY (GEMINI LLM) -->
    @if(!empty($record->ai_commentary))
        <div class="section-title" style="margin-top: 15px;">AI Commentary & Recommendation (Gemini LLM)</div>
        <div class="commentary-box">
            {!! nl2br(e($record->ai_commentary)) !!}
        </div>
    @endif

</body>
</html>
