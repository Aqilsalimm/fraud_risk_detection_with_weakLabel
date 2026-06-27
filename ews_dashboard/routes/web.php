<?php

use App\Http\Controllers\ProfileController;
use App\Http\Controllers\EwsController;
use Illuminate\Foundation\Application;
use Illuminate\Support\Facades\Route;
use Inertia\Inertia;

Route::get('/', function () {
    return Inertia::render('Welcome', [
        'canLogin' => Route::has('login'),
        'canRegister' => Route::has('register'),
        'laravelVersion' => Application::VERSION,
        'phpVersion' => PHP_VERSION,
    ]);
});

Route::middleware(['auth', 'verified'])->group(function () {
    Route::get('/dashboard', [EwsController::class, 'index'])->name('dashboard');
    Route::get('/ews/check-lag', [EwsController::class, 'checkLag'])->name('ews.check-lag');
    Route::get('/ews/{id}', [EwsController::class, 'show'])->name('ews.show');
    Route::get('/ews/{id}/export', [EwsController::class, 'export'])->name('ews.export');
    
    // Prediction History & Upload
    Route::get('/prediction-history', [EwsController::class, 'history'])->name('prediction.history');
    Route::get('/upload-predict', [EwsController::class, 'uploadForm'])->name('prediction.upload');
    Route::post('/upload-predict', [EwsController::class, 'processUploadPredict'])->name('prediction.process');
});

Route::middleware('auth')->group(function () {
    Route::get('/profile', [ProfileController::class, 'edit'])->name('profile.edit');
    Route::patch('/profile', [ProfileController::class, 'update'])->name('profile.update');
    Route::delete('/profile', [ProfileController::class, 'destroy'])->name('profile.destroy');
});

require __DIR__.'/auth.php';
