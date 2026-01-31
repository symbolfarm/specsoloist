import warnings

# Warn user upon import
warnings.warn(
    "The 'specular-ai' package has been renamed to 'specsoloist'. "
    "Please uninstall 'specular-ai' and install 'specsoloist' directly to receive future updates.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export key components from specsoloist if installed, 
# so 'from specular import SpecularCore' might still work if they have the new package.
# This provides a "soft" landing.
try:
    from specsoloist import SpecSoloistCore as SpecularCore
    from specsoloist import SpecSoloistConfig as SpecularConfig
    __all__ = ["SpecularCore", "SpecularConfig"]
except ImportError:
    pass
