# 🚀 IGS Site Log Manager (SLM) - Systemd Deployment

This setup provides a **production-ready systemd service deployment** for the IGS Site Log Manager using Gunicorn and Nginx.

---

## 📋 Prerequisites

- Ubuntu/Debian Linux system
- PostgreSQL 16+ with PostGIS extension
- Python 3.13+ 
- [uv](https://docs.astral.sh/uv/) package manager
- nginx web server
- sudo access for systemd service installation

---

## 🚀 Installation Steps

### 1. Install System Dependencies

```bash
# Install PostgreSQL with PostGIS
sudo apt-get update
sudo apt-get install postgresql-16 postgresql-16-postgis-3 nginx

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Setup Database

```bash
# Create database and user
sudo -u postgres psql
CREATE USER slm_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE slm OWNER slm_user;
\c slm
CREATE EXTENSION postgis;
\q
```

### 3. Clone Repository and Setup Project

```bash
# Clone repository
git clone https://github.com/International-GNSS-Service/SLM.git
cd SLM/network

# Install dependencies with uv
uv sync --all-extras
```

### 4. Configure Production Environment

```bash
# Create production directory
sudo mkdir -p /var/www/network/production/{logs,media,static,secrets}
sudo chown -R $USER:www-data /var/www/network/production
chmod 775 /var/www/network/production

# Create production .env file
cat > /var/www/network/production/.env << 'EOF'
DEBUG=False
BASE_DIR=/var/www/network/production
SLM_ORG_NAME="Your Organization Name"
SLM_SITE_NAME="network.example.com"
DJANGO_SETTINGS_MODULE=sites.network.production
SECRET_KEY=your_secret_key_here
SLM_DATABASE=postgis://slm_user:your_secure_password@localhost:5432/slm
ALLOWED_HOSTS=network.example.com,192.168.8.252
EOF

chmod 600 /var/www/network/production/.env
```

### 5. Run Migrations and Collect Static Files

```bash
cd /home/roman/gitrepo/SLM/network
export SLM_ENV=/var/www/network/production/.env
export DJANGO_SETTINGS_MODULE=sites.network.production
export PYTHONPATH=/home/roman/gitrepo/SLM/network/src

# Run migrations
uv run python -m django migrate

# Collect static files
uv run python -m django collectstatic --noinput --clear

# Create superuser
uv run python -m django createsuperuser
```

### 6. Install Systemd Service

```bash
# Copy systemd service file
sudo cp /path/to/SLM/deploy/systemd/slm-network.service /etc/systemd/system/

# IMPORTANT: Edit the service file to match your paths
sudo nano /etc/systemd/system/slm-network.service

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable slm-network.service
sudo systemctl start slm-network.service

# Check service status
sudo systemctl status slm-network.service
```

### 7. Configure Nginx

Create nginx configuration `/etc/nginx/sites-available/slm-network`:

```nginx
server {
    listen 80;
    server_name network.example.com 192.168.8.252;

    # Allow large file uploads for SLM (geodetic data, photos, etc.)
    client_max_body_size 100M;

    location / {
        proxy_pass http://unix:/var/www/network/production/slm.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/network/production/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/network/production/media/;
        expires 1M;
        add_header Cache-Control "public";
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/slm-network /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔧 Service Management

### Basic Commands

```bash
# Start service
sudo systemctl start slm-network.service

# Stop service
sudo systemctl stop slm-network.service

# Restart service
sudo systemctl restart slm-network.service

# View status
sudo systemctl status slm-network.service

# View logs
sudo journalctl -u slm-network.service -n 100 --no-pager

# Follow logs in real-time
sudo journalctl -u slm-network.service -f
```

### Troubleshooting

If the service fails to start, check the logs:

```bash
# View detailed error messages
sudo journalctl -u slm-network.service -xe

# Common issues:
# 1. Missing PYTHONPATH - ensure it's set in the service file
# 2. Database connection - check SLM_DATABASE in .env
# 3. Permission issues - verify socket directory ownership
# 4. Module import errors - verify PYTHONPATH matches your repository structure
```

---

## 🔄 Updating the Application

```bash
# Navigate to repository
cd /home/roman/gitrepo/SLM

# Pull latest changes
git pull origin main

# Update dependencies
cd network
uv sync --all-extras

# Run migrations
export SLM_ENV=/var/www/network/production/.env
export DJANGO_SETTINGS_MODULE=sites.network.production
export PYTHONPATH=/home/roman/gitrepo/SLM/network/src
uv run python -m django migrate

# Collect static files
uv run python -m django collectstatic --noinput

# Restart service
sudo systemctl restart slm-network.service
```

---

## 🔐 Important Configuration Notes

### PYTHONPATH Requirement

The service file **must** include `PYTHONPATH` environment variable:

```ini
Environment="PYTHONPATH=/home/roman/gitrepo/SLM/network/src"
```

This is required for Django to properly import the application modules and load XSD schemas.

### User and Group

The service runs as the `roman` user with `www-data` group:

```ini
User=roman
Group=www-data
```

Adjust these to match your system's user/group configuration.

### Socket File Location

The Unix socket is created at `/var/www/network/production/slm.sock`. Ensure:
- The directory exists
- The user has write permissions
- Nginx can read from this socket

---

## 📊 Monitoring

### Check Service Health

```bash
# Verify service is running
systemctl is-active slm-network.service

# Check socket file exists
ls -la /var/www/network/production/slm.sock

# Test with curl
curl -I http://localhost
```

### Log Files

- **Systemd logs**: `journalctl -u slm-network.service`
- **Nginx access logs**: `/var/log/nginx/access.log`
- **Nginx error logs**: `/var/log/nginx/error.log`
- **Application logs**: `/var/www/network/production/logs/`

---

## 🆘 Common Issues

### 502 Bad Gateway

**Cause**: Gunicorn service not running or socket not accessible

**Solution**:
```bash
# Check service status
sudo systemctl status slm-network.service

# Check for errors
sudo journalctl -u slm-network.service -n 50

# Verify socket exists
ls -la /var/www/network/production/slm.sock

# Restart service
sudo systemctl restart slm-network.service
```

### Worker Failed to Boot

**Cause**: Usually missing PYTHONPATH or database connection issues

**Solution**:
1. Verify PYTHONPATH in service file
2. Test database connection: `psql -U slm_user -d slm -h localhost`
3. Check .env file configuration
4. Review error logs: `sudo journalctl -u slm-network.service -xe`

### XMLSchemaParseError

**Cause**: Missing PYTHONPATH prevents proper module imports

**Solution**: Ensure the service file includes:
```ini
Environment="PYTHONPATH=/home/roman/gitrepo/SLM/network/src"
```

---

## 📚 Additional Resources

- [SLM Documentation](https://igs-slm.readthedocs.io)
- [IGS Site Log Manager GitHub](https://github.com/International-GNSS-Service/SLM)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Systemd Service Documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
