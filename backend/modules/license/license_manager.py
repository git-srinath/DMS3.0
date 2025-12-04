import os
import json
from datetime import datetime
import getmac

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.key_gen import LicenseKeyGenerator, get_system_identifier
    from backend.modules.logger import logger, info, warning, error
except ImportError:  # When running Flask app.py directly inside backend
    from key_gen import LicenseKeyGenerator, get_system_identifier  # type: ignore
    from modules.logger import logger, info, warning, error  # type: ignore

class LicenseManager:
    def __init__(self):
        # Use absolute paths in the backend directory
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.license_file = os.path.join(self.base_dir, "license.key")
        self.secret_key_file = os.path.join(self.base_dir, "secret.key")
        self._load_secret_key()
        self.generator = LicenseKeyGenerator(self.secret_key)
        self.system_id = get_system_identifier()
        info(f"License Manager initialized with system ID: {self.system_id}")
        
    def _load_secret_key(self):
        """Load or generate secret key"""
        try:
            if os.path.exists(self.secret_key_file):
                info(f"Loading secret key from: {self.secret_key_file}")
                with open(self.secret_key_file, 'rb') as f:
                    self.secret_key = f.read()
            else:
                info("No secret key found, generating new one")
                try:
                    from backend.key_gen import generate_secret_key
                except ImportError:
                    from key_gen import generate_secret_key  # type: ignore
                self.secret_key = generate_secret_key()
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.secret_key_file), exist_ok=True)
                with open(self.secret_key_file, 'wb') as f:
                    f.write(self.secret_key)
                info(f"New secret key saved to: {self.secret_key_file}")
        except Exception as e:
            error(f"Error loading secret key: {str(e)}")
            try:
                from backend.key_gen import generate_secret_key
            except ImportError:
                from key_gen import generate_secret_key  # type: ignore
            self.secret_key = generate_secret_key()

    def get_license_status(self):
        """Get current license status"""
        try:
            if not os.path.exists(self.license_file):
                warning(f"No license file found at: {self.license_file}")
                return {
                    "status": "inactive",
                    "message": "No license key found",
                    "valid": False,
                    "system_id": self.system_id
                }

            info(f"Reading license from: {self.license_file}")
            with open(self.license_file, 'r') as f:
                license_key = f.read().strip()
            
            info(f"Validating license with system ID: {self.system_id}")
            is_valid, result = self.generator.validate_license_key(license_key, self.system_id)
            
            if is_valid:
                info("License validation successful")
                return {
                    "status": "active",
                    "message": "License is valid",
                    "valid": True,
                    "expires": result["valid_until"],
                    "features": result["features"],
                    "system_id": result["system_id"]
                }
            else:
                warning(f"License validation failed: {result}")
                return {
                    "status": "invalid",
                    "message": result,
                    "valid": False,
                    "system_id": self.system_id
                }
                
        except Exception as e:
            error(f"Error checking license status: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "valid": False,
                "system_id": self.system_id
            }

    def activate_license(self, license_key):
        """Activate a new license key"""
        try:
            info(f"Activating license with system ID: {self.system_id}")
            info(f"License key (first 20 chars): {license_key[:20] if license_key else 'None'}...")
            
            # Strip whitespace from license key
            license_key = license_key.strip()
            
            is_valid, result = self.generator.validate_license_key(license_key, self.system_id)
            
            if not is_valid:
                error(f"License validation failed during activation: {result}")
                return False, result
            
            info("License validation successful, saving license file")
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.license_file), exist_ok=True)
                
            # Save the license key
            with open(self.license_file, 'w') as f:
                f.write(license_key)
                
            info(f"License key saved to: {self.license_file}")
            return True, "License activated successfully"
            
        except Exception as e:
            error(f"Error activating license: {str(e)}", exc_info=True)
            return False, f"Failed to activate license: {str(e)}"

    def deactivate_license(self):
        """Remove the current license"""
        try:
            if os.path.exists(self.license_file):
                info(f"Removing license file: {self.license_file}")
                os.remove(self.license_file)
            return True, "License deactivated successfully"
        except Exception as e:
            error(f"Error deactivating license: {str(e)}")
            return False, f"Failed to deactivate license: {str(e)}" 