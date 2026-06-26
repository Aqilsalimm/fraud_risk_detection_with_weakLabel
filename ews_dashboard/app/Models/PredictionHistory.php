<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class PredictionHistory extends Model
{
    use HasFactory;

    protected $table = 'prediction_history';

    protected $guarded = [];

    protected $casts = [
        'year' => 'integer',
        'fraud_probability' => 'double',
        'prediction' => 'integer',
        'model_b_probability' => 'double',
        'model_b_prediction' => 'integer',
        'model_a_probability' => 'double',
        'model_a_prediction' => 'integer',
    ];
}
