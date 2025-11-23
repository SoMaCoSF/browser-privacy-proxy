<!--
===============================================================================
file_id: SOM-DOC-0004-v1.0.0
name: ARCHITECTURE.md
description: Technical architecture documentation with diagrams
project_id: BROWSER-MIXER-ANON
category: documentation
tags: [architecture, diagrams, technical]
created: 2025-01-23
modified: 2025-01-23
version: 1.0.0
agent_id: AGENT-PRIME-001
execution: Documentation file
===============================================================================
-->

# Privacy Proxy - Technical Architecture

This document provides detailed technical architecture diagrams and explanations of how the Privacy Proxy system works.

## Table of Contents
- [System Overview](#system-overview)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Database Schema](#database-schema)
- [Request Processing Pipeline](#request-processing-pipeline)
- [Fingerprint Rotation Logic](#fingerprint-rotation-logic)
- [Cookie Blocking Mechanism](#cookie-blocking-mechanism)
- [Auto-Blocking System](#auto-blocking-system)

---

## System Overview

```mermaid
graph TB
    subgraph "Browser"
        B[Web Browser]
    end

    subgraph "Privacy Proxy System"
        PS[Proxy Server<br/>127.0.0.1:8080]

        subgraph "Core Components"
            FR[Fingerprint<br/>Randomizer]
            CI[Cookie<br/>Interceptor]
            TB[Traffic<br/>Blocker]
            DH[Database<br/>Handler]
        end

        subgraph "Data Layer"
            DB[(SQLite Database)]
        end

        subgraph "Configuration"
            CF[config.yaml]
        end

        subgraph "Management"
            MC[Management CLI]
        end
    end

    subgraph "Internet"
        WS[Web Servers]
    end

    B -->|HTTP/HTTPS| PS
    PS --> FR
    PS --> CI
    PS --> TB
    FR --> DH
    CI --> DH
    TB --> DH
    DH --> DB
    CF -.->|Config| PS
    MC -->|Query/Export| DB
    PS -->|Modified Request| WS
    WS -->|Response| PS
    PS -->|Filtered Response| B

    style PS fill:#4CAF50
    style FR fill:#2196F3
    style CI fill:#FF9800
    style TB fill:#F44336
    style DB fill:#9C27B0
```

---

## Component Architecture

```mermaid
classDiagram
    class PrivacyProxyAddon {
        +request_count: int
        +request(flow)
        +response(flow)
        +running()
        +done()
    }

    class FingerprintRandomizer {
        +db: DatabaseHandler
        +config: dict
        +current_fingerprint: dict
        +rotation_count: int
        +generate_fingerprint(trigger)
        +should_rotate(trigger_type)
        +apply_to_headers(headers)
        -_random_user_agent()
        -_random_language()
        -_random_encoding()
    }

    class CookieInterceptor {
        +db: DatabaseHandler
        +config: dict
        +blocked_count: int
        +tracking_patterns: list
        +should_block_cookie(domain, name)
        +process_request_cookies(flow)
        +process_response_cookies(flow)
        +get_stats()
    }

    class TrafficBlocker {
        +db: DatabaseHandler
        +config: dict
        +blocked_requests: int
        +block_patterns: list
        +should_block_domain(domain)
        +should_block_ip(ip)
        +process_request(flow)
        +export_blocklist(format)
    }

    class DatabaseHandler {
        +db_path: str
        +local: threading.local
        +log_cookie_traffic()
        +log_fingerprint_rotation()
        +log_request()
        +add_tracking_domain()
        +add_tracking_ip()
        +is_domain_blocked()
        +is_ip_blocked()
        +is_whitelisted()
        +get_statistics()
    }

    PrivacyProxyAddon --> FingerprintRandomizer
    PrivacyProxyAddon --> CookieInterceptor
    PrivacyProxyAddon --> TrafficBlocker
    FingerprintRandomizer --> DatabaseHandler
    CookieInterceptor --> DatabaseHandler
    TrafficBlocker --> DatabaseHandler
```

---

## Data Flow

### Request Flow (Outgoing)

```mermaid
sequenceDiagram
    participant Browser
    participant Proxy as Privacy Proxy
    participant TB as Traffic Blocker
    participant FR as Fingerprint Randomizer
    participant CI as Cookie Interceptor
    participant DB as Database
    participant Web as Web Server

    Browser->>Proxy: HTTP/HTTPS Request

    Proxy->>TB: Check if should block
    TB->>DB: Check blocklist

    alt Domain/IP Blocked
        TB->>DB: Log blocked request
        TB->>Proxy: Kill connection
        Proxy-->>Browser: Connection refused
    else Allowed
        Proxy->>FR: Should rotate fingerprint?
        FR->>FR: Check rotation mode

        alt Should Rotate
            FR->>FR: Generate new fingerprint
            FR->>DB: Log rotation
        end

        FR->>Proxy: Apply fingerprint to headers

        Proxy->>CI: Process request cookies
        CI->>DB: Check whitelist

        alt Cookies present
            CI->>CI: Check block patterns
            CI->>DB: Log cookie attempts
            CI->>Proxy: Remove blocked cookies
        end

        Proxy->>DB: Log request
        Proxy->>Web: Forward modified request
    end
```

### Response Flow (Incoming)

```mermaid
sequenceDiagram
    participant Web as Web Server
    participant Proxy as Privacy Proxy
    participant CI as Cookie Interceptor
    participant DB as Database
    participant Browser

    Web->>Proxy: HTTP Response
    Proxy->>CI: Process response

    alt Set-Cookie headers present
        CI->>DB: Check whitelist
        CI->>CI: Check block patterns
        CI->>DB: Log cookie attempts
        CI->>DB: Track domain/IP
        CI->>Proxy: Remove Set-Cookie headers
    end

    Proxy->>Browser: Filtered response
```

---

## Database Schema

```mermaid
erDiagram
    tracking_domains ||--o{ tracking_ips : "associated_domain"
    tracking_domains ||--o{ cookie_traffic : "domain"
    fingerprint_rotations ||--o{ request_log : "fingerprint_id"

    tracking_domains {
        int id PK
        text domain UK
        timestamp first_seen
        timestamp last_seen
        int hit_count
        boolean blocked
        text category
        text notes
    }

    tracking_ips {
        int id PK
        text ip_address UK
        timestamp first_seen
        timestamp last_seen
        int hit_count
        boolean blocked
        text associated_domain FK
        text notes
    }

    cookie_traffic {
        int id PK
        timestamp timestamp
        text domain
        text cookie_name
        text cookie_value
        text ip_address
        text request_url
        boolean blocked
    }

    fingerprint_rotations {
        int id PK
        timestamp timestamp
        text user_agent
        text platform
        text accept_language
        text accept_encoding
        text rotation_trigger
    }

    request_log {
        int id PK
        timestamp timestamp
        text method
        text url
        text host
        text ip_address
        int fingerprint_id FK
        boolean blocked
        text block_reason
    }

    whitelist {
        int id PK
        text domain UK
        timestamp added
        text reason
    }

    diary_entries {
        int id PK
        timestamp timestamp
        text entry_type
        text title
        text content
        text agent_id
    }
```

---

## Request Processing Pipeline

```mermaid
flowchart TD
    Start([Browser Request]) --> CheckBlock{Check Traffic Blocker}

    CheckBlock -->|Whitelisted| FingerprintCheck
    CheckBlock -->|Domain Blocked| Block1[Kill Connection]
    CheckBlock -->|IP Blocked| Block1
    CheckBlock -->|Pattern Match| Block1
    CheckBlock -->|Not Blocked| FingerprintCheck

    Block1 --> LogBlock[Log Blocked Request]
    LogBlock --> End1([Return 403/Kill])

    FingerprintCheck{Should Rotate<br/>Fingerprint?} -->|Yes| GenFingerprint[Generate New<br/>Fingerprint]
    FingerprintCheck -->|No| UseFingerprint[Use Current<br/>Fingerprint]

    GenFingerprint --> LogFingerprint[Log to DB]
    LogFingerprint --> ApplyFingerprint[Apply to Headers]
    UseFingerprint --> ApplyFingerprint

    ApplyFingerprint --> CheckCookies{Cookies in<br/>Request?}

    CheckCookies -->|Yes| ParseCookies[Parse Cookies]
    CheckCookies -->|No| LogRequest

    ParseCookies --> CheckEachCookie{For Each Cookie}
    CheckEachCookie --> CheckWhitelist{Whitelisted?}

    CheckWhitelist -->|Yes| AllowCookie[Allow Cookie]
    CheckWhitelist -->|No| CheckPattern{Matches<br/>Pattern?}

    CheckPattern -->|Yes| BlockCookie[Block Cookie]
    CheckPattern -->|No, but block_all=true| BlockCookie
    CheckPattern -->|No, block_all=false| AllowCookie

    BlockCookie --> LogCookie[Log to DB]
    LogCookie --> TrackDomain[Track Domain/IP]
    AllowCookie --> LogRequest
    TrackDomain --> LogRequest

    LogRequest[Log Request] --> ForwardRequest[Forward to Server]
    ForwardRequest --> End2([Wait for Response])

    style Start fill:#4CAF50
    style End1 fill:#F44336
    style End2 fill:#2196F3
    style Block1 fill:#F44336
    style BlockCookie fill:#FF9800
```

---

## Fingerprint Rotation Logic

```mermaid
stateDiagram-v2
    [*] --> NoFingerprint

    NoFingerprint --> GenerateFingerprint: First Request

    GenerateFingerprint --> Active: Fingerprint Created

    Active --> CheckRotationMode: New Request

    CheckRotationMode --> EveryRequest: mode=every_request
    CheckRotationMode --> CheckInterval: mode=interval
    CheckRotationMode --> CheckNewTab: mode=new_tab
    CheckRotationMode --> CheckLaunch: mode=launch

    EveryRequest --> GenerateFingerprint: Always Rotate

    CheckInterval --> GenerateFingerprint: Time > threshold
    CheckInterval --> Active: Time <= threshold

    CheckNewTab --> GenerateFingerprint: New Tab Detected
    CheckNewTab --> Active: Same Tab

    CheckLaunch --> Active: Keep Current

    GenerateFingerprint --> LogToDB: New Fingerprint
    LogToDB --> Active: Fingerprint Logged

    Active --> ApplyHeaders: Use Fingerprint
    ApplyHeaders --> [*]: Headers Modified
```

---

## Cookie Blocking Mechanism

```mermaid
flowchart TD
    Start([Cookie Detected]) --> CheckDirection{Request or<br/>Response?}

    CheckDirection -->|Request| ParseReqCookie[Parse Cookie Header]
    CheckDirection -->|Response| ParseRespCookie[Parse Set-Cookie Header]

    ParseReqCookie --> ExtractCookies[Extract Cookie Names/Values]
    ParseRespCookie --> ExtractCookies

    ExtractCookies --> ForEach{For Each Cookie}

    ForEach --> CheckWhitelist{Domain<br/>Whitelisted?}

    CheckWhitelist -->|Yes| AllowCookie[Allow Cookie]
    CheckWhitelist -->|No| CheckBlockAll{block_all<br/>enabled?}

    CheckBlockAll -->|Yes| BlockCookie[Block Cookie]
    CheckBlockAll -->|No| CheckPatterns{Matches Tracking<br/>Pattern?}

    CheckPatterns -->|Yes| BlockCookie
    CheckPatterns -->|No| AllowCookie

    BlockCookie --> LogBlocked[Log to cookie_traffic<br/>blocked=1]
    AllowCookie --> LogAllowed[Log to cookie_traffic<br/>blocked=0]

    LogBlocked --> TrackDomain[Add to tracking_domains]
    LogAllowed --> Continue

    TrackDomain --> TrackIP[Add to tracking_ips]
    TrackIP --> CheckAutoBlock{Hit Count >=<br/>Threshold?}

    CheckAutoBlock -->|Yes| MarkBlocked[Mark domain/IP<br/>as blocked]
    CheckAutoBlock -->|No| Continue

    MarkBlocked --> RemoveFromRequest[Remove from<br/>Request/Response]
    Continue --> Keep[Keep in<br/>Request/Response]

    RemoveFromRequest --> End([Cookie Blocked])
    Keep --> End2([Cookie Allowed])

    style BlockCookie fill:#F44336
    style AllowCookie fill:#4CAF50
    style End fill:#F44336
    style End2 fill:#4CAF50
```

---

## Auto-Blocking System

```mermaid
flowchart TD
    Start([Tracking Event]) --> Identify{Event Type}

    Identify -->|Cookie Attempt| AddDomain[Add/Update<br/>tracking_domains]
    Identify -->|IP Connection| AddIP[Add/Update<br/>tracking_ips]
    Identify -->|Pattern Match| ImmediateBlock[Immediate Block]

    AddDomain --> IncrementDomain[Increment hit_count]
    AddIP --> IncrementIP[Increment hit_count]

    IncrementDomain --> CheckDomainThreshold{hit_count >=<br/>threshold?}
    IncrementIP --> CheckIPThreshold{hit_count >=<br/>threshold?}

    CheckDomainThreshold -->|Yes| AutoBlockDomain[Set blocked=1<br/>for domain]
    CheckDomainThreshold -->|No| LogOnly1[Log Only]

    CheckIPThreshold -->|Yes| AutoBlockIP[Set blocked=1<br/>for IP]
    CheckIPThreshold -->|No| LogOnly2[Log Only]

    ImmediateBlock --> AddToBlocklist[Add to blocklist<br/>with category]

    AutoBlockDomain --> NotifyDomain[Log: Auto-blocked<br/>domain]
    AutoBlockIP --> NotifyIP[Log: Auto-blocked<br/>IP]
    AddToBlocklist --> NotifyPattern[Log: Pattern-blocked]

    NotifyDomain --> UpdateDB1[Update Database]
    NotifyIP --> UpdateDB2[Update Database]
    NotifyPattern --> UpdateDB3[Update Database]
    LogOnly1 --> UpdateDB4[Update Database]
    LogOnly2 --> UpdateDB5[Update Database]

    UpdateDB1 --> FutureRequests[Block Future<br/>Requests]
    UpdateDB2 --> FutureRequests
    UpdateDB3 --> FutureRequests
    UpdateDB4 --> End1([Allow for Now])
    UpdateDB5 --> End1

    FutureRequests --> End2([Blocked])

    style ImmediateBlock fill:#F44336
    style AutoBlockDomain fill:#FF5722
    style AutoBlockIP fill:#FF5722
    style End2 fill:#F44336
    style End1 fill:#4CAF50
```

---

## Privacy Levels Comparison

```mermaid
graph LR
    subgraph "Maximum Privacy (Paranoid)"
        MP1[Every Request<br/>New Fingerprint]
        MP2[Block ALL Cookies]
        MP3[Auto-block<br/>Threshold: 1]
        MP4[Strip All Tracking<br/>Headers]
    end

    subgraph "Balanced Privacy (Recommended)"
        BP1[Interval Rotation<br/>5 minutes]
        BP2[Block ALL Cookies]
        BP3[Auto-block<br/>Threshold: 3]
        BP4[Strip Tracking<br/>Headers]
    end

    subgraph "Minimal Privacy (Testing)"
        LP1[Launch Rotation<br/>Once per session]
        LP2[Log Cookies<br/>Don't Block]
        LP3[No Auto-block<br/>Just Log]
        LP4[Keep Most<br/>Headers]
    end

    Privacy[Privacy Level] -->|Highest| MP1
    Privacy -->|Medium| BP1
    Privacy -->|Lowest| LP1

    Compatibility[Site Compatibility] -->|Lowest| MP1
    Compatibility -->|Medium| BP1
    Compatibility -->|Highest| LP1

    Performance[Performance] -->|Slower| MP1
    Performance -->|Moderate| BP1
    Performance -->|Faster| LP1

    style MP1 fill:#F44336
    style MP2 fill:#F44336
    style MP3 fill:#F44336
    style MP4 fill:#F44336
    style BP1 fill:#FF9800
    style BP2 fill:#FF9800
    style BP3 fill:#FF9800
    style BP4 fill:#FF9800
    style LP1 fill:#4CAF50
    style LP2 fill:#4CAF50
    style LP3 fill:#4CAF50
    style LP4 fill:#4CAF50
```

---

## Management CLI Architecture

```mermaid
flowchart TD
    CLI([manage.py]) --> ParseCmd{Parse Command}

    ParseCmd -->|stats| GetStats[Get Statistics<br/>from DB]
    ParseCmd -->|domains| GetDomains[Query tracking_domains<br/>ORDER BY hit_count]
    ParseCmd -->|ips| GetIPs[Query tracking_ips<br/>ORDER BY hit_count]
    ParseCmd -->|cookies| GetCookies[Query cookie_traffic<br/>ORDER BY timestamp]
    ParseCmd -->|requests| GetRequests[Query request_log<br/>ORDER BY timestamp]
    ParseCmd -->|export| ExportList[Generate Blocklist]
    ParseCmd -->|whitelist| AddWhitelist[Add to whitelist]
    ParseCmd -->|block| AddBlock[Add to blocklist]

    GetStats --> DisplayStats[Display Formatted<br/>Statistics]
    GetDomains --> DisplayTable1[Display Table]
    GetIPs --> DisplayTable2[Display Table]
    GetCookies --> DisplayTable3[Display Table]
    GetRequests --> DisplayTable4[Display Table]

    ExportList --> ChooseFormat{Format?}
    ChooseFormat -->|hosts| HostsFormat[0.0.0.0 domain]
    ChooseFormat -->|text| TextFormat[Plain List]
    ChooseFormat -->|list| JSONFormat[JSON Object]

    HostsFormat --> WriteFile[Write to File]
    TextFormat --> WriteFile
    JSONFormat --> WriteFile

    AddWhitelist --> UpdateWL[INSERT INTO whitelist]
    AddBlock --> UpdateBL[INSERT INTO tracking_domains]

    WriteFile --> Success1([Export Complete])
    UpdateWL --> Success2([Added to Whitelist])
    UpdateBL --> Success3([Added to Blocklist])
    DisplayStats --> Done([Display Complete])
    DisplayTable1 --> Done
    DisplayTable2 --> Done
    DisplayTable3 --> Done
    DisplayTable4 --> Done

    style CLI fill:#2196F3
    style Success1 fill:#4CAF50
    style Success2 fill:#4CAF50
    style Success3 fill:#F44336
```

---

## Thread Safety Model

```mermaid
sequenceDiagram
    participant T1 as Thread 1
    participant T2 as Thread 2
    participant DBH as DatabaseHandler
    participant TLS as threading.local
    participant DB as SQLite DB

    Note over DBH: Uses thread-local storage<br/>for connections

    T1->>DBH: log_request()
    DBH->>TLS: Get thread-local conn

    alt Connection exists for T1
        TLS-->>DBH: Return existing conn
    else No connection for T1
        TLS->>DB: sqlite3.connect()
        DB-->>TLS: New connection
        TLS-->>DBH: Return new conn
    end

    DBH->>DB: Execute INSERT
    DB-->>DBH: Success
    DBH-->>T1: Done

    par Concurrent Access
        T2->>DBH: log_cookie_traffic()
        DBH->>TLS: Get thread-local conn

        alt Connection exists for T2
            TLS-->>DBH: Return existing conn
        else No connection for T2
            TLS->>DB: sqlite3.connect()
            DB-->>TLS: New connection (separate from T1)
            TLS-->>DBH: Return new conn
        end

        DBH->>DB: Execute INSERT
        DB-->>DBH: Success
        DBH-->>T2: Done
    end

    Note over T1,DB: Each thread has its own<br/>SQLite connection
```

---

## Configuration Loading Flow

```mermaid
flowchart TD
    Start([start_proxy.py]) --> ParseArgs[Parse CLI Arguments]

    ParseArgs --> CheckConfig{Config File<br/>Exists?}

    CheckConfig -->|Yes| LoadConfig[Load config.yaml]
    CheckConfig -->|No| CreateDefault[Create Default Config]

    CreateDefault --> LoadConfig

    LoadConfig --> MergeArgs[Merge CLI args<br/>with config]

    MergeArgs --> InitDB[Initialize Database]
    InitDB --> CreateSchema[Create/Update Schema]

    CreateSchema --> InitComponents[Initialize Components]

    InitComponents --> InitFR[FingerprintRandomizer<br/>db, config]
    InitComponents --> InitCI[CookieInterceptor<br/>db, config]
    InitComponents --> InitTB[TrafficBlocker<br/>db, config]

    InitFR --> LoadWhitelist[Load Whitelist<br/>from Config]
    InitCI --> LoadWhitelist
    InitTB --> LoadWhitelist

    LoadWhitelist --> BuildMitmArgs[Build mitmproxy<br/>Arguments]

    BuildMitmArgs --> LaunchMitm[Launch mitmdump<br/>with addon]

    LaunchMitm --> Running([Proxy Running])

    style Start fill:#4CAF50
    style Running fill:#2196F3
```

---

## System Interactions

```mermaid
graph TB
    subgraph "User Layer"
        U1[User<br/>Web Browser]
        U2[User<br/>Terminal]
    end

    subgraph "Application Layer"
        PS[Privacy Proxy<br/>start_proxy.py]
        MC[Management CLI<br/>manage.py]
    end

    subgraph "Component Layer"
        FR[Fingerprint<br/>Randomizer]
        CI[Cookie<br/>Interceptor]
        TB[Traffic<br/>Blocker]
    end

    subgraph "Data Access Layer"
        DH[Database<br/>Handler]
    end

    subgraph "Storage Layer"
        DB[(SQLite DB)]
        CF[config.yaml]
        LF[Logs]
    end

    subgraph "External"
        WEB[Internet]
    end

    U1 <-->|HTTP/HTTPS| PS
    U2 <-->|Commands| MC

    PS --> FR
    PS --> CI
    PS --> TB
    PS <-->|Requests| WEB

    FR --> DH
    CI --> DH
    TB --> DH
    MC --> DH

    DH --> DB

    PS -.->|Read| CF
    PS -.->|Write| LF
    MC -.->|Read| CF

    style U1 fill:#E1F5FE
    style U2 fill:#E1F5FE
    style DB fill:#9C27B0
    style WEB fill:#FFF9C4
```

---

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        DEV[Developer Machine]

        subgraph "Virtual Environment"
            VENV[.venv<br/>Python 3.12+]
            PKG[Dependencies<br/>mitmproxy, fake-useragent]
        end

        subgraph "Project Files"
            SRC[Source Code<br/>*.py]
            CFG[config.yaml]
            SCH[schema.sql]
        end
    end

    subgraph "Runtime Environment"
        PROXY[Privacy Proxy<br/>Process]

        subgraph "Data Storage"
            DBS[(browser_privacy.db)]
            LOGS[logs/*.log]
        end

        subgraph "mitmproxy"
            CERT[CA Certificate]
            MITM[mitmproxy Core]
        end
    end

    subgraph "Browser"
        BR[Browser Process]
        BRCFG[Proxy Settings<br/>127.0.0.1:8080]
    end

    DEV --> VENV
    VENV --> PKG
    DEV --> SRC
    DEV --> CFG
    DEV --> SCH

    SRC --> PROXY
    CFG --> PROXY
    SCH --> DBS

    PROXY --> MITM
    PROXY --> DBS
    PROXY --> LOGS
    MITM --> CERT

    BR --> BRCFG
    BRCFG -->|Proxy Traffic| PROXY
    CERT -.->|Install| BR

    style DEV fill:#E3F2FD
    style PROXY fill:#4CAF50
    style BR fill:#FFF9C4
```

---

## Summary

The Privacy Proxy system is built on a modular architecture with clear separation of concerns:

1. **Proxy Layer**: mitmproxy handles HTTP/HTTPS interception
2. **Component Layer**: Specialized modules for fingerprinting, cookie blocking, traffic filtering
3. **Data Layer**: Thread-safe SQLite database for persistence and analysis
4. **Management Layer**: CLI tools for monitoring and configuration

The system processes each request through a pipeline that:
- Checks for blocked domains/IPs
- Rotates browser fingerprints based on configuration
- Blocks cookies bidirectionally (request and response)
- Logs all activity for analysis
- Auto-blocks trackers based on behavior patterns

This architecture provides maximum privacy while maintaining flexibility through configuration options.
