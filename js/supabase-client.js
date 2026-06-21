// js/supabase-client.js
// Supabase Frontend Configuration
const SUPABASE_URL = "https://kpynymwghfwshvcvevxq.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtweW55bXdnaGZ3c2h2Y3ZldnhxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkwNDAwMTksImV4cCI6MjA5NDYxNjAxOX0.skNy5PKg0oFIqZD-2GyMZFTVA68OxrS1rBKkFiWAhwA";

// Initialize Supabase client
window.supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
