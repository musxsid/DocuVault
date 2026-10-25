<#import "template.ftl" as layout>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocuVault — Enterprise Sign In</title>
    <link rel="stylesheet" href="${url.resourcesPath}/css/docuvault.css">
</head>
<body>
    <div class="login-card">
        <div class="brand-header">
            <div class="brand-logo">&#x1F6E1;</div>
            <h1 class="brand-title">DocuVault</h1>
            <p class="brand-subtitle">Offline-First Document Intelligence & Cryptographic Verifier</p>
        </div>

        <form id="kc-form-login" onsubmit="login.disabled = true; return true;" action="${url.loginAction}" method="post">
            <div class="form-group">
                <label for="username" class="form-label">Email or Username</label>
                <input tabindex="1" id="username" class="form-input" name="username" value="${(login.username!'')}" type="text" autofocus autocomplete="username" placeholder="name@domain.com" required />
            </div>

            <div class="form-group">
                <label for="password" class="form-label">Password</label>
                <input tabindex="2" id="password" class="form-input" name="password" type="password" autocomplete="current-password" placeholder="••••••••" required />
            </div>

            <button tabindex="3" class="btn-primary" name="login" id="kc-login" type="submit">Sign In</button>
        </form>

        <div class="divider">or continue with</div>

        <a href="${url.loginAction}?kc_idp_hint=google" class="btn-social">
            <svg width="18" height="18" viewBox="0 0 18 18"><path fill="#4285F4" d="M17.64 9.2c0-.63-.06-1.25-.16-1.84H9v3.49h4.84a4.14 4.14 0 0 1-1.8 2.71v2.26h2.92c1.71-1.57 2.68-3.88 2.68-6.62z"/><path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.91-2.26c-.8.54-1.83.86-3.05.86-2.34 0-4.33-1.58-5.04-3.71H.95v2.33C2.43 15.89 5.48 18 9 18z"/><path fill="#FBBC05" d="M3.96 10.71c-.18-.54-.28-1.12-.28-1.71s.1-1.17.28-1.71V4.96H.95A8.996 8.996 0 0 0 0 9c0 1.45.35 2.82.95 4.04l3.01-2.33z"/><path fill="#EA4335" d="M9 3.58c1.32 0 2.51.45 3.44 1.35l2.58-2.59C13.46.89 11.43 0 9 0 5.48 0 2.43 2.11.95 4.96l3.01 2.33c.71-2.13 2.7-3.71 5.04-3.71z"/></svg>
            Sign in with Google
        </a>

        <div class="footer-links">
            Don't have an account? <a href="${url.registrationUrl}">Create Free Account</a>
        </div>
    </div>
</body>
</html>
