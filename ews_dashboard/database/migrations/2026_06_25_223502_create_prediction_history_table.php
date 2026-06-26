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
        Schema::create('prediction_history', function (Blueprint $table) {
            $table->id();
            $table->string('company_name');
            $table->string('kode', 10)->nullable();
            $table->integer('year');
            $table->double('fraud_probability');
            $table->string('risk_level');
            $table->integer('prediction'); // 0 or 1
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('prediction_history');
    }
};
