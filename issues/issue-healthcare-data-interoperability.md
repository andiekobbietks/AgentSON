# Issue: Healthcare data interoperability — FreeStyle Libre context

## The problem

Glucose data from FreeStyle Libre 2 is generated on-device, routed through Abbott's LibreView cloud, and export is manual, rate-limited, and UI-bound. Third-party interoperability is intentionally constrained.

## Legal context (what GDPR actually says)

### GDPR Article 20 — Right to data portability

> "The data subject shall have the right to receive the personal data concerning him or her, which he or she has provided to a controller, in a structured, commonly used and machine-readable format"
> — [EUR-Lex, Regulation (EU) 2016/679](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32016R0679)

### What GDPR requires vs. doesn't require

| Requirement | Mandated? | Source |
|---|---|---|
| Export in structured, machine-readable format (CSV, JSON, XML) | **Yes** | Art. 20(1) |
| Direct controller-to-controller transmission | **Conditional** — "where technically feasible" | Art. 20(2) |
| APIs specifically | **No** — APIs are one implementation method, not a requirement | ICO guidance |
| Interoperable formats | **Encouraged**, not required | Recital 68 |

### ICO guidance

> "Machine-readable data can be made directly available to applications that request that data over the web. This is undertaken by means of an application programming interface ('API'). **If you are able** to implement such a system then you can facilitate data exchanges."
> — [ICO, Right to data portability](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-data-portability)

The ICO uses the conditional "if you are able" — APIs are presented as a helpful option, not a mandate.

### GDPR compliance baseline

CSV export usually already satisfies compliance baseline. Even if it is annoying, manual, or behind a login.

## The stronger angle: healthcare interoperability

### FDA position on interoperability

> "Interoperable devices with the ability to share information across systems and platforms can: Improve patient care, Reduce errors and adverse events, Encourage innovation, and Enable more diverse study datasets."
> — [FDA, Medical Device Interoperability](https://www.fda.gov/medical-devices/digital-health-center-excellence/medical-device-interoperability)

### Clinical decision latency

> "Every hour that passes before sepsis is diagnosed and treated, the risk of mortality increases by 7.6%. Real-time and contextual information is critical here."
> — [Innovaccer](https://innovaccer.com/blogs/data-fidelity-and-latency-all-things-clinical)

> "When latency becomes chronic, clinicians compensate with inefficient workarounds that can degrade patient safety. Clinical systems latency is no longer an IT nuisance — it's a patient safety issue."
> — [Silk](https://silk.us/blog/when-data-performance-becomes-a-patient-care-issue/)

### NHS FHIR mandate

> "Lack of access to an up-to-date medical history can affect the way patients are treated. The impact on treatment, particularly in an emergency situation, can be significant."
> — [NHS England](https://www.england.nhs.uk/long-read/interoperability)

> "The NHS uses FHIR to make integration with APIs and services easier. FHIR is the global industry standard for passing healthcare data between systems."
> — [NHS England](https://www.england.nhs.uk/long-read/interoperability)

### CMS Interop Rule (US)

> "ONC-certified health IT must expose a FHIR R4 Patient Access API giving patients access to all their EHI at no cost. Organizations that interfere with EHI access face civil monetary penalties up to $1 million per violation."
> — [ONC Cures Act Final Rule](https://www.healthit.gov/information-blocking/)

### Information blocking is illegal (US)

> "The information blocking provisions require that patients and their physicians be given immediate electronic access to significant portions of the patient's EHI upon request, unless an exception applies."
> — [Texas Medical Association](https://www.texmed.org/21stCCA)

### Real-world litigation

> "Health Gorilla filed a motion to dismiss a lawsuit brought earlier this year by Epic and several health systems alleging improper access to patient records. The motion called Epic's lawsuit 'an attack on interoperability.'"
> — [MedCity News, March 2026](https://medcitynews.com/2026/03/health-gorilla-epic-data-interoperability/)

### Clinical outcomes from interoperability

> "Intermountain Health medical informaticists have developed a novel and interoperable technology platform... In the studies, we demonstrated a 36% relative decrease in 30-day mortality for pneumonia patients, which is more than 100 lives saved annually."
> — [Intermountain Health](https://news.intermountainhealth.org/intermountain-health-develops-real-time-interoperable-technology-platform-which-integrates-artificial-intelligence-into-clinical-workflows-to-help-clinicians-better-diagnose-and-treat-patients)

## What Abbott doesn't have (and why)

It's not just negligence. It's usually:
- Regulatory liability risk (medical device data misuse)
- Clinical interpretation control (they don't want 3rd-party misreads)
- Cybersecurity surface reduction
- Commercial lock-in (yes, also this)

The absence of APIs is not automatically a compliance failure — it's a design trade-off under regulated constraints.

## Realistic outcomes

| Outcome | Likelihood |
|---|---|
| Full API mandate | Very unlikely |
| Improved export UX | Possible |
| Clarification of portability rights | Possible |
| ICO dismissal ("compliant enough") | Likely baseline |
| Informal pressure / best practice guidance | Plausible |

## AgentSON's role

AgentSON is not a law enforcement tool. It's an interoperability representation layer. The gap it addresses:

> **Health data portability is legally recognized but architecturally not standardized.**

Law says "you own your data." Systems still behave like "data is leased via interface." That tension is why formats like AgentSON matter — not as GDPR enforcement, but as interoperability representations of system behaviour over time.

## Sources

1. GDPR Article 20: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32016R0679
2. ICO guidance: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-data-portability
3. FDA interoperability: https://www.fda.gov/medical-devices/digital-health-center-excellence/medical-device-interoperability
4. NHS FHIR: https://www.england.nhs.uk/long-read/interoperability
5. ONC Cures Act: https://www.healthit.gov/information-blocking/
6. CMS-0057-F: https://www.cms.gov/newsroom/fact-sheets/cms-interoperability-prior-authorization-final-rule-cms-0057-f
7. Intermountain Health outcomes: https://news.intermountainhealth.org/
8. Epic litigation: https://medcitynews.com/2026/03/health-gorilla-epic-data-interoperability/
