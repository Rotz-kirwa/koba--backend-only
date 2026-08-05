# Admin Management System

## Overview
The Queen Koba admin dashboard now includes a comprehensive admin management system that allows super admins to manage other admin users.

## User Roles

### Super Admin
- **Full Access**: Can perform all operations
- **Admin Management**: Can add, edit, suspend, and remove other admins
- **Cannot be suspended**: Super admin accounts cannot be suspended
- **Permissions**: `['*']` (all permissions)

### Admin
- **Limited Access**: Can perform most operations except admin management
- **Cannot access**: Admin Management page
- **Can be suspended**: Super admins can suspend admin accounts
- **Permissions**: `['read', 'write']` (configurable)

## Features

### 1. Add New Admins
- Create new admin or super admin accounts
- Set email, password, and role
- Assign permissions

### 2. Edit Admins
- Update admin details (name, email, role)
- Change passwords
- Modify permissions

### 3. Suspend Admins
- Temporarily disable admin accounts
- Suspended admins cannot log in
- Can be reactivated by super admin

### 4. Remove Admins
- Permanently delete admin accounts
- Super admins cannot be deleted

## Setup

### 1. Create Super Admin
Run the seed script to create the initial super admin:

```bash
cd backend/queen-koba-backend
python3 seed_admin.py
```

Or reset the super admin:

```bash
python3 reset_admin.py
```

**Default Credentials:**
- Email: `admin@queenkoba.com`
- Password: `admin123`
- Role: `super_admin`

### 2. Access Admin Management
1. Log in as super admin
2. Navigate to "Admins" in the sidebar
3. Click "Add Admin" to create new admin users

## API Endpoints

### Get All Admins
```
GET /admin/admins
Authorization: Bearer <token>
```

### Create Admin
```
POST /admin/admins
Authorization: Bearer <token>
Body: {
  "full_name": "John Doe",
  "email": "john@queenkoba.com",
  "password": "password123",
  "role": "admin",
  "permissions": ["read", "write"]
}
```

### Update Admin
```
PUT /admin/admins/<admin_id>
Authorization: Bearer <token>
Body: {
  "full_name": "John Doe Updated",
  "email": "john@queenkoba.com",
  "role": "admin",
  "permissions": ["read", "write"],
  "password": "newpassword" (optional)
}
```

### Update Admin Status
```
PUT /admin/admins/<admin_id>/status
Authorization: Bearer <token>
Body: {
  "status": "suspended" | "active"
}
```

### Delete Admin
```
DELETE /admin/admins/<admin_id>
Authorization: Bearer <token>
```

## Security Features

1. **Role-Based Access Control**: Only super admins can access admin management
2. **Password Hashing**: All passwords are hashed using bcrypt
3. **JWT Authentication**: Secure token-based authentication
4. **Status Checking**: Suspended accounts cannot log in
5. **Protected Super Admins**: Super admin accounts cannot be suspended or deleted

## Usage Examples

### Creating a Regular Admin
1. Log in as super admin
2. Go to Admins page
3. Click "Add Admin"
4. Fill in details:
   - Full Name: "Jane Smith"
   - Email: "jane@queenkoba.com"
   - Password: "secure123"
   - Role: "Admin"
5. Click "Create"

### Suspending an Admin
1. Find the admin in the list
2. Click the status badge (Active/Suspended)
3. Status will toggle between active and suspended

### Editing an Admin
1. Click the edit icon next to the admin
2. Update the details
3. Click "Update"

## Permissions System

The system supports granular permissions:
- `*`: All permissions (super admin only)
- `read`: View-only access
- `write`: Can create and update
- `delete`: Can delete items
- Custom permissions can be added as needed

## Best Practices

1. **Change Default Password**: Always change the default super admin password after first login
2. **Limit Super Admins**: Only create super admin accounts when absolutely necessary
3. **Regular Audits**: Periodically review admin accounts and remove unused ones
4. **Strong Passwords**: Enforce strong password policies for all admin accounts
5. **Suspend Instead of Delete**: Consider suspending accounts instead of deleting them for audit trails

## Troubleshooting

### Cannot Access Admin Management
- Ensure you're logged in as a super admin
- Check that your role is set to `super_admin` in the database

### Forgot Super Admin Password
Run the reset script:
```bash
python3 reset_admin.py
```

### Admin Cannot Log In
- Check if the account is suspended
- Verify the email and password are correct
- Ensure the role is set to `admin` or `super_admin`
