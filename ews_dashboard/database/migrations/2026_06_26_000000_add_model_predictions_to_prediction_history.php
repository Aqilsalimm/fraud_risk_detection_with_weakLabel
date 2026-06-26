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
        Schema::table('prediction_history', function (Blueprint $table) {
            $table->double('model_b_probability')->nullable();
            $table->integer('model_b_prediction')->nullable();
            $table->double('model_a_probability')->nullable();
            $table->integer('model_a_prediction')->nullable();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('prediction_history', function (Blueprint $table) {
            $table->dropColumn([
                'model_b_probability',
                'model_b_prediction',
                'model_a_probability',
                'model_a_prediction'
            ]);
        });
    }
};
