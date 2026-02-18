# Grafana Dashboards and Datasources

## Setup Instructions

### 1. Prometheus Data Source
1. Go to Configuration > Data Sources
2. Click "Add data source"
3. Select "Prometheus"
4. Configure:
   - Name: `Prometheus`
   - URL: `http://prometheus:9090`
   - Access: `Server (default)`
   - Click "Save & Test"

### 2. Import Dashboards
1. Go to Dashboards > Import
2. Upload the JSON dashboard files
3. Select Prometheus data source
4. Click "Import"

### 3. Dashboard Variables
Create these variables for flexible dashboard usage:
- `instance`: Prometheus server instance
- `app`: Application name (default: arya-video-agent)
- `namespace`: Cache namespace (default: all)
- `job`: Prometheus job name
