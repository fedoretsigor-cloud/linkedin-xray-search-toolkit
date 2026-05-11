from src.text_utils import clean_text


FAMILY_DEFAULT_GROUPS = {
    "Java Backend": [
        ["Java", "JVM"],
        ["Spring Boot", "Spring"],
        ["Kafka", "RabbitMQ", "message broker"],
        ["AWS", "cloud"],
        ["microservices", "distributed systems"],
        ["PostgreSQL", "MySQL", "Oracle"],
        ["REST", "API", "GraphQL"],
        ["Docker", "Kubernetes"],
        ["Hibernate", "JPA"],
        ["CI/CD", "Jenkins", "GitLab"],
        ["Redis", "Elasticsearch"],
        ["SQL", "NoSQL"],
    ],
    "QA Automation": [
        ["Python", "pytest"],
        ["Selenium", "Playwright", "Cypress"],
        ["automation framework", "test automation"],
        ["automotive", "embedded", "ADAS"],
        ["HiL", "SIL"],
        ["log analysis", "logs", "virtual environments"],
        ["Git", "CI/CD"],
        ["BDD", "Gherkin", "keyword-driven testing"],
        ["Robot Framework"],
        ["Puppeteer"],
        ["Jenkins", "GitLab"],
        ["API testing", "REST"],
    ],
    "Business Analysis": [
        ["requirements analysis", "business requirements"],
        ["BPMN", "UML", "process mapping"],
        ["Jira", "Confluence"],
        ["UAT", "user acceptance testing"],
        ["SQL", "data analysis"],
        ["stakeholder management", "workshops"],
        ["Agile", "Scrum"],
        ["API", "integration"],
        ["user stories", "acceptance criteria"],
        ["ERP", "CRM"],
        ["financial services", "banking"],
        ["documentation", "functional specifications"],
    ],
    "Frontend": [
        ["JavaScript", "TypeScript"],
        ["React", "Next.js"],
        ["Angular", "Vue"],
        ["HTML", "CSS"],
        ["Redux", "state management"],
        ["frontend architecture"],
        ["GraphQL", "REST"],
        ["Jest", "Cypress", "Playwright"],
    ],
    "Fullstack": [
        ["JavaScript", "TypeScript"],
        ["React", "Angular", "Vue"],
        ["Node.js", "Express"],
        ["Java", "Spring"],
        ["Python", "Django", "FastAPI"],
        ["PostgreSQL", "MySQL", "MongoDB"],
        ["AWS", "cloud"],
        ["Docker", "Kubernetes"],
    ],
    "iOS": [
        ["Swift", "SwiftUI"],
        ["iOS", "UIKit"],
        ["Objective-C"],
        ["Xcode"],
        ["Combine", "async await"],
        ["Core Data"],
        ["App Store"],
        ["mobile architecture"],
    ],
    "Android": [
        ["Kotlin", "Java"],
        ["Android", "Jetpack"],
        ["Compose", "Jetpack Compose"],
        ["Gradle"],
        ["Coroutines", "Flow"],
        ["Android SDK"],
        ["Google Play"],
        ["mobile architecture"],
    ],
    "DevOps / SRE": [
        ["Kubernetes", "Docker"],
        ["AWS", "Azure", "GCP"],
        ["Terraform", "IaC"],
        ["CI/CD", "Jenkins", "GitLab"],
        ["Prometheus", "Grafana"],
        ["Linux", "Bash"],
        ["SRE", "observability"],
        ["Helm", "ArgoCD"],
    ],
    "Data Engineer": [
        ["Python", "SQL"],
        ["Spark", "Databricks"],
        ["Airflow", "ETL"],
        ["Kafka", "streaming"],
        ["Snowflake", "BigQuery", "Redshift"],
        ["dbt"],
        ["AWS", "GCP", "Azure"],
        ["data pipelines"],
    ],
    "Data / BI Analytics": [
        ["SQL", "Excel"],
        ["Power BI", "DAX"],
        ["Tableau", "Looker"],
        ["dashboard", "reporting"],
        ["KPI", "metrics"],
        ["Python", "R"],
        ["Snowflake", "BigQuery"],
        ["data visualization", "analytics"],
        ["A/B testing", "experimentation"],
        ["product analytics", "Amplitude"],
        ["Mixpanel", "Google Analytics"],
        ["data modeling", "ETL"],
    ],
    "ML / AI Engineer": [
        ["Python", "machine learning"],
        ["PyTorch", "TensorFlow"],
        ["LLM", "NLP"],
        ["MLOps", "model deployment"],
        ["scikit-learn"],
        ["computer vision"],
        ["AWS", "GCP", "Azure"],
        ["vector search", "embeddings"],
    ],
    "Product Management": [
        ["roadmap", "product strategy"],
        ["discovery", "user research"],
        ["backlog", "user stories"],
        ["B2B", "SaaS"],
        ["analytics", "metrics"],
        ["A/B testing", "experimentation"],
        ["stakeholder management", "go-to-market"],
        ["Jira", "Confluence"],
        ["Agile", "Scrum"],
        ["market research", "competitive analysis"],
        ["product-led growth", "PLG"],
        ["API", "platform"],
    ],
    "Project / Delivery Management": [
        ["project management", "delivery management"],
        ["Agile", "Scrum"],
        ["Jira", "Confluence"],
        ["risk management", "planning"],
        ["stakeholder management", "communication"],
        ["budget", "resource planning"],
        ["program management", "portfolio"],
        ["Kanban", "retrospectives"],
        ["roadmap", "milestones"],
        ["vendor management", "outsourcing"],
        ["PMP", "Prince2"],
        ["software delivery", "SDLC"],
    ],
    "Architecture / Leadership": [
        ["architecture", "solution design"],
        ["cloud", "AWS", "Azure"],
        ["microservices", "distributed systems"],
        ["API", "integration"],
        ["Kubernetes", "Docker"],
        ["security", "scalability"],
        ["enterprise architecture", "TOGAF"],
        ["technical leadership", "mentoring"],
        ["people management", "hiring"],
        ["roadmap", "delivery"],
        ["Java", ".NET"],
        ["event-driven", "Kafka"],
    ],
    "UX / Product Design": [
        ["Figma", "Sketch"],
        ["design systems", "UI"],
        ["UX research", "user interviews"],
        ["prototyping", "wireframes"],
        ["usability testing", "accessibility"],
        ["interaction design", "user flows"],
        ["journey mapping", "personas"],
        ["mobile design", "web design"],
        ["product design", "SaaS"],
        ["information architecture", "IA"],
        ["A/B testing", "experimentation"],
        ["design thinking", "workshops"],
    ],
    "Embedded": [
        ["C", "C++"],
        ["embedded", "firmware"],
        ["RTOS", "FreeRTOS"],
        ["microcontroller", "MCU"],
        ["CAN", "LIN", "Ethernet"],
        ["automotive", "ADAS"],
        ["Linux", "Yocto"],
        ["hardware", "debugging"],
    ],
}


def desired_group_count(target_count):
    try:
        target_count = int(target_count)
    except (TypeError, ValueError):
        target_count = 20

    if target_count <= 20:
        return 3
    if target_count <= 40:
        return 4
    if target_count <= 60:
        return 5
    if target_count <= 100:
        return 8
    return 12


def expand_skill_groups(skill_groups, role_pattern=None, target_count=20):
    desired_count = desired_group_count(target_count)
    expanded = []

    for group in skill_groups or [[]]:
        add_group(expanded, group)

    family = (role_pattern or {}).get("family") or ""
    for group in FAMILY_DEFAULT_GROUPS.get(family, []):
        if len(expanded) >= desired_count:
            break
        add_group(expanded, group)

    return expanded[:desired_count] or [[]]


def add_group(groups, group):
    cleaned = [clean_text(value) for value in group or [] if clean_text(value)]
    if not cleaned:
        if not groups:
            groups.append([])
        return
    key = group_key(cleaned)
    if key in {group_key(existing) for existing in groups}:
        return
    if is_subset_of_existing_group(cleaned, groups):
        return
    groups.append(cleaned)


def group_key(group):
    return "|".join(sorted(clean_text(value).lower() for value in group if clean_text(value)))


def is_subset_of_existing_group(group, groups):
    new_terms = {clean_text(value).lower() for value in group if clean_text(value)}
    if not new_terms:
        return False
    for existing in groups:
        existing_terms = {clean_text(value).lower() for value in existing if clean_text(value)}
        if new_terms and new_terms.issubset(existing_terms):
            return True
    return False
