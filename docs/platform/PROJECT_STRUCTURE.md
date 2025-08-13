# Nexus Project Structure

## Overview

This document describes the organized folder structure of the Nexus platform, designed for scalability and maintainability.

## 📁 Root Structure

```
Nexus/
├── README.md                    # Main project overview
├── .cursor/                     # Cursor IDE configuration
├── docs/                        # 📚 Documentation
├── scripts/                     # 🔧 Scripts and utilities
├── services/                    # 🏗️ Platform services
├── iac/                         # 🏗️ Infrastructure as Code
├── kind-config-persistent.yaml  # Kind cluster configuration
└── values-observability.yaml    # Helm values for monitoring
```

## 📚 Documentation (`docs/`)

All project documentation is centralized in the `docs/` folder:

```
docs/
├── README.md                    # Detailed setup and usage guide
├── ROLE_BASED_ACCESS.md         # RBAC system documentation
├── PORT_CHANGE.md              # Port configuration details
├── PROJECT_STRUCTURE.md        # This file
└── developer guide             # Development guidelines
```

### Documentation Guidelines
- **README.md** - Main documentation with setup instructions
- **Feature-specific docs** - Separate files for complex features
- **Developer guide** - Guidelines for contributors
- **Structure docs** - This file and similar organizational docs

## 🔧 Scripts (`scripts/`)

All utility scripts are organized in the `scripts/` folder:

```
scripts/
├── start-dashboard.sh          # Start unified dashboard
├── access-services.sh          # Access individual services
└── verify-setup.sh             # Verify platform setup
```

### Script Guidelines
- **Descriptive names** - Clear purpose from filename
- **Executable permissions** - All scripts are executable
- **Error handling** - Proper error checking and user feedback
- **Documentation** - Comments explaining functionality

## 🏗️ Services (`services/`)

Each platform service has its own directory:

```
services/
├── admin-dashboard-service/     # Main admin dashboard
│   ├── src/                    # Application source code
│   ├── kubernetes/             # K8s manifests
│   ├── tests/                  # Test files
│   ├── Dockerfile              # Container configuration
│   ├── requirements.txt        # Python dependencies
│   ├── admin-rbac.yaml         # RBAC configuration
│   └── test-service.yaml       # Test service
└── [future-services]/          # Additional services
```

### Service Guidelines
- **Self-contained** - Each service has all its files
- **Standard structure** - Consistent layout across services
- **Kubernetes manifests** - In `kubernetes/` subdirectory
- **Configuration** - Service-specific configs in service directory

## 🏗️ Infrastructure as Code (`iac/`)

Future infrastructure configurations:

```
iac/
├── kubernetes/                 # K8s configurations
│   ├── base/                   # Base configurations
│   ├── overlays/               # Environment overlays
│   └── charts/                 # Custom Helm charts
└── terraform/                  # Terraform configurations
    ├── modules/                # Reusable modules
    ├── environments/           # Environment-specific configs
    └── variables/              # Variable definitions
```

## 📋 File Organization Principles

### 1. **Separation of Concerns**
- **Documentation** → `docs/`
- **Scripts** → `scripts/`
- **Services** → `services/`
- **Infrastructure** → `iac/`

### 2. **Scalability**
- **Easy to add new services** - Just create new directory in `services/`
- **Easy to add new scripts** - Place in `scripts/`
- **Easy to add new docs** - Place in `docs/`

### 3. **Maintainability**
- **Clear structure** - Easy to find files
- **Consistent naming** - Predictable file locations
- **Logical grouping** - Related files together

### 4. **Team Collaboration**
- **Clear ownership** - Each service is self-contained
- **Easy onboarding** - Clear structure for new team members
- **Reduced conflicts** - Separate directories for different concerns

## 🚀 Adding New Components

### Adding a New Service
```bash
# 1. Create service directory
mkdir -p services/new-service

# 2. Create standard structure
mkdir -p services/new-service/{src,kubernetes,tests}

# 3. Add service files
touch services/new-service/{Dockerfile,requirements.txt,README.md}

# 4. Add to main README.md
# Update the services section
```

### Adding a New Script
```bash
# 1. Create script in scripts/
touch scripts/new-script.sh

# 2. Make executable
chmod +x scripts/new-script.sh

# 3. Add to main README.md
# Update the scripts section
```

### Adding New Documentation
```bash
# 1. Create doc in docs/
touch docs/NEW_FEATURE.md

# 2. Add to main README.md
# Update the documentation section
```

## 📊 Benefits of This Structure

### **For Developers**
- **Easy navigation** - Know exactly where to find files
- **Clear ownership** - Each service is self-contained
- **Reduced conflicts** - Separate concerns

### **For Operations**
- **Easy deployment** - Clear service boundaries
- **Simple monitoring** - Service-specific configurations
- **Quick troubleshooting** - Organized logs and configs

### **For Management**
- **Clear project structure** - Easy to understand scope
- **Scalable organization** - Can grow without chaos
- **Team collaboration** - Clear areas of responsibility

## 🔄 Migration Notes

### **What Changed**
- **Documentation moved** → `docs/` folder
- **Scripts moved** → `scripts/` folder
- **Services organized** → `services/` folder
- **Admin dashboard** → `services/admin-dashboard-service/`

### **Updated Commands**
```bash
# Old
./start-dashboard.sh

# New
./scripts/start-dashboard.sh
```

### **Updated Paths**
```bash
# Old
kubectl apply -f admin-rbac.yaml

# New
kubectl apply -f services/admin-dashboard-service/admin-rbac.yaml
```

## 🎯 Best Practices

### **File Naming**
- **Use descriptive names** - `start-dashboard.sh` not `start.sh`
- **Use consistent casing** - kebab-case for files, camelCase for variables
- **Include extensions** - `.md` for docs, `.sh` for scripts

### **Directory Structure**
- **Keep it flat** - Don't nest too deeply
- **Group logically** - Related files together
- **Be consistent** - Same structure across similar components

### **Documentation**
- **Update README.md** - When adding new components
- **Keep docs current** - Update when features change
- **Use clear language** - Write for new team members

This organized structure ensures the Nexus platform can scale efficiently while remaining maintainable and easy to understand.
