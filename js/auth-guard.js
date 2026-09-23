/**
 * Contexia Auth Guard — client-side session check for /app/* pages.
 *
 * This project deploys as a static site on Vercel (no Next.js build), so the
 * Edge Middleware in middleware.ts never executes. This script provides the
 * equivalent protection on the client side.
 *
 * HOW IT WORKS:
 * 1. Immediately hides the <body> to prevent flash of protected content.
 * 2. Loads the Supabase JS client (if not already loaded).
 * 3. Calls getSession() — if a valid session exists, reveals the page.
 * 4. If no session, redirects to /login.html with a ?next= param so the user
 *    can return after logging in.
 *
 * USAGE: Add this inside <head> of any protected page:
 *   <script src="/js/auth-guard.js"></script>
 *
 * The script is safe to include multiple times (idempotent).
 */
(function () {
  "use strict";

  // --- Config ---
  var SUPABASE_URL = "https://kpynymwghfwshvcvevxq.supabase.co";
  var SUPABASE_ANON_KEY =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtweW55bXdnaGZ3c2h2Y3ZldnhxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkwNDAwMTksImV4cCI6MjA5NDYxNjAxOX0.skNy5PKg0oFIqZD-2GyMZFTVA68OxrS1rBKkFiWAhwA";
  var LOGIN_PATH = "/login.html";

  // --- 1. Hide body immediately to prevent content flash ---
  var style = document.createElement("style");
  style.id = "cx-auth-guard-hide";
  style.textContent = "body { visibility: hidden !important; }";
  (document.head || document.documentElement).appendChild(style);

  // --- Helper: redirect to login ---
  function redirectToLogin() {
    var next = window.location.pathname + window.location.search;
    var url = LOGIN_PATH + "?next=" + encodeURIComponent(next);
    window.location.replace(url);
  }

  // --- Helper: reveal the page ---
  function revealPage() {
    var hideStyle = document.getElementById("cx-auth-guard-hide");
    if (hideStyle) hideStyle.remove();
  }

  // --- Helper: load Supabase JS if not already loaded ---
  function ensureSupabase(callback) {
    if (window.supabase && typeof window.supabase.createClient === "function") {
      callback();
      return;
    }
    var script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2";
    script.onload = callback;
    script.onerror = function () {
      // Can't load Supabase — fail open to avoid locking users out when CDN is down.
      // The page content is non-sensitive (dashboard UI without user data until API calls).
      console.warn("[auth-guard] Could not load Supabase SDK — failing open");
      revealPage();
    };
    (document.head || document.documentElement).appendChild(script);
  }

  // --- 2. Check session ---
  function checkAuth() {
    try {
      var client = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
      client.auth
        .getSession()
        .then(function (result) {
          var session =
            result && result.data && result.data.session;
          if (session && session.user) {
            // Valid session — reveal page
            revealPage();
          } else {
            // No session — redirect to login
            redirectToLogin();
          }
        })
        .catch(function () {
          // Error checking session — redirect to login for safety
          redirectToLogin();
        });
    } catch (e) {
      // Fatal error — redirect to login
      redirectToLogin();
    }
  }

  // --- 3. Run ---
  ensureSupabase(checkAuth);
})();
