<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class EwsRecord extends Model
{
    use HasFactory;

    /**
     * The attributes that are not mass assignable.
     *
     * @var array
     */
    protected $guarded = [];

    /**
     * Get the attributes that should be cast.
     *
     * @return array<string, string>
     */
    protected function casts(): array
    {
        return [
            'total_assets' => 'double',
            'total_liabilities' => 'double',
            'total_equity' => 'double',
            'current_assets' => 'double',
            'ppe' => 'double',
            'depreciation' => 'double',
            'revenue' => 'double',
            'receivables' => 'double',
            'gross_profit' => 'double',
            'selling_expense' => 'double',
            'ga_expense' => 'double',
            'net_income' => 'double',
            'cfo' => 'double',
            'dsri' => 'double',
            'gmi' => 'double',
            'aqi' => 'double',
            'sgi' => 'double',
            'lvgi' => 'double',
            'depi' => 'double',
            'sgai' => 'double',
            'tata' => 'double',
            'm_score' => 'double',
            'revenue_growth' => 'double',
            'asset_growth' => 'double',
            'net_income_growth_assets' => 'double',
            'cfo_to_net_income' => 'double',
            'anomaly_score_05' => 'double',
            'sentiment' => 'double',
            'risk_words' => 'double',
            'readability' => 'double',
            'text_length' => 'double',
            'narrative_risk_score' => 'double',
            'financial_risk_score' => 'double',
            'combined_fraud_score' => 'double',
            'weak_score' => 'integer',
            'weak_label' => 'integer',
            'weak_label_t3' => 'integer',
            'weak_label_t2' => 'integer',
        ];
    }
}
