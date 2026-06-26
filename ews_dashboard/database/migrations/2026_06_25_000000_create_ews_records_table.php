<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('ews_records', function (Blueprint $table) {
            $table->id();
            
            // Metadata
            $table->string('kode', 10);
            $table->integer('tahun');
            $table->string('nama_perusahaan', 255);
            $table->string('sektor', 255)->nullable();
            $table->string('file', 255)->nullable();
            $table->text('path')->nullable();
            
            // Financial Variables (using double to allow null and large numbers)
            $table->double('total_assets')->nullable();
            $table->double('total_liabilities')->nullable();
            $table->double('total_equity')->nullable();
            $table->double('current_assets')->nullable();
            $table->double('ppe')->nullable();
            $table->double('depreciation')->nullable();
            $table->double('revenue')->nullable();
            $table->double('receivables')->nullable();
            $table->double('gross_profit')->nullable();
            $table->double('selling_expense')->nullable();
            $table->double('ga_expense')->nullable();
            $table->double('net_income')->nullable();
            $table->double('cfo')->nullable();
            
            // Beneish Indices & M-Score
            $table->double('dsri')->nullable();
            $table->double('gmi')->nullable();
            $table->double('aqi')->nullable();
            $table->double('sgi')->nullable();
            $table->double('lvgi')->nullable();
            $table->double('depi')->nullable();
            $table->double('sgai')->nullable();
            $table->double('tata')->nullable();
            $table->double('m_score')->nullable();
            $table->string('fraud_flag', 50)->nullable();
            
            // Trend & Growth
            $table->double('revenue_growth')->nullable();
            $table->double('asset_growth')->nullable();
            $table->double('net_income_growth_assets')->nullable();
            
            // CFO Quality
            $table->double('cfo_to_net_income')->nullable();
            $table->string('cfo_quality_flag', 50)->nullable();
            
            // Anomaly
            $table->double('anomaly_score_05')->nullable();
            
            // Narrative Features
            $table->double('sentiment')->nullable();
            $table->double('risk_words')->nullable();
            $table->double('readability')->nullable();
            $table->double('text_length')->nullable();
            
            // Risk & Fraud Scores
            $table->double('narrative_risk_score')->nullable();
            $table->double('financial_risk_score')->nullable();
            $table->double('combined_fraud_score')->nullable();
            $table->string('combined_fraud_status', 50)->nullable();
            
            // Weak Label Status
            $table->integer('weak_score')->nullable();
            $table->integer('weak_label')->nullable();
            $table->integer('weak_label_t3')->nullable();
            $table->integer('weak_label_t2')->nullable();
            
            $table->timestamps();
            
            // Indexes for fast searching and filtering
            $table->unique(['kode', 'tahun']);
            $table->index('sektor');
            $table->index('combined_fraud_status');
            $table->index('weak_label_t3');
            $table->index('weak_label_t2');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('ews_records');
    }
};
