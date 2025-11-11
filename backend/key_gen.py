import uuid
import hashlib
import hmac
import base64
import binascii
from datetime import datetime, timedelta
import json
from cryptography.fernet import Fernet
import getmac
import os
import argparse

def generate_secret_key():
    """Generate a secret key for Fernet encryption"""
    return Fernet.generate_key()

def get_system_identifier():
    """
    Get a unique and stable system identifier.
    It first tries to get the MAC address using uuid.getnode().
    If the returned address is randomly generated (multicast bit is set),
    it falls back to using the getmac library to find a real hardware address.
    """
    mac_int = uuid.getnode()
    # Check if the MAC address is randomly generated (multicast bit is set).
    if (mac_int >> 40) & 1:
        print("uuid.getnode() returned a random MAC address. Falling back to getmac.")
        mac_str = getmac.get_mac_address()
        if mac_str:
            print(f"Retrieved MAC address from getmac: {mac_str}")
            return mac_str.replace(':', '')

        print("getmac failed. Using the random MAC from uuid.getnode().")
        mac_hex = f'{mac_int:012x}'
        return mac_hex
    else:
        mac_hex = f'{mac_int:012x}'
        mac_str = ':'.join(mac_hex[i:i+2] for i in range(0, 12, 2))
        print(f"Retrieved MAC address from uuid.getnode(): {mac_str}")
        return mac_str.replace(':', '')

class LicenseKeyGenerator:
    def __init__(self, secret_key=None):
        if secret_key is None:
            self.secret_key = generate_secret_key()
        else:
            self.secret_key = secret_key
        self.fernet = Fernet(self.secret_key)
        
    def generate_license_key(self, system_id=None, days_valid=365, features=None):
        """Generate a new license key"""
        if features is None:
            features = ["basic"]
            
        if system_id is None:
            system_id = get_system_identifier()
            
        print(f"Generating license key for system ID: {system_id}")
            
        # Create license data
        license_data = {
            "created_at": datetime.now().isoformat(),
            "valid_until": (datetime.now() + timedelta(days=days_valid)).isoformat(),
            "features": features,
            "license_id": str(uuid.uuid4()),
            "system_id": system_id
        }
        
        print(f"License data being encrypted: {json.dumps(license_data, indent=2)}")
        
        # Convert to JSON and encrypt
        json_data = json.dumps(license_data)
        encrypted_data = self.fernet.encrypt(json_data.encode())
        
        # Encode to base64 for easier handling
        license_key = base64.urlsafe_b64encode(encrypted_data).decode()
        return license_key, license_data
    
    def validate_license_key(self, license_key, system_id):
        """Validate a license key"""
        try:
            print(f"\nValidating license key...")
            print(f"Provided system ID: {system_id}")
            
            # Normalize system IDs for comparison (strip, lowercase, remove colons/dashes)
            def normalize_system_id(sid):
                if not sid:
                    return ""
                # Convert to lowercase, remove whitespace, colons, dashes
                normalized = sid.lower().strip().replace(':', '').replace('-', '')
                return normalized
            
            normalized_current_id = normalize_system_id(system_id)
            
            # Strip whitespace from license key
            license_key = license_key.strip()
            
            # Decode from base64
            encrypted_data = base64.urlsafe_b64decode(license_key)
            
            # Decrypt the data
            decrypted_data = self.fernet.decrypt(encrypted_data)
            license_data = json.loads(decrypted_data)
            
            print(f"Decrypted license data: {json.dumps(license_data, indent=2)}")
            
            # Check system ID (normalized comparison)
            license_system_id = license_data.get('system_id', '')
            normalized_license_id = normalize_system_id(license_system_id)
            
            if normalized_license_id != normalized_current_id:
                print(f"System ID mismatch:")
                print(f"  License system ID (original): {license_system_id}")
                print(f"  License system ID (normalized): {normalized_license_id}")
                print(f"  Current system ID (original): {system_id}")
                print(f"  Current system ID (normalized): {normalized_current_id}")
                return False, f"License key is not valid for this system. License is for system: {license_system_id}, but current system is: {system_id}"
            
            # Check expiration
            valid_until = datetime.fromisoformat(license_data['valid_until'])
            if valid_until < datetime.now():
                print(f"License expired:")
                print(f"  Valid until: {valid_until}")
                print(f"  Current time: {datetime.now()}")
                return False, f"License has expired on {valid_until.strftime('%Y-%m-%d %H:%M:%S')}"
            
            print("License validation successful!")
            return True, license_data
            
        except (binascii.Error, ValueError) as e:
            print(f"Base64 decode error: {str(e)}")
            return False, f"Invalid license key format (base64 error): {str(e)}"
        except Exception as e:
            print(f"Error during license validation: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, f"Invalid license key: {str(e)}"

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate license key with specified validity period')
    parser.add_argument('--days', type=int, default=365, help='Number of days the license will be valid')
    parser.add_argument('--system-id', type=str, default=None, help='System ID to generate license for (defaults to current system)')
    args = parser.parse_args()
    
    # Load existing secret key if it exists, otherwise generate a new one
    secret_key_file = 'modules/license/secret.key'
    secret_key = None
    
    if os.path.exists(secret_key_file):
        print(f"Loading existing secret key from {secret_key_file}")
        with open(secret_key_file, 'rb') as f:
            secret_key = f.read()
    else:
        print(f"No existing secret key found. Generating new one...")
        secret_key = generate_secret_key()
        os.makedirs('modules/license', exist_ok=True)
        with open(secret_key_file, 'wb') as f:
            f.write(secret_key)
        print(f"New secret key saved to {secret_key_file}")
    
    # Get the system identifier (MAC address)
    if args.system_id:
        system_id = args.system_id
        print(f"Using provided system ID: {system_id}")
    else:
        system_id = get_system_identifier()
        print(f"Using current system ID: {system_id}")
    
    # Generate a new license key using the existing secret key
    generator = LicenseKeyGenerator(secret_key=secret_key)
    license_key, license_data = generator.generate_license_key(
        system_id=system_id,
        days_valid=args.days,
        features=["basic", "advanced", "premium"]
    )
    
    # Save the license key to a file in modules/license directory (optional)
    os.makedirs('modules/license', exist_ok=True)
    with open('modules/license/license.key', 'w') as f:
        f.write(license_key)
    
    # Print only the requested information
    print(f"\n=== License Key Generated Successfully ===")
    print(f"System MAC: {system_id}")
    print(f"License Key: {license_key}")
    print(f"Validation Key: {secret_key.decode()}")
    print(f"Number of Days: {args.days}")
    print(f"License ID: {license_data['license_id']}")
    print(f"Created Date: {datetime.fromisoformat(license_data['created_at']).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Valid Until: {datetime.fromisoformat(license_data['valid_until']).strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 