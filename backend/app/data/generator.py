import json
import os
from pathlib import Path
from typing import List, Dict, Any

DATA_DIR = Path(__file__).resolve().parent

# 1. Ground truth metadata (Kept separate from searchable evidence)
CASES_GROUND_TRUTH: List[Dict[str, Any]] = [
    {
        "id": "INC-2024-0891",
        "title": "Project Aegis Core Algorithm Exfiltration",
        "category": "Intellectual Property Theft",
        "incident_description": "On October 14, 2024, at 23:42 UTC, an external threat alert flagged an unauthorized 4.2 GB data transfer of the proprietary 'Project Aegis' codebase to an offshore IP address (198.51.100.44). Initial source control commits were tagged with Lead Engineer Alice Vance's credentials. However, automated workstation logs show conflicting login events from Bob Martin's terminal and unusual physical badge events.",
        "ground_truth": {
            "primary_responsible_party": "Mallory Price",
            "role": "External Security Consultant / Contract Pentester",
            "method": "Exploited Bob Martin's unlocked DevOps terminal WS-ENG-088 during an authorized after-hours maintenance window. Cloned Alice Vance's SSH key from a shared staging repo and forged git commit author headers before SFTP transfer to 198.51.100.44.",
            "framed_individual": "Alice Vance",
            "exonerating_evidence": ["ACC-101", "ACC-102"],
            "incriminating_evidence": ["ACC-103", "LOG-201", "LOG-202", "LOG-203", "MSG-301", "MSG-302", "EML-401"],
            "policy_violation": "POL-SEC-04 (Unauthorized Code Export & Terminal Sharing)",
            "verdict_type": "conclusive"
        }
    },
    {
        "id": "INC-2024-1142",
        "title": "Unauthorized ₹41,22,500 Wire Transfer & Vendor Tampering",
        "category": "Financial Fraud & Policy Bypass",
        "incident_description": "On November 3, 2024, Accounts Payable disbursed a ₹41,22,500 wire transfer for invoice #INV-9921 to 'Apex-Cloud-Billing LLC' instead of established partner 'Apex Cloud Systems Inc.'. The transfer cleared without the mandatory VP secondary authorization required by corporate policy POL-FIN-12. The finance department flagged the transaction 48 hours later during monthly reconciliation.",
        "ground_truth": {
            "primary_responsible_party": "David Chen",
            "role": "Accounts Payable Specialist",
            "method": "Bypassed mandatory dual-authorization policy POL-FIN-12 using a spoofed executive email as pretext. While claiming to be a victim of BEC fraud, digital forensic audit revealed an illicit cryptocurrency kickback of 5,000 USDT received three days prior from an affiliate linked to the fraudulent shell company.",
            "exonerating_evidence": [],
            "incriminating_evidence": ["POL-FIN-12", "EML-501", "TRX-601", "MSG-602", "TRX-602", "MTG-701"],
            "policy_violation": "POL-FIN-12 (Dual Approval Required for Disbursements ≥ ₹8,50,000)",
            "verdict_type": "conclusive"
        }
    },
    {
        "id": "INC-2024-1405",
        "title": "Critical Production Outage and Audit Log Truncation",
        "category": "Infrastructure Outage & Ambiguous Log Loss",
        "incident_description": "On December 12, 2024, between 02:14 and 02:45 UTC, the primary US-East Kubernetes cluster suffered an unrecoverable failure resulting in 31 minutes of total customer downtime. Concurrently, all security audit log files for that 31-minute window were wiped from the primary S3 bucket. System administrators cannot determine whether this was deliberate sabotage by a disgruntled staff member or a catastrophic cascading failure of automated maintenance scripts.",
        "ground_truth": {
            "primary_responsible_party": "INCONCLUSIVE / SYSTEM RACE CONDITION (UNRESOLVED)",
            "role": "Automated Service Accounts & System Administration",
            "method": "Direct telemetry attributes the cluster failure to a race condition between Jenkins automated failover rehearsal and Docker storage pruner clean_logs.sh. However, because S3 audit logs during 02:14-02:45 were completely erased by svc-k8s-daemon, insider sabotage by DBA Marcus Brody cannot be mathematically ruled out, nor can it be proven.",
            "exonerating_evidence": ["LOG-805", "LOG-806"],
            "incriminating_evidence": ["LOG-801", "LOG-802", "LOG-803", "MSG-804"],
            "policy_violation": "POL-OPS-03 (Change Management Freeze & WORM Storage Enforcement)",
            "verdict_type": "insufficient_evidence"
        }
    }
]

# 2. Searchable Corporate Evidence Records (Indexed in ChromaDB & SQLite)
SYNTHETIC_RECORDS: List[Dict[str, Any]] = [
    # ------------------ Corporate Policies ------------------
    {
        "record_id": "POL-SEC-04",
        "case_id": "INC-2024-0891",
        "source_type": "policy",
        "title": "Corporate Policy: Source Code Protection and Network Egress",
        "timestamp": "2024-01-15T09:00:00Z",
        "content": "Section 4.2: All proprietary algorithms and repositories under Project Aegis are classified RESTRICTED. Direct outbound transmission of source code archives via SFTP, SSH, or unapproved cloud storage is strictly prohibited without written dual authorization from the Chief Information Security Officer (CISO) and Lead Project Architect. Section 4.5: Workstations must be locked when unattended; sharing of privileged access sessions is a dismissible infraction.",
        "metadata": {"category": "Information Security", "version": "3.1", "author": "CISO Office"}
    },
    {
        "record_id": "POL-FIN-12",
        "case_id": "INC-2024-1142",
        "source_type": "policy",
        "title": "Corporate Policy: Financial Authorization Limits and Disbursements",
        "timestamp": "2023-11-01T09:00:00Z",
        "content": "Section 2.1: Single-signature disbursements are strictly limited to amounts under ₹8,50,000. Any payment equal to or exceeding ₹8,50,000 requires two independent approvals: (1) Accounts Payable Specialist review and (2) Department Director or Vice President digital signature. Email approvals or verbal requests from executives are not valid reasons to bypass the automated approval process.",
        "metadata": {"category": "Finance & Accounting", "version": "4.0", "author": "Internal Audit Committee"}
    },
    {
        "record_id": "POL-OPS-03",
        "case_id": "INC-2024-1405",
        "source_type": "policy",
        "title": "Corporate Policy: Production Change Management & Audit Retention",
        "timestamp": "2024-02-10T10:00:00Z",
        "content": "Section 5.1: Automated infrastructure failover testing must only be scheduled during approved maintenance windows with senior SRE on-call presence. Section 5.4: Production audit logs must be replicated in real-time to Write Once Read Many (WORM) compliant S3 buckets with ObjectLock enabled. Under no circumstances may automated cleanup scripts have DeleteObject permissions on audit buckets.",
        "metadata": {"category": "Site Reliability Engineering", "version": "2.5", "author": "VP Infrastructure"}
    },

    # ------------------ Case 1 Evidence: INC-2024-0891 (Project Aegis) ------------------
    {
        "record_id": "EMP-001",
        "case_id": "INC-2024-0891",
        "source_type": "employee_record",
        "title": "Employee Profile: Alice Vance",
        "timestamp": "2024-10-01T00:00:00Z",
        "content": "Name: Alice Vance. Title: Senior Principal AI Architect. Role: Project Lead for Project Aegis. Security Clearance: Level 4 (Top Secret Internal). Tenured: 5 years. Performance: Outstanding. System Credentials: SSH Key #AV-9012, Git handle: @alice.vance. Workstation: WS-ENG-012 (Building B, Room 302).",
        "metadata": {"department": "AI Research", "email": "alice.vance@novacorp.internal", "manager": "Evelyn Reed"}
    },
    {
        "record_id": "EMP-002",
        "case_id": "INC-2024-0891",
        "source_type": "employee_record",
        "title": "Employee Profile: Bob Martin",
        "timestamp": "2024-10-01T00:00:00Z",
        "content": "Name: Bob Martin. Title: Senior DevOps Engineer. Role: Cluster Infrastructure & Staging Server Administrator. Security Clearance: Level 3. Workstation: WS-ENG-088 (Building B, Lab 3). On-call shift: October 14, 2024, 18:00 - 02:00 UTC.",
        "metadata": {"department": "DevOps", "email": "bob.martin@novacorp.internal", "manager": "Elena Rostova"}
    },
    {
        "record_id": "EMP-003",
        "case_id": "INC-2024-0891",
        "source_type": "employee_record",
        "title": "Contractor Profile: Mallory Price",
        "timestamp": "2024-10-01T00:00:00Z",
        "content": "Name: Mallory Price. Title: Senior Security Consultant. Organization: CyberShield Advisory Group (Vendor). Role: Third-party penetration testing and vulnerability auditing. Guest Badge: G-44. Clearance: Level 2 (Temporary Escorted Lab Access). Contract Term: Concludes October 18, 2024.",
        "metadata": {"department": "External Security Audit", "email": "m.price@cybershield-vendor.com", "sponsor": "CISO Office"}
    },
    {
        "record_id": "ACC-101",
        "case_id": "INC-2024-0891",
        "source_type": "access_log",
        "title": "Physical Security Badge Log: Alice Vance Exit",
        "timestamp": "2024-10-14T18:30:12Z",
        "content": "Turnstile B-North Exit Log. Badge ID: #AV-9012 (Alice Vance). Event: OUTBOUND SWIPE. Status: Approved. Facility: Headquarters Main Gate.",
        "metadata": {"location": "HQ Main Gate", "badge_id": "AV-9012", "event_type": "exit"}
    },
    {
        "record_id": "ACC-102",
        "case_id": "INC-2024-0891",
        "source_type": "transaction",
        "title": "Expense Receipt: Client Dinner Alice Vance",
        "timestamp": "2024-10-14T22:45:00Z",
        "content": "Corporate Amex Card ending in 4102. Cardholder: Alice Vance. Vendor: The Capital Grille, Downtown (18 miles from HQ). Transaction Amount: ₹29,078.50. Timestamp: 2024-10-14 22:15 UTC. Accompanying Uber receipt from Restaurant to Residence: Pickup 22:30 UTC, Dropoff 22:58 UTC.",
        "metadata": {"cardholder": "Alice Vance", "amount": 29078.50, "currency": "INR", "vendor": "The Capital Grille"}
    },
    {
        "record_id": "ACC-103",
        "case_id": "INC-2024-0891",
        "source_type": "access_log",
        "title": "Physical Security Badge Log: Lab 3 Secure Entry",
        "timestamp": "2024-10-14T22:50:33Z",
        "content": "Door Controller: Building B, Lab 3 (DevOps & Server Annex). Badge ID: #G-44 (Mallory Price). Event: INBOUND SWIPE. Status: Approved (Scheduled Maintenance Window). Keypad PIN entered: Correct.",
        "metadata": {"location": "Building B - Lab 3", "badge_id": "G-44", "event_type": "entry"}
    },
    {
        "record_id": "MSG-301",
        "case_id": "INC-2024-0891",
        "source_type": "internal_message",
        "title": "Slack Direct Message: Mallory Price to Bob Martin",
        "timestamp": "2024-10-14T17:45:20Z",
        "content": "Mallory Price [17:45]: 'Hey Bob, I'll be running the staged vulnerability scans in Lab 3 tonight around 23:00 UTC. You don't need to stay late at your desk, I'll monitor the automated scripts and log off when done.'\nBob Martin [17:48]: 'Appreciate it Mallory! I'll leave the terminal session active on WS-ENG-088 so the staging daemons don't drop connection. Ping me if any alerts pop.'",
        "metadata": {"channel": "direct-message", "participants": ["Mallory Price", "Bob Martin"]}
    },
    {
        "record_id": "MSG-302",
        "case_id": "INC-2024-0891",
        "source_type": "internal_message",
        "title": "Slack Channel Post: #devops-team",
        "timestamp": "2024-10-14T18:15:00Z",
        "content": "Bob Martin [18:15]: 'Heads up team, heading out early for family dinner. Workstation WS-ENG-088 in Lab 3 remains unlocked under maintenance bypass for external contractor Mallory Price to execute pentest scans.'",
        "metadata": {"channel": "#devops-team", "author": "Bob Martin"}
    },
    {
        "record_id": "LOG-201",
        "case_id": "INC-2024-0891",
        "source_type": "access_log",
        "title": "Host Operating System Audit Log: WS-ENG-088",
        "timestamp": "2024-10-14T23:15:40Z",
        "content": "Host: WS-ENG-088. Local IP: 10.200.4.15. Physical Console Event: Keyboard activity resumed from screensaver without re-authenticating (screensaver grace period disabled). User context: bmartin (uid 1004). Shell spawned: bash pid 39121.",
        "metadata": {"hostname": "WS-ENG-088", "ip": "10.200.4.15", "user": "bmartin"}
    },
    {
        "record_id": "LOG-202",
        "case_id": "INC-2024-0891",
        "source_type": "access_log",
        "title": "GitLab Enterprise Audit Log: Project Aegis Commit",
        "timestamp": "2024-10-14T23:38:12Z",
        "content": "GitLab Server Event: git-push to repository 'core/aegis-engine.git'. Branch: main. Commit Hash: 8f4a1c0d2. Stated Author: 'Alice Vance <alice.vance@novacorp.internal>'. Stated Committer: 'Alice Vance'. Client Origin IP: 10.200.4.15 (Port: Building B Lab 3 Switch Port 14 - Host: WS-ENG-088). Used SSH Key fingerprint: SHA256:AV-Key-Staging-Deploy (cached on WS-ENG-088).",
        "metadata": {"repo": "core/aegis-engine.git", "commit": "8f4a1c0d2", "client_ip": "10.200.4.15"}
    },
    {
        "record_id": "LOG-203",
        "case_id": "INC-2024-0891",
        "source_type": "access_log",
        "title": "Palo Alto Firewall Network Flow Log: Egress Alert",
        "timestamp": "2024-10-14T23:42:05Z",
        "content": "Firewall Alert #FW-9941. Protocol: SFTP / SSH (TCP Port 2222). Source: 10.200.4.15 (WS-ENG-088). Destination: 198.51.100.44 (Offshore Host, ASN 49102, Geo: Foreign Hosting Facility). Transferred Payload: 4,289,145,210 bytes (4.2 GB). Archive Name: aegis_weights_and_source_v4.tar.gz. Status: Completed.",
        "metadata": {"firewall_id": "PA-5250-HQ", "dest_ip": "198.51.100.44", "bytes_transferred": 4289145210}
    },
    {
        "record_id": "EML-401",
        "case_id": "INC-2024-0891",
        "source_type": "email",
        "title": "Forensic Email Image: Contractor Laptop Cache",
        "timestamp": "2024-10-15T08:12:00Z",
        "content": "Recovered unsent draft from local mail spool on Mallory Price's assigned contractor laptop. To: secure-drop-box-49@protonmail.com. Subject: Package Ready. Body: 'Target package archived from Lab 3 terminal. Exfiltration completed at 23:42 UTC to designated server 198.51.100.44. Commit headers planted under AV lead profile as discussed. Release milestone escrow payment to wallet 0x7a3...'",
        "metadata": {"sender": "m.price@cybershield-vendor.com", "laptop_id": "CYBER-LPT-04"}
    },

    # ------------------ Case 2 Evidence: INC-2024-1142 (Procurement Wire Fraud) ------------------
    {
        "record_id": "EMP-004",
        "case_id": "INC-2024-1142",
        "source_type": "employee_record",
        "title": "Employee Profile: David Chen",
        "timestamp": "2024-10-01T00:00:00Z",
        "content": "Name: David Chen. Title: Accounts Payable Specialist. Role: Processing daily vendor disbursements and supplier invoices. Tenured: 2 years. Authorization Limit: Up to ₹8,50,000 without secondary approval.",
        "metadata": {"department": "Accounts Payable", "email": "david.chen@novacorp.internal", "manager": "Sarah Lin"}
    },
    {
        "record_id": "EMP-005",
        "case_id": "INC-2024-1142",
        "source_type": "employee_record",
        "title": "Employee Profile: Sarah Lin",
        "timestamp": "2024-10-01T00:00:00Z",
        "content": "Name: Sarah Lin. Title: Director of Financial Operations. Role: Secondary signatory on disbursements between ₹8,50,000 and ₹85,00,000. Out of office attending Q4 Financial Summit on November 3 from 13:00 to 18:00 UTC.",
        "metadata": {"department": "Finance", "email": "sarah.lin@novacorp.internal"}
    },
    {
        "record_id": "EML-501",
        "case_id": "INC-2024-1142",
        "source_type": "email",
        "title": "Inbound Spoofed Email: Urgent CEO Invoice",
        "timestamp": "2024-11-03T15:20:10Z",
        "content": "From: 'CEO Executive Office' <ceo-office@novac0rp.com> [Note domain: novac0rp.com with numeral zero]. To: david.chen@novacorp.internal. Subject: URGENT: Outstanding Apex Cloud Systems Payment. Body: 'David, our primary cloud services with Apex Cloud will terminate at midnight due to non-payment of invoice #INV-9921 (₹41,22,500). Disburse wire immediately to new banking details: Apex-Cloud-Billing LLC, First Offshore Bank, Routing: 021000089, Acct: 881920491. I personally authorize bypassing secondary director sign-off given Sarah is in summit.'",
        "metadata": {"spoofed": True, "sender_domain": "novac0rp.com", "claimed_amount": 4122500.00, "currency": "INR"}
    },
    {
        "record_id": "TRX-601",
        "case_id": "INC-2024-1142",
        "source_type": "transaction",
        "title": "ERP Wire Transfer Record: #WT-8831",
        "timestamp": "2024-11-03T16:14:00Z",
        "content": "ERP Financial Transaction #WT-8831. Payee: Apex-Cloud-Billing LLC. Amount: ₹41,22,500 INR. Invoice Ref: INV-9921. Initiator: David Chen (User: dchen). Secondary Approver: [BLANK - OVERRIDDEN]. Override Reason: 'Per Direct Executive Directive from CEO Office'. Bank Ref: First Offshore Bank #881920491. Status: Executed.",
        "metadata": {"amount": 4122500.00, "currency": "INR", "initiator": "David Chen", "policy_breached": "POL-FIN-12"}
    },
    {
        "record_id": "MSG-602",
        "case_id": "INC-2024-1142",
        "source_type": "internal_message",
        "title": "Slack Message: David Chen to Sarah Lin",
        "timestamp": "2024-11-03T16:35:10Z",
        "content": "David Chen [16:35]: 'Hi Sarah, FYI I just cleared an urgent ₹41,22,500 invoice for Apex Cloud because the CEO emailed saying our production instances would be cut off otherwise. Since you were in the summit I used executive emergency override.'\n(Note: Message was sent 21 minutes AFTER the wire transfer had already been finalized and cleared).",
        "metadata": {"channel": "direct-message", "sender": "David Chen"}
    },
    {
        "record_id": "TRX-602",
        "case_id": "INC-2024-1142",
        "source_type": "transaction",
        "title": "Financial Intelligence Forensic Audit: David Chen Personal Account",
        "timestamp": "2024-10-31T14:22:00Z",
        "content": "Subpoenaed digital asset audit: Personal cryptocurrency wallet registered to David Chen (phone verification match) received a deposit of 5,000 USDT on October 31, 2024 (3 days before the wire transfer). The sending address was traced back to the same overseas entity that registered domain 'novac0rp.com'.",
        "metadata": {"account_holder": "David Chen", "illicit_deposit": 5000.00, "currency": "USDT"}
    },
    {
        "record_id": "MTG-701",
        "case_id": "INC-2024-1142",
        "source_type": "meeting_note",
        "title": "Minutes: Q4 IT Vendor Review Meeting",
        "timestamp": "2024-10-28T11:00:00Z",
        "content": "Attendees: Sarah Lin, David Chen, IT Director. Discussion Point 3: 'Apex Cloud Systems contract confirmed paid in full through December 31, 2024 via annual pre-payment PO #8819. No additional payments due until Q1 2025.' David Chen was recorded as taking meeting minutes.",
        "metadata": {"attendees": ["Sarah Lin", "David Chen"], "vendor": "Apex Cloud Systems"}
    },

    # ------------------ Case 3 Evidence: INC-2024-1405 (Cloud Outage & Log Loss - Ambiguous Case) ------------------
    {
        "record_id": "EMP-007",
        "case_id": "INC-2024-1405",
        "source_type": "employee_record",
        "title": "Employee Profile: Marcus Brody",
        "timestamp": "2024-11-01T00:00:00Z",
        "content": "Name: Marcus Brody. Title: Database Administrator. Role: Relational databases & cluster backup operations. Context: Reassigned to legacy systems maintenance following team restructuring in November 2024. Active VPN credentials.",
        "metadata": {"department": "Database Systems", "email": "marcus.brody@novacorp.internal"}
    },
    {
        "record_id": "EMP-008",
        "case_id": "INC-2024-1405",
        "source_type": "employee_record",
        "title": "Employee Profile: Elena Rostova",
        "timestamp": "2024-11-01T00:00:00Z",
        "content": "Name: Elena Rostova. Title: Senior Site Reliability Engineering Lead. Role: SRE On-call incident response commander for production cloud clusters.",
        "metadata": {"department": "SRE", "email": "elena.rostova@novacorp.internal"}
    },
    {
        "record_id": "LOG-801",
        "case_id": "INC-2024-1405",
        "source_type": "access_log",
        "title": "Jenkins Automated Deployment Log: Failover Test",
        "timestamp": "2024-12-12T02:00:00Z",
        "content": "Job #SRE-DR-Rehearsal-402 triggered by automated cron (User: svc-jenkins-auto). Action: Initiate graceful failover of primary PostgreSQL cluster to replica zone US-East-2. Parameter: graceful_timeout=300s.",
        "metadata": {"service": "Jenkins", "job": "SRE-DR-Rehearsal-402", "triggered_by": "svc-jenkins-auto"}
    },
    {
        "record_id": "LOG-802",
        "case_id": "INC-2024-1405",
        "source_type": "access_log",
        "title": "Kubernetes Kubelet Node Alert: Storage Pressure",
        "timestamp": "2024-12-12T02:12:15Z",
        "content": "Cluster: k8s-prod-useast. Node: worker-node-pool-4. Event: DiskPressure condition met (98% root partition utilized). Triggered daemonset: 'log-cleaner-daemon' running script '/usr/local/bin/clean_logs.sh'. Parameter: aggressive_purge=true.",
        "metadata": {"cluster": "k8s-prod-useast", "node": "worker-node-pool-4", "alert": "DiskPressure"}
    },
    {
        "record_id": "LOG-803",
        "case_id": "INC-2024-1405",
        "source_type": "access_log",
        "title": "Terraform Cloud Audit Log: S3 Bucket Policy Modification",
        "timestamp": "2024-12-10T14:30:00Z",
        "content": "Terraform Run #TF-9901 applied by service account 'svc-tf-deployer'. Resource modified: 'aws_s3_bucket.prod_security_audit_logs'. The ObjectLock configuration was inadvertently omitted during an automated modules refactoring, removing WORM write-protection on audit objects.",
        "metadata": {"service": "Terraform", "resource": "aws_s3_bucket.prod_security_audit_logs"}
    },
    {
        "record_id": "MSG-804",
        "case_id": "INC-2024-1405",
        "source_type": "internal_message",
        "title": "Slack Incident Channel: #war-room-outage",
        "timestamp": "2024-12-12T02:22:40Z",
        "content": "Elena Rostova [02:22]: 'P1 ALERT: Entire US-East cluster just went dark! What happened?'\nElena Rostova [02:25]: 'Looking at the storage logs, worker-node-pool-4 hit disk pressure during the Jenkins failover rehearsal. The log cleaner daemon started killing active database sockets!'\nElena Rostova [02:30]: 'Wait... why is our audit S3 bucket empty between 02:14 and now? Did the cleaner script wipe remote logs too?!'",
        "metadata": {"channel": "#war-room-outage", "author": "Elena Rostova"}
    },
    {
        "record_id": "LOG-805",
        "case_id": "INC-2024-1405",
        "source_type": "access_log",
        "title": "Okta SSO & OpenVPN Audit Log: Marcus Brody",
        "timestamp": "2024-12-12T01:45:00Z",
        "content": "User: marcus.brody@novacorp.internal. SSO Authentication: Success (2FA hardware key). VPN Gateway: US-West-Gateway. Session Duration: 01:45 UTC to 03:00 UTC. Terminal History: Executed read-only queries on staging replica 'SELECT count(*) FROM user_analytics_archive;'. No command history found referencing clean_logs.sh or S3 DeleteObject API.",
        "metadata": {"user": "marcus.brody", "vpn_ip": "172.16.88.12", "commands": "SELECT only"}
    },
    {
        "record_id": "LOG-806",
        "case_id": "INC-2024-1405",
        "source_type": "access_log",
        "title": "AWS CloudTrail Event: S3 DeleteObjects Call",
        "timestamp": "2024-12-12T02:18:10Z",
        "content": "EventName: DeleteObjects. Bucket: prod_security_audit_logs. UserIdentity: ARN 'arn:aws:iam::123456789012:role/k8s-node-daemon-role' (Assumed by worker-node-pool-4). SourceIP: 10.100.12.44. UserAgent: aws-sdk-go/v1.44. User was NOT an individual human account.",
        "metadata": {"arn": "arn:aws:iam::123456789012:role/k8s-node-daemon-role", "event": "DeleteObjects"}
    },

    # ------------------ Benign Background Records (Noise & Realism) ------------------
    {
        "record_id": "NOISE-001",
        "case_id": None,
        "source_type": "email",
        "title": "Corporate All-Hands Announcement: Q4 Town Hall",
        "timestamp": "2024-10-10T14:00:00Z",
        "content": "From: HR Communications <hr@novacorp.internal>. All staff are invited to attend our Q4 Town Hall in the main auditorium or via Zoom. Coffee and refreshments will be provided on the 2nd floor.",
        "metadata": {"department": "HR", "category": "General"}
    },
    {
        "record_id": "NOISE-002",
        "case_id": None,
        "source_type": "meeting_note",
        "title": "Meeting Notes: Cafeteria Vendor Selection",
        "timestamp": "2024-10-12T11:00:00Z",
        "content": "Facilities committee reviewed proposals for new coffee vendor in Building B. Consensus reached on Green Roasters LLC starting November 1.",
        "metadata": {"department": "Facilities", "category": "General"}
    },
    {
        "record_id": "NOISE-003",
        "case_id": None,
        "source_type": "access_log",
        "title": "Badge Swipe: Fitness Center Entrance",
        "timestamp": "2024-10-14T07:15:00Z",
        "content": "Employee gym turnstile badge swipe. Badge: #AV-9012 (Alice Vance). Status: Granted.",
        "metadata": {"location": "Building C - Gym"}
    },
    {
        "record_id": "NOISE-004",
        "case_id": None,
        "source_type": "transaction",
        "title": "Routine Office Supply Purchase",
        "timestamp": "2024-11-01T10:00:00Z",
        "content": "Invoice #OFF-2024-118 from Staples Corporate. Amount: ₹35,062.50. Approved by Office Manager. Category: Stationary and Printer Toner.",
        "metadata": {"amount": 35062.50, "currency": "INR", "category": "Supplies"}
    }
]

def save_synthetic_data_files():
    """Generates and writes ground truth and synthetic records to JSON files."""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    gt_file = DATA_DIR / "cases_ground_truth.json"
    with open(gt_file, "w", encoding="utf-8") as f:
        json.dump(CASES_GROUND_TRUTH, f, indent=2)
        
    records_file = DATA_DIR / "synthetic_records.json"
    with open(records_file, "w", encoding="utf-8") as f:
        json.dump(SYNTHETIC_RECORDS, f, indent=2)
        
    print(f"Generated {len(CASES_GROUND_TRUTH)} ground truth cases -> {gt_file}")
    print(f"Generated {len(SYNTHETIC_RECORDS)} synthetic records -> {records_file}")

if __name__ == "__main__":
    save_synthetic_data_files()
