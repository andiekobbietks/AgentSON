# AgentSON + Diabetes Monitoring: Personas & User Stories

**Date:** 05 July 2026  
**Research Sources:** Grand View Research, MarkWide Research, Diabetes UK, Glooko Global Report, WHO Africa, Akoma Pa Program

---

## Market Context

| Statistic | Value | Source |
|-----------|-------|--------|
| UK CGM market (2026) | £1.2-1.5 billion | IndexBox |
| UK CGM market (2033) | $1.95 billion | Grand View Research |
| Global CGM readings (2025) | 60.1 billion | Glooko |
| NHS CGM users (England) | 200,000+ | NHS Digital |
| Ghana diabetes prevalence | 2.8-4.0% | WHO Africa |
| West Africa CGM access | <1% | Akoma Pa Program |

---

## Key Clusters

### Cluster 1: UK Carer-Led Diabetes Management
### Cluster 2: NHS Clinical Integration
### Cluster 3: West African Digital Health
### Cluster 4: Developer/Engineer Tooling

---

## Cluster 1: UK Carer-Led Diabetes Management

### Persona 1.1: Andrea (Carer)
| Attribute | Detail |
|-----------|--------|
| **Role** | Primary carer for mother |
| **Location** | Mansfield, Nottinghamshire |
| **Tech level** | Intermediate (Python, CLI) |
| **Pain points** | No real-time visibility, manual USB reads, can't be there 24/7 |
| **Goal** | Know mother's glucose remotely, get alerts, share with doctors |

**User Stories:**

| ID | Story | Priority |
|----|-------|----------|
| US-1.1.1 | As Andrea, I want to read mother's sensor remotely so I don't need to be physically present | High |
| US-1.1.2 | As Andrea, I want WhatsApp voice alerts when glucose is low/high so I can respond immediately | High |
| US-1.1.3 | As Andrea, I want to see glucose trends on my TV so I can monitor while working | Medium |
| US-1.1.4 | As Andrea, I want to export glucose reports for GP appointments so I can show patterns | High |
| US-1.1.5 | As Andrea, I want to search across AI sessions to find past discussions about mother's care | Medium |

---

### Persona 1.2: Mother (Patient)
| Attribute | Detail |
|-----------|--------|
| **Age** | Elderly |
| **Condition** | Type 2 diabetes, post-STEMI, post-stroke |
| **Tech level** | Low (uses phone for calls only) |
| **Pain points** | Can't self-manage, forgets medications, no family nearby |
| **Goal** | Stay safe, avoid hospital admissions |

**User Stories:**

| ID | Story | Priority |
|----|-------|----------|
| US-1.2.1 | As mother, I want my sensor to work automatically so I don't have to do anything | High |
| US-1.2.2 | As mother, I want voice alerts on my phone when something is wrong | High |
| US-1.2.3 | As mother, I want my daughter to know if I'm low even when she's not here | High |
| US-1.2.4 | As mother, I want simple reminders for medications | Medium |

---

## Cluster 2: NHS Clinical Integration

### Persona 2.1: GP/Doctor
| Attribute | Detail |
|-----------|--------|
| **Role** | General Practitioner |
| **Location** | Churchside Medical Practice, Mansfield |
| **Pain points** | No real-time data, relies on patient recall, 10-minute appointments |
| **Goal** | Make evidence-based decisions quickly |

**User Stories:**

| ID | Story | Priority |
|----|-------|----------|
| US-2.1.1 | As a GP, I want to see glucose trends during consultations so I can adjust medications | High |
| US-2.1.2 | As a GP, I want exported reports in standard format so I can import to EMIS/SystmOne | High |
| US-2.1.3 | As a GP, I want alerts when patients are out of range so I can intervene early | Medium |
| US-2.1.4 | As a GP, I want to compare my practice's outcomes with national data | Low |

---

### Persona 2.2: Diabetes Nurse Specialist
| Attribute | Detail |
|-----------|--------|
| **Role** | Diabetes specialist nurse |
| **Pain points** | Too many patients, no remote monitoring, reactive care |
| **Goal** | Proactive management, reduce complications |

**User Stories:**

| ID | Story | Priority |
|----|-------|----------|
| US-2.2.1 | As a nurse, I want dashboard views of all my patients' glucose so I can prioritise | High |
| US-2.2.2 | As a nurse, I want to see HbA1c trends alongside CGM data | Medium |
| US-2.2.3 | As a nurse, I want to send voice notes to patients with advice | Medium |

---

### Persona 2.3: NHS Commissioner
| Attribute | Detail |
|-----------|--------|
| **Role** | ICB decision-maker |
| **Pain points** | Rising diabetes costs, hospital admissions, health inequalities |
| **Goal** | Reduce costs, improve outcomes, close inequality gaps |

**User Stories:**

| ID | Story | Priority |
|----|-------|----------|
| US-2.3.1 | As a commissioner, I want cost-benefit data showing CGM reduces admissions | High |
| US-2.3.2 | As a commissioner, I want to see inequality metrics by ethnicity and deprivation | High |
| US-2.3.3 | As a commissioner, I want scalable solutions that work across my ICB | Medium |

---

## Cluster 3: West African Digital Health

### Persona 3.1: Community Health Worker (Ghana)
| Attribute | Detail |
|-----------|--------|
| **Role** | Community-based screening and monitoring |
| **Location** | Rural/urban Ghana |
| **Tech level** | Basic smartphone |
| **Pain points** | No CGM access, limited supplies, paper-based records |
| **Goal** | Screen and monitor diabetes in community |

**User Stories:**

| ID | Story | Priority |
|----|-------|----------|
| US-3.1.1 | As a CHW, I want to screen for diabetes using a smartphone app | High |
| US-3.1.2 | As a CHW, I want to track patients remotely without clinic visits | High |
| US-3.1.3 | As a CHW, I want voice alerts in local language (Twi, Ga, Ewe) | High |
| US-3.1.4 | As a CHW, I want to sync data when internet is available | Medium |

---

### Persona 3.2: Patient in West Africa
| Attribute | Detail |
|-----------|--------|
| **Location** | Ghana, Nigeria, etc. |
| **Tech level** | Basic phone (feature phone possible) |
| **Pain points** | Can't afford CGM, no specialists nearby, complications undetected |
| **Goal** | Manage diabetes without travelling long distances |

**User Stories:**

| ID | Story | Priority |
|----|-------|----------|
| US-3.2.1 | As a patient, I want SMS reminders for medications | High |
| US-3.2.2 | As a patient, I want to know if my readings are dangerous | High |
| US-3.2.3 | As a patient, I want to share data with my doctor remotely | Medium |
| US-3.2.4 | As a patient, I want voice instructions in my language | High |

---

### Persona 3.3: NGO/Program Manager (Akoma Pa)
| Attribute | Detail |
|-----------|--------|
| **Role** | Program manager for diabetes intervention |
| **Organization** | CHAG, Novartis, Medtronic LABS, GIZ |
| **Pain points** | Fragmented data, no interoperability, hard to measure impact |
| **Goal** | Scale digital health interventions across regions |

**User Stories:**

| ID | Story | Priority |
|----|-------|----------|
| US-3.3.1 | As a program manager, I want aggregated dashboard across 85 facilities | High |
| US-3.3.2 | As a program manager, I want cost-consequence analysis data | High |
| US-3.3.3 | As a program manager, I want interoperable data format (AgentSON) | Medium |

---

## Cluster 4: Developer/Engineer Tooling

### Persona 4.1: AI/ML Engineer
| Attribute | Detail |
|-----------|--------|
| **Role** | Building AI tools for diabetes |
| **Pain points** | Can't export sessions, can't search across tools, no standard format |
| **Goal** | Portable, searchable, hydrateable session data |

**User Stories:**

| ID | Story | Priority |
|----|-------|----------|
| US-4.1.1 | As an engineer, I want to export opencode sessions to AgentSON | High |
| US-4.1.2 | As an engineer, I want to search across all my AI sessions | High |
| US-4.1.3 | As an engineer, I want to hydrate context from one tool to another | Medium |
| US-4.1.4 | As an engineer, I want to build glucose prediction models on AgentSON data | High |

---

### Persona 4.2: Data Scientist
| Attribute | Detail |
|-----------|--------|
| **Role** | Analysing glucose patterns |
| **Pain points** | Messy CSVs, no standard schema, hard to combine datasets |
| **Goal** | Clean, structured, queryable glucose data |

**User Stories:**

| ID | Story | Priority |
|----|-------|----------|
| US-4.2.1 | As a data scientist, I want glucose data in structured JSON format | High |
| US-4.2.2 | As a data scientist, I want to query across multiple patients | Medium |
| US-4.2.3 | As a data scientist, I want to train models on AgentSON glucose data | High |

---

## NHS Inequality Data

From Diabetes UK study (March 2026):

| Finding | Impact |
|---------|--------|
| CGM prescribing higher in White areas | Black/South Asian patients less likely to receive CGM |
| Deprivation + ethnicity = compounded inequality | Type 2 patients most affected |
| ICB policy variation | NICE guidelines not uniformly applied |
| Our project addresses | Free, open-source, no eligibility criteria |

---

## West Africa Context

From Akoma Pa Program and WHO Africa:

| Statistic | Value |
|-----------|-------|
| Ghana diabetes prevalence | 2.8-4.0% |
| West Africa CGM access | <1% |
| NCDs as % of Ghana mortality | 45% |
| Mobile phone penetration | High (opportunity) |
| Our project addresses | Voice alerts, SMS reminders, offline-capable |

---

## Prioritised Roadmap

### Phase 1: UK Carer (Months 1-3)
- Real-time glucose monitoring via Juggluco + Nightscout
- WhatsApp voice alerts
- GP report export

### Phase 2: NHS Integration (Months 4-6)
- FHIR API connection
- Clinical dashboard
- Cost-benefit evidence

### Phase 3: West Africa (Months 7-12)
- SMS reminders
- Voice alerts in local languages
- Community health worker app
- Offline capability

### Phase 4: AgentSON Platform (Ongoing)
- Cross-tool session portability
- Glucose prediction models
- Multi-patient analytics

---

## NHS Funding Alignment

| Funding Stream | Our Alignment |
|----------------|---------------|
| NIHR i4i PDA | Evidence generation, carer-led innovation |
| SBRI Healthcare | Digital health, NHS integration |
| NIA 2027 | AI for health, inequality focus |
| Digital Notts | Local innovation, NHS partnership |

---

## Key Differentiators

| Differentiator | NHS | West Africa | Commercial |
|----------------|-----|-------------|------------|
| **Free/open source** | ✅ | ✅ | ❌ |
| **No eligibility criteria** | ✅ | ✅ | ❌ |
| **Carer-led** | ✅ | ✅ | ❌ |
| **Voice alerts** | ✅ | ✅ | Partial |
| **Offline capable** | ✅ | ✅ | ❌ |
| **AgentSON format** | ✅ | ✅ | ❌ |
| **NHS FHIR ready** | ✅ | ❌ | Partial |

---

*"This isn't just a tool for one patient. It's a blueprint for how carers, clinicians, and communities can monitor diabetes without depending on expensive, proprietary systems."*
