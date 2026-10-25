"""
DocuVault — UI Component Modules
Exports Onboarding Carousel, Login & Registration Dialog, User Profile Drawer,
and Pro Tier Upgrade Modal.
"""

from ui.components.onboarding import OnboardingDialog
from ui.components.login_dialog import LoginDialog, EmbeddedAuthWidget
from ui.components.profile_dialog import ProfileDialog
from ui.components.upgrade_modal import UpgradeModal
from ui.components.startup_splash import StartupSplashDialog, StartupShowcaseWidget

__all__ = [
    "OnboardingDialog",
    "LoginDialog",
    "EmbeddedAuthWidget",
    "ProfileDialog",
    "UpgradeModal",
    "StartupSplashDialog",
    "StartupShowcaseWidget",
]


