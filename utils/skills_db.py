"""
Curated skill/tool/keyword taxonomy.
This boosts extraction accuracy beyond plain TF-IDF by recognizing
known multi-word skills, tools, and certifications that JDs commonly use.

Add to these lists over time -- this is the highest-leverage file to
improve match quality for a specific niche (e.g. supply chain, tech, etc.)
"""

GENERIC_SKILLS = [
    "communication", "leadership", "teamwork", "problem solving",
    "project management", "stakeholder management", "time management",
    "critical thinking", "negotiation", "presentation skills",
    "cross-functional collaboration", "people management", "team management",
    "strategic planning", "decision making", "conflict resolution",
    "customer service", "attention to detail", "multitasking",
]

TECH_SKILLS = [
    "python", "sql", "excel", "power bi", "tableau", "java", "javascript",
    "r programming", "sap", "erp", "vba", "machine learning", "data analysis",
    "data visualization", "statistics", "power query", "power automate",
    "google sheets", "microsoft office", "aws", "azure", "git", "api",
    "etl", "data warehousing", "predictive modeling", "forecasting models",
]

SUPPLY_CHAIN_SKILLS = [
    "otif", "on time in full", "fefo", "fifo", "eoq", "abc analysis",
    "fsn analysis", "inventory management", "warehouse management",
    "wms", "sap mm", "sap wm", "3pl", "cfa", "co-packing", "dispatch planning",
    "demand forecasting", "supply chain planning", "logistics management",
    "vendor management", "procurement", "sourcing", "material planning",
    "distribution management", "fleet management", "route optimization",
    "network optimization", "supplier scorecard", "fill rate", "lead time",
    "safety stock", "cycle counting", "batch tracking", "cold chain",
    "reverse logistics", "last mile delivery", "gst", "e-way bill",
    "iso 9001", "six sigma", "lean manufacturing", "kaizen", "5s",
    "control tower", "tat", "turnaround time", "slotting optimization",
]

CERTIFICATIONS = [
    "pmp", "six sigma green belt", "six sigma black belt", "cscp", "cpim",
    "cltd", "iso certified", "lean certified", "prince2",
]

MASTER_SKILLS = list(set(
    GENERIC_SKILLS + TECH_SKILLS + SUPPLY_CHAIN_SKILLS + CERTIFICATIONS
))

# Maps each curated skill -> category, used to pick the right suggestion
# sentence template. Built automatically from the lists above.
SKILL_CATEGORY = {}
for _skill in GENERIC_SKILLS:
    SKILL_CATEGORY[_skill] = "soft_skill"
for _skill in TECH_SKILLS:
    SKILL_CATEGORY[_skill] = "tool"
for _skill in SUPPLY_CHAIN_SKILLS:
    SKILL_CATEGORY[_skill] = "domain"
for _skill in CERTIFICATIONS:
    SKILL_CATEGORY[_skill] = "certification"

# Common resume section headers used for formatting/ATS-readability checks
EXPECTED_SECTIONS = [
    "experience", "education", "skills", "summary", "objective",
    "certifications", "projects", "contact",
]

# Words to ignore when extracting keywords from free text
STOPWORDS_EXTRA = [
    "role", "responsibilities", "requirements", "candidate", "years",
    "experience", "team", "company", "job", "work", "ability", "strong",
    "excellent", "including", "etc", "preferred", "required", "must",
    "will", "using", "knowledge", "understanding", "skills", "plus",
    "looking", "good", "great", "who", "you", "we", "our", "the", "with",
]
