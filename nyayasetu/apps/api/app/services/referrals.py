"""
Links to official services rather than attempting to automate protected
submissions (Section 11). Domain -> list of (need, action, source_id).
"""

REFERRAL_MAP: dict[str, list[dict]] = {
    "rental_tenancy": [
        {
            "need": "Free legal aid",
            "action": "Contact NALSA / your State Legal Services Authority, or call the 15100 helpline.",
            "source_id": "source-nalsa-002",
        },
        {
            "need": "Pre-litigation settlement",
            "action": "A Lok Adalat can settle a rent or eviction dispute by compromise, without court fees.",
            "source_id": "source-nalsa-001",
        },
        {
            "need": "Case status and hearing information",
            "action": "Look up your case by CNR number on eCourts Services.",
            "source_id": "source-ecourts-001",
        },
    ],
    "employment": [
        {
            "need": "Free legal aid",
            "action": "Contact NALSA / your State Legal Services Authority, or call the 15100 helpline.",
            "source_id": "source-nalsa-002",
        },
        {
            "need": "Wage or termination dispute",
            "action": "Raise it with your state Labour Commissioner; NALSA can advise on eligibility for free legal aid.",
            "source_id": "source-employment-general-001",
        },
    ],
    "consumer_disputes": [
        {
            "need": "Consumer complaint filing",
            "action": "File online via the e-Daakhil portal.",
            "source_id": "source-edaakhil-001",
        },
        {
            "need": "Free mediation before escalation",
            "action": "Call the National Consumer Helpline (1915) or use INGRAM.",
            "source_id": "source-nch-001",
        },
    ],
    "cyber_fraud": [
        {
            "need": "Report cyber fraud",
            "action": "Report immediately on the National Cyber Crime Reporting Portal.",
            "source_id": "source-ncrp-001",
        },
        {
            "need": "Financial fraud — urgent",
            "action": "Call the 1930 helpline right away to improve the chance of freezing transferred funds.",
            "source_id": "source-ncrp-002",
        },
    ],
    "general_notice": [
        {
            "need": "Free legal aid",
            "action": "Contact NALSA / your State Legal Services Authority, or call the 15100 helpline.",
            "source_id": "source-nalsa-002",
        },
        {
            "need": "Case status and hearing information",
            "action": "Look up your case by CNR number on eCourts Services.",
            "source_id": "source-ecourts-001",
        },
    ],
}


def get_referrals_for_domain(domain: str) -> list[dict]:
    return REFERRAL_MAP.get(domain, REFERRAL_MAP["general_notice"])
