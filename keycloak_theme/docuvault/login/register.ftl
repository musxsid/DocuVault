<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocuVault — Create Free Account</title>
    <link rel="stylesheet" href="${url.resourcesPath}/css/docuvault.css">
</head>
<body>
    <div class="login-card">
        <div class="brand-header">
            <div class="brand-logo">&#x1F6E1;</div>
            <h1 class="brand-title">Join DocuVault</h1>
            <p class="brand-subtitle">Worldwide Free Trial Plan with Instant Access</p>
        </div>

        <form id="kc-register-form" action="${url.registrationAction}" method="post">
            <div class="form-group">
                <label for="firstName" class="form-label">Full Name</label>
                <input type="text" id="firstName" class="form-input" name="firstName" value="${(register.formData.firstName!'')}" placeholder="Alex Rivera" required />
            </div>

            <div class="form-group">
                <label for="email" class="form-label">Email Address</label>
                <input type="email" id="email" class="form-input" name="email" value="${(register.formData.email!'')}" placeholder="alex@domain.com" autocomplete="email" required />
            </div>

            <div class="form-group">
                <label for="password" class="form-label">Password</label>
                <input type="password" id="password" class="form-input" name="password" autocomplete="new-password" placeholder="••••••••" required />
            </div>

            <div class="form-group">
                <label for="password-confirm" class="form-label">Confirm Password</label>
                <input type="password" id="password-confirm" class="form-input" name="password-confirm" placeholder="••••••••" required />
            </div>

            <button class="btn-primary" type="submit">Create Free Account</button>
        </form>

        <div class="footer-links">
            Already have an account? <a href="${url.loginUrl}">Sign In</a>
        </div>
    </div>
</body>
</html>
