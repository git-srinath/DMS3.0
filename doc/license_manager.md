# License Management System Documentation

## Overview
This document provides a comprehensive guide to the license management system implemented in the Data Warehouse Tool application. The system uses a combination of hardware-based identification, encryption, and token-based authentication to ensure secure license management.

## Tech Stack
- **Backend**: Python Flask
- **Frontend**: React/Next.js
- **Authentication**: JWT (JSON Web Tokens)
- **Encryption**: Fernet (symmetric encryption)
- **Database**: SQLite/PostgreSQL
- **Key Storage**: File-based (.key files)

## System Components

### 1. Backend Components
- `backend/key_gen.py`: License key generation and validation
- `backend/license_manager.py`: License management and status tracking
- `backend/app.py`: API endpoints for license operations

### 2. Frontend Components
- `frontend/src/components/LicenseValidation.jsx`: License validation UI
- `frontend/src/app/context/AuthContext.js`: License state management
- `frontend/src/components/LayoutWrapper.js`: Application layout with license check

## License Generation

### System Identifier Generation
```python
def get_system_identifier():
    """Get unique system identifier based on MAC address"""
    mac = getmac.get_mac_address()
    return mac.replace(':', '')
```

### License Key Structure
The license key is a JSON object encrypted using Fernet encryption:
```json
{
    "created_at": "ISO timestamp",
    "valid_until": "ISO timestamp",
    "features": ["basic", "advanced", "premium"],
    "license_id": "UUID",
    "system_id": "MAC address without colons"
}
```

### License Generation Process
1. Generate a secret key (if not exists):
   ```python
   from cryptography.fernet import Fernet
   secret_key = Fernet.generate_key()
   ```

2. Create license data:
   ```python
   license_data = {
       "created_at": datetime.now().isoformat(),
       "valid_until": (datetime.now() + timedelta(days=365)).isoformat(),
       "features": ["basic", "advanced", "premium"],
       "license_id": str(uuid.uuid4()),
       "system_id": system_id
   }
   ```

3. Encrypt license data:
   ```python
   fernet = Fernet(secret_key)
   encrypted_data = fernet.encrypt(json.dumps(license_data).encode())
   license_key = base64.urlsafe_b64encode(encrypted_data).decode()
   ```

## License Validation

### Validation Process
1. Decode license key from base64
2. Decrypt using Fernet
3. Validate system ID matches
4. Check expiration date
5. Verify features

### Validation Code Example
```python
def validate_license_key(self, license_key, system_id):
    try:
        encrypted_data = base64.urlsafe_b64decode(license_key)
        decrypted_data = self.fernet.decrypt(encrypted_data)
        license_data = json.loads(decrypted_data)
        
        if license_data.get('system_id') != system_id:
            return False, "License key is not valid for this system"
        
        valid_until = datetime.fromisoformat(license_data['valid_until'])
        if valid_until < datetime.now():
            return False, "License has expired"
        
        return True, license_data
    except Exception as e:
        return False, f"Invalid license key: {str(e)}"
```

## API Endpoints

### 1. License Status Check
```http
GET /api/license/status
Response: {
    "status": "active|inactive|invalid",
    "message": "Status message",
    "valid": boolean,
    "expires": "ISO timestamp",
    "features": ["feature1", "feature2"]
}
```

### 2. License Activation (Admin only)
```http
POST /api/admin/license/activate
Headers: {
    "Authorization": "Bearer {token}"
}
Body: {
    "license_key": "encrypted_license_key"
}
Response: {
    "success": boolean,
    "message": "Status message"
}
```

### 3. License Deactivation (Admin only)
```http
POST /api/admin/license/deactivate
Headers: {
    "Authorization": "Bearer {token}"
}
Response: {
    "success": boolean,
    "message": "Status message"
}
```

## Frontend Implementation

### License Status Management
The application uses React Context to manage license state:
```javascript
const AuthContext = createContext({
    licenseStatus: null,
    checkLicenseStatus: () => {},
});
```

### License Status Storage
License status is stored in:
1. React state (runtime)
2. localStorage (persistence)
3. AuthContext (global access)

### License Check Flow
1. Initial login:
   ```javascript
   const login = async (username, password) => {
       // ... authentication logic ...
       await checkLicenseStatus();
   };
   ```

2. Application initialization:
   ```javascript
   useEffect(() => {
       const initializeAuth = async () => {
           const storedLicenseStatus = localStorage.getItem('licenseStatus');
           if (storedLicenseStatus) {
               setLicenseStatus(JSON.parse(storedLicenseStatus));
           }
       };
       initializeAuth();
   }, []);
   ```

## Security Measures

### 1. Hardware Binding
- License keys are bound to specific hardware using MAC addresses
- Prevents license sharing between different systems

### 2. Encryption
- Uses Fernet symmetric encryption
- Secret key stored securely on the server
- License keys are base64 encoded for transmission

### 3. Authentication
- Admin-only endpoints protected by JWT authentication
- Token validation on every admin request
- Role-based access control for license management

### 4. Storage Security
- Secret key stored in separate file
- License key stored encrypted
- Sensitive data not exposed in logs

## Development Setup

### 1. Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Generate initial secret key
python -c "from key_gen import generate_secret_key; print(generate_secret_key())"
```

### 2. Frontend Setup
```bash
# Install dependencies
npm install

# Set environment variables
cp .env.example .env.local
# Edit .env.local with appropriate values
```

### 3. Required Environment Variables
```env
NEXT_PUBLIC_API_URL=http://localhost:5000
SECRET_KEY_FILE=backend/secret.key
LICENSE_FILE=backend/license.key
```

## License Generation Tool

### Command Line Tool
```python
# generate_license.py
from key_gen import LicenseKeyGenerator
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--system-id', required=True)
    parser.add_argument('--days', type=int, default=365)
    parser.add_argument('--features', nargs='+', default=['basic'])
    args = parser.parse_args()

    generator = LicenseKeyGenerator()
    license_key = generator.generate_license_key(
        system_id=args.system_id,
        days_valid=args.days,
        features=args.features
    )
    print(f"Generated License Key:\n{license_key}")

if __name__ == '__main__':
    main()
```

Usage:
```bash
python generate_license.py --system-id 001122334455 --days 365 --features basic advanced premium
```

## Troubleshooting

### Common Issues

1. Invalid License Key
   - Check system ID matches
   - Verify key hasn't been tampered with
   - Ensure secret key is correct

2. License Validation Fails
   - Check license expiration
   - Verify system ID matches
   - Check for encryption/decryption errors

3. Admin Access Issues
   - Verify JWT token is valid
   - Check user has admin role
   - Ensure proper authorization headers

### Debug Logging
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('license_manager')
```

## Best Practices

1. License Key Management
   - Generate unique keys per system
   - Store keys securely
   - Implement proper error handling

2. Security
   - Regular secret key rotation
   - Secure storage of keys
   - Input validation
   - Rate limiting on API endpoints

3. User Experience
   - Clear error messages
   - Grace period for expired licenses
   - Easy license activation process

## Testing

### Unit Tests
```python
def test_license_validation():
    generator = LicenseKeyGenerator()
    system_id = "001122334455"
    
    # Generate test license
    license_key = generator.generate_license_key(system_id)
    
    # Test validation
    is_valid, result = generator.validate_license_key(license_key, system_id)
    assert is_valid
    assert result['system_id'] == system_id
```

### Integration Tests
```python
def test_license_activation_api():
    response = client.post('/api/admin/license/activate', 
        json={'license_key': 'test_key'},
        headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    assert response.json['success']
```

## Detailed License Key Generation and Validation Process

### License Key Generation Workflow

1. **System Information Collection**
   - When a customer requests a license, their system's MAC address is collected
   - The MAC address is sanitized by removing colons to create a unique system identifier
   - This system identifier ensures the license is tied to specific hardware

2. **License Data Preparation**
   - A unique license ID (UUID) is generated to track the license
   - The creation timestamp is recorded in ISO format
   - The expiration date is calculated based on the license duration (e.g., 365 days)
   - Features are assigned based on the purchased license tier (basic, advanced, premium)
   - All this information is combined with the system identifier

3. **Encryption Process**
   - A secret key is used for encryption (stored securely on the license generation server)
   - The license data is converted to a JSON string
   - The JSON string is encrypted using Fernet symmetric encryption
   - The encrypted data is encoded in base64 format for safe transmission
   - The resulting string is the license key provided to the customer

4. **License Key Distribution**
   - The generated license key is stored in the license management database
   - A copy is provided to the customer through a secure channel
   - The customer receives instructions for activating the license

### License Key Validation Workflow

1. **Initial Validation**
   - When a license key is submitted for activation, the system first checks if it's properly formatted
   - The system verifies that the key is a valid base64-encoded string
   - Basic format validation helps prevent unnecessary decryption attempts

2. **Decryption Process**
   - The system decodes the base64 string
   - Using the same secret key used for generation, it attempts to decrypt the data
   - If decryption fails, the license is immediately marked as invalid
   - Successful decryption yields the original JSON data

3. **Hardware Verification**
   - The system extracts the current machine's MAC address
   - The MAC address is processed in the same way as during generation
   - This system identifier is compared with the one in the license data
   - Any mismatch indicates the license is being used on an unauthorized system

4. **Temporal Validation**
   - The system checks the license creation date to ensure it's not from the future
   - The expiration date is compared with the current time
   - If the license has expired, it's marked as invalid but may enter a grace period
   - The validation system accounts for timezone differences

5. **Feature Verification**
   - The system checks which features are included in the license
   - It verifies that the features match the expected tier
   - The feature list is used to enable/disable specific application functionality
   - Any attempt to access unauthorized features is blocked

6. **Continuous Validation**
   - The license status is checked during application startup
   - Periodic validation ensures the license hasn't been revoked
   - The system maintains a cache of the license status to prevent frequent checks
   - Failed validations trigger appropriate user notifications

7. **Security Measures**
   - All validation attempts are logged for security monitoring
   - Failed validations are rate-limited to prevent brute force attacks
   - The system detects and blocks attempts to tamper with the license data
   - Validation results are digitally signed to prevent manipulation

8. **Error Handling**
   - Each validation step has specific error messages
   - Users receive clear instructions on how to resolve license issues
   - Administrators can view detailed validation logs
   - The system provides grace periods for expired licenses

9. **License Management**
   - Administrators can revoke licenses if necessary
   - License transfers to new hardware require admin approval
   - The system maintains an audit trail of all license operations
   - Regular backups of license data are maintained

10. **User Experience**
    - Users receive notifications before license expiration
    - The system provides clear status indicators
    - License renewal process is streamlined
    - Automatic license activation reduces user intervention

This comprehensive validation process ensures that licenses are properly enforced while maintaining a good user experience. The system is designed to be secure against common attack vectors while remaining flexible enough to handle legitimate use cases like hardware upgrades or system migrations. 