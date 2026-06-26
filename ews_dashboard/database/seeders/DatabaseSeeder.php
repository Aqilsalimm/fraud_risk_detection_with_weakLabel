<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;

class DatabaseSeeder extends Seeder
{
    use WithoutModelEvents;

    /**
     * Seed the application's database.
     */
    public function run(): void
    {
        // Create an admin user
        User::updateOrCreate(
            ['email' => 'admin@ews.com'],
            [
                'name' => 'Administrator EWS',
                'password' => Hash::make('password'),
            ]
        );

        // Load and run the EWS SQL data
        $sqlPath = database_path('seeders/ews_data.sql');
        if (file_exists($sqlPath)) {
            $this->command->info("Loading EWS data from SQL file...");
            DB::unprepared(file_get_contents($sqlPath));
            $this->command->info("EWS data successfully seeded!");
        } else {
            $this->command->error("EWS SQL file not found at: " . $sqlPath);
        }
    }
}
