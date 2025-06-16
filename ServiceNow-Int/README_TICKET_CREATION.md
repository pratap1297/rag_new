# ServiceNow Warehouse Network Ticket Generator

This directory contains scripts to generate realistic network incident tickets for Cisco routers in warehouse environments and push them to ServiceNow.

## 📁 Files Overview

### Core Scripts
- **`create_sample_tickets.py`** - Main script to create actual ServiceNow tickets (requires credentials)
- **`servicenow_connector.py`** - ServiceNow API connector class
- **`demo_ticket_creation.py`** - Demo script that shows what tickets would be created (no credentials needed)

### Configuration
- **`.env`** (root directory) - Environment variables for ServiceNow credentials

## 🚀 Quick Start

### Option 1: Demo Mode (No ServiceNow Access Required)
```bash
python demo_ticket_creation.py
```
This will show you exactly what tickets would be created without requiring ServiceNow credentials.

### Option 2: Create Actual ServiceNow Tickets
1. Configure your ServiceNow credentials in the root `.env` file
2. Run the ticket creation script:
```bash
python create_sample_tickets.py
```

## ⚙️ Configuration

### ServiceNow Credentials
Add these variables to your root `.env` file:

```env
# ServiceNow Configuration
SERVICENOW_INSTANCE=your-instance-name
SERVICENOW_USERNAME=your-username
SERVICENOW_PASSWORD=your-password
```

**Instance Format Options:**
- `your-company` (will become `https://your-company.service-now.com`)
- `your-company.service-now.com` (will become `https://your-company.service-now.com`)
- `https://your-company.service-now.com` (used as-is)

## 🎫 Generated Ticket Types

### Warehouse Locations
- Distribution Center North - Chicago, IL
- Fulfillment Center East - Atlanta, GA
- Regional Warehouse West - Phoenix, AZ
- Central Distribution Hub - Dallas, TX
- Logistics Center South - Miami, FL
- Processing Facility - Denver, CO

### Cisco Router Models
- Cisco ISR 4331, 4351, 4431
- Cisco ASR 1001-X
- Cisco ISR 1100-4G
- Cisco ISR 900 Series
- Cisco Catalyst 8300
- Cisco ISR 4321

### Network Issue Types
1. **Connectivity Issues**
   - Intermittent connection drops
   - High packet loss
   - Timeout errors

2. **Performance Degradation**
   - Slow data transfer
   - High latency
   - Bandwidth bottlenecks

3. **Routing Protocol Issues**
   - Route flapping
   - Convergence delays
   - Unreachable networks

4. **Hardware Malfunctions**
   - Device overheating
   - Memory errors
   - Interface failures

5. **Security Incidents**
   - Unauthorized access attempts
   - Suspicious traffic
   - Firewall alerts

### Business Impact Scenarios
- Warehouse operations halted
- Inventory management system offline
- Barcode scanners disconnected
- WMS (Warehouse Management System) inaccessible
- RFID tracking system down
- Automated sorting system offline
- Loading dock systems disconnected
- Temperature monitoring system offline

## 📊 Priority Distribution

The scripts generate tickets with realistic priority distribution:

| Priority | Label | Count | Description |
|----------|-------|-------|-------------|
| 1 | Critical | 25% | Complete operations shutdown, >$10K/hour impact |
| 2 | High | 37.5% | Significant operational impact, multiple systems affected |
| 3 | Moderate | 25% | Partial service degradation, workarounds available |
| 4 | Low | 12.5% | Minor impact, normal operations continue |

## 🎯 Sample Ticket Structure

Each generated ticket includes:

### Basic Information
- **Short Description**: Brief issue summary with equipment and location
- **Priority**: 1-4 (Critical to Low)
- **Category**: Network > Router
- **State**: New (1)
- **Assignment Group**: Network Operations

### Detailed Information
- **Location**: Specific warehouse facility
- **CMDB CI**: Router hostname (e.g., WH-RTR-CEN-28)
- **Business Service**: Warehouse Operations

### Comprehensive Description
- **Incident Summary**: Overview of the network issue
- **Affected Equipment**: Device details, hostname, IP, location
- **Business Impact**: Specific operational consequences
- **Symptoms Observed**: Technical symptoms experienced
- **Troubleshooting Performed**: Initial diagnostic steps taken
- **Priority Justification**: Reason for assigned priority level

## 🔧 Usage Examples

### Demo Mode
```bash
# Show 5 sample tickets
python demo_ticket_creation.py
# Select option 1

# Show 10 sample tickets  
python demo_ticket_creation.py
# Select option 2

# Custom number of tickets
python demo_ticket_creation.py
# Select option 3, enter desired count
```

### Create Actual Tickets
```bash
# Create 5 tickets in ServiceNow
python create_sample_tickets.py
# Select option 1

# Create 10 tickets in ServiceNow
python create_sample_tickets.py  
# Select option 2

# Create custom number of tickets
python create_sample_tickets.py
# Select option 3, enter desired count
```

## 📋 Sample Output

### Demo Mode Output
```
DEMO: Showing 5 sample warehouse network tickets that would be created
================================================================================

TICKET 1/5 (Priority 1):
--------------------------------------------------
Title: Cisco router connectivity failure - Cisco ISR 4321 at Central Distribution Hub
Priority: Critical
Location: Central Distribution Hub - Dallas, TX
Equipment: WH-RTR-CEN-28
Category: Network > Router
Assigned to: Network Operations
Would create ticket: INC1030244

Description Preview:
   INCIDENT SUMMARY:
   Network connectivity issues affecting Cisco ISR 4321 router in Central Distribution Hub - Dallas, TX.
   
   AFFECTED EQUIPMENT:
   - Device: Cisco ISR 4321
   - Hostname: WH-RTR-CEN-28
   - Management IP: 10.154.141.1
   - Location: Central Distribution Hub - Dallas, TX
   ... (15 more lines)
```

### Actual Creation Output
```
Creating 5 sample warehouse network tickets...
============================================================

Creating ticket 1/5 (Priority 1)...
Created: INC0010001 - Critical Priority
   Location: Distribution Center North - Chicago, IL
   Equipment: WH-RTR-DIS-15

Creating ticket 2/5 (Priority 1)...
Created: INC0010002 - Critical Priority
   Location: Regional Warehouse West - Phoenix, AZ
   Equipment: WH-RTR-REG-42

Summary: Successfully created 5/5 tickets

Created Tickets:
   • INC0010001 - Priority 1
   • INC0010002 - Priority 1
   • INC0010003 - Priority 2
   • INC0010004 - Priority 2
   • INC0010005 - Priority 3
```

## 🛠️ Troubleshooting

### Connection Issues
1. **Verify credentials** in `.env` file
2. **Check instance URL** format
3. **Test connectivity** to ServiceNow instance
4. **Verify user permissions** for incident creation

### Common Errors
- **Missing credentials**: Ensure all required environment variables are set
- **Invalid instance**: Check ServiceNow instance name/URL format
- **Permission denied**: Verify user has incident creation permissions
- **Network timeout**: Check firewall/proxy settings

### Testing Connection
```bash
python servicenow_connector.py
```
This will test your ServiceNow connection and show recent incidents.

## 🔐 Security Notes

- Store credentials securely in `.env` file
- Never commit credentials to version control
- Use service accounts with minimal required permissions
- Consider using OAuth for production environments

## 📈 Integration with Router Rescue AI

These tickets are designed to integrate with the Router Rescue AI system:

1. **Network Keywords**: Tickets include router, switch, network, BGP, OSPF terms
2. **Cisco Equipment**: Focus on Cisco router models commonly used in warehouses  
3. **Technical Details**: Include specific network troubleshooting information
4. **Business Context**: Warehouse-specific operational impacts

The ServiceNow scheduler (`servicenow_scheduler.py`) can automatically fetch these tickets and process them through the Router Rescue AI backend for intelligent analysis and recommendations.

## 📞 Support

For issues with:
- **Script functionality**: Check this README and troubleshooting section
- **ServiceNow API**: Consult ServiceNow documentation
- **Router Rescue AI integration**: See main project documentation 