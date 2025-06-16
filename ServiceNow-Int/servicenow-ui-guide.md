# ServiceNow UI Navigation Guide
## How to Find and View Incidents in ServiceNow

### 🌐 **Accessing ServiceNow**

1. **Login to ServiceNow Instance**
   - URL: `https://dev319029.service-now.com`
   - Use your ServiceNow credentials
   - Navigate to the main dashboard

### 📋 **Finding Incidents in the UI**

#### **Method 1: Using the Application Navigator**

1. **Navigate to Incidents**
   - In the left navigation panel (Application Navigator)
   - Go to: **Incident** → **All**
   - Or search for "Incident" in the filter navigator

2. **Direct Path**
   ```
   Application Navigator → Incident → All
   ```

#### **Method 2: Using Global Search**

1. **Use the Search Bar**
   - Click on the search icon (🔍) in the top navigation
   - Type: "Incidents" or specific incident number (e.g., "INC0010001")
   - Select "Incident" from the dropdown

#### **Method 3: Using Quick Links**

1. **Dashboard Widgets**
   - Many ServiceNow instances have incident widgets on the homepage
   - Look for "My Incidents", "Open Incidents", or "Recent Incidents"

### 🔍 **Filtering and Searching Incidents**

#### **Basic Filters (Left Panel)**

1. **By State**
   - New
   - In Progress  
   - On Hold
   - Resolved
   - Closed

2. **By Priority**
   - 1 - Critical
   - 2 - High
   - 3 - Moderate
   - 4 - Low
   - 5 - Planning

3. **By Category**
   - Network
   - Hardware
   - Software
   - Inquiry
   - Database

#### **Advanced Filtering**

1. **Using the Filter Bar**
   - Click "Show Filters" at the top of the incident list
   - Add conditions like:
     - `Category = Network`
     - `Priority = 1`
     - `State = New`

2. **Custom Filter Examples**
   ```
   Network Incidents: Category = Network
   Critical Issues: Priority = 1
   Open Items: State IN New,In Progress,On Hold
   Recent Items: Created > Last 7 days
   ```

### 🎯 **Finding Specific Incidents from Our Data**

#### **Critical Network Incidents (29 total)**
1. **Filter Setup**:
   - Priority = 1 (Critical)
   - Category = Network
   
2. **Expected Results**: Should show network-related critical incidents including our warehouse tickets

#### **All Network Incidents (15 total)**
1. **Filter Setup**:
   - Category = Network
   
2. **Expected Results**: Should include tickets like:
   - INC0010004: Complete Network Outage - Chicago Warehouse
   - INC0010005: Cisco Router Intermittent Connectivity
   - INC0010006: Switch Port Failures
   - And other network-related incidents

#### **Recent Incidents We Created**
1. **Search by Number Range**:
   - Use filter: `Number STARTSWITH INC001`
   - This should show our warehouse network tickets (INC0010004-INC0010011)

### 📊 **Viewing Incident Details**

#### **Incident Form Fields**

When you click on an incident, you'll see:

1. **Basic Information**
   - Number (e.g., INC0010001)
   - Short Description
   - Description
   - State
   - Priority
   - Urgency

2. **Assignment Information**
   - Assigned to
   - Assignment group
   - Caller

3. **Classification**
   - Category
   - Subcategory
   - Configuration Item (CI)

4. **Business Information**
   - Business service
   - Location
   - Impact

#### **Tabs in Incident Form**
- **Notes**: Work notes and additional comments
- **Related Records**: Linked items
- **Attachments**: Files and documents
- **Activities**: Timeline of changes

### 🔧 **Useful ServiceNow UI Tips**

#### **List Navigation**
1. **Sorting**: Click column headers to sort
2. **Grouping**: Right-click column headers → Group by
3. **Personalization**: Right-click list → Configure → List Layout

#### **Quick Actions**
1. **Bulk Operations**: Select multiple incidents → Actions menu
2. **Export**: Right-click list → Export → Excel/CSV
3. **Print**: Use browser print function

#### **Bookmarking Useful Views**
1. **Create Personal Filters**
   - Set up your filters
   - Click "Save" → "Save as new filter"
   - Name it (e.g., "My Network Incidents")

2. **Bookmark URLs**
   - Save direct links to filtered views
   - Example: `https://dev319029.service-now.com/incident_list.do?sysparm_query=category=network`

### 📱 **Mobile Access**

#### **ServiceNow Mobile App**
1. Download ServiceNow mobile app
2. Login with same credentials
3. Navigate to Incidents
4. Use same filtering capabilities

### 🔗 **Direct URLs for Quick Access**

#### **Common Incident Views**
```
All Incidents:
https://dev319029.service-now.com/incident_list.do

Network Incidents:
https://dev319029.service-now.com/incident_list.do?sysparm_query=category=network

Critical Incidents:
https://dev319029.service-now.com/incident_list.do?sysparm_query=priority=1

New Incidents:
https://dev319029.service-now.com/incident_list.do?sysparm_query=state=1

Our Warehouse Tickets (INC001xxxx):
https://dev319029.service-now.com/incident_list.do?sysparm_query=numberSTARTSWITHINC001
```

### 🎨 **Customizing Your View**

#### **List Columns**
1. **Add/Remove Columns**
   - Right-click list header
   - Select "Configure" → "List Layout"
   - Add useful columns like:
     - Business Impact
     - Configuration Item
     - Location
     - Created date

2. **Recommended Columns for Network Incidents**
   - Number
   - Short Description
   - Priority
   - State
   - Category
   - Configuration Item
   - Location
   - Created

#### **Dashboard Widgets**
1. **Create Personal Dashboard**
   - Go to Self-Service → Dashboards
   - Create widgets for:
     - My Open Incidents
     - Critical Network Issues
     - Recent Assignments

### 🚨 **Troubleshooting UI Issues**

#### **Common Problems**
1. **Can't See Incidents**
   - Check user permissions
   - Verify you're in the correct application scope
   - Clear browser cache

2. **Filters Not Working**
   - Refresh the page
   - Clear all filters and reapply
   - Check for typos in filter values

3. **Slow Loading**
   - Reduce the number of records displayed
   - Remove unnecessary columns
   - Use more specific filters

### 📞 **Getting Help**

#### **ServiceNow Help**
1. **Help Icon**: Click "?" in top navigation
2. **Documentation**: Access built-in help docs
3. **Community**: ServiceNow Community forums

#### **Instance-Specific Help**
1. **System Administrator**: Contact your ServiceNow admin
2. **IT Help Desk**: Internal support for access issues

---

## 🎯 **Quick Reference: Finding Our Warehouse Network Tickets**

### **Step-by-Step Instructions**

1. **Login**: Go to `https://dev319029.service-now.com`
2. **Navigate**: Application Navigator → Incident → All
3. **Filter**: Add filter `Category = network`
4. **Search**: Look for incidents INC0010004 through INC0010011
5. **View**: Click on any incident number to see full details

### **Expected Warehouse Network Tickets**
- **INC0010004**: Complete Network Outage - Chicago Warehouse (Critical)
- **INC0010005**: Cisco Router Intermittent Connectivity - Phoenix (High)
- **INC0010006**: Switch Port Failures - Miami Distribution Hub (High)
- **INC0010007**: WAN Link Degradation - Denver Regional Center (High)
- **INC0010008**: WiFi Access Point Failures - Los Angeles (Moderate)
- **INC0010009**: Firewall Configuration Issue - Seattle (Critical)
- **INC0010010**: Network Cable Infrastructure Damage - Denver (High)
- **INC0010011**: DHCP Server Failure - Miami Distribution Hub (High)

These tickets contain detailed technical information, business impact assessments, and troubleshooting procedures that will be perfect for testing our Router AI Agent system! 