window.ROLE_PRESETS = [
  {
    group: "Backend Engineering",
    presets: [
      {
        name: "Java Backend Developer",
        role: "Java Backend Developer",
        variants: ["Java Developer", "Backend Engineer", "Java Software Engineer", "Spring Boot Developer"],
        stacks: ["Java | Spring Boot | Kafka | AWS", "Java | Spring | Oracle"],
      },
      {
        name: "Python Backend Developer",
        role: "Python Backend Developer",
        variants: ["Python Developer", "Backend Engineer", "Django Developer", "FastAPI Developer"],
        stacks: ["Python | Django | PostgreSQL | AWS", "Python | FastAPI | Docker"],
      },
      {
        name: "Node.js Backend Developer",
        role: "Node.js Backend Developer",
        variants: ["Node.js Developer", "Backend Engineer", "JavaScript Backend Developer", "TypeScript Developer"],
        stacks: ["Node.js | TypeScript | PostgreSQL | AWS", "Node.js | Express | MongoDB"],
      },
      {
        name: ".NET Backend Developer",
        role: ".NET Backend Developer",
        variants: [".NET Developer", "C# Developer", "Backend Engineer", "ASP.NET Developer"],
        stacks: ["C# | .NET | ASP.NET | Azure", ".NET | SQL Server | Microservices"],
      },
      {
        name: "Go Backend Developer",
        role: "Go Backend Developer",
        variants: ["Golang Developer", "Go Engineer", "Backend Engineer", "Platform Backend Engineer"],
        stacks: ["Go | Kubernetes | PostgreSQL | AWS", "Golang | Docker | Microservices"],
      },
    ],
  },
  {
    group: "Frontend Engineering",
    presets: [
      {
        name: "React Frontend Developer",
        role: "React Frontend Developer",
        variants: ["Frontend Developer", "React Developer", "JavaScript Developer", "UI Engineer"],
        stacks: ["React | TypeScript | Redux", "JavaScript | HTML | CSS"],
      },
      {
        name: "Angular Frontend Developer",
        role: "Angular Frontend Developer",
        variants: ["Frontend Developer", "Angular Developer", "TypeScript Developer", "UI Engineer"],
        stacks: ["Angular | TypeScript | RxJS", "JavaScript | HTML | CSS"],
      },
      {
        name: "Vue Frontend Developer",
        role: "Vue Frontend Developer",
        variants: ["Frontend Developer", "Vue.js Developer", "JavaScript Developer", "UI Engineer"],
        stacks: ["Vue.js | TypeScript | Pinia", "JavaScript | HTML | CSS"],
      },
    ],
  },
  {
    group: "Full Stack Engineering",
    presets: [
      {
        name: "Java Full Stack Developer",
        role: "Java Full Stack Developer",
        variants: ["Full Stack Developer", "Java Developer", "React Developer", "Software Engineer"],
        stacks: ["Java | Spring Boot | React | TypeScript", "Java | Angular | PostgreSQL"],
      },
      {
        name: "MERN Full Stack Developer",
        role: "MERN Full Stack Developer",
        variants: ["Full Stack Developer", "Node.js Developer", "React Developer", "JavaScript Developer"],
        stacks: ["MongoDB | Express | React | Node.js", "JavaScript | TypeScript | AWS"],
      },
    ],
  },
  {
    group: "Mobile",
    presets: [
      {
        name: "iOS Developer",
        role: "iOS Developer",
        variants: ["Swift Developer", "Mobile Engineer", "iOS Engineer"],
        stacks: ["Swift | SwiftUI | iOS", "Objective-C | UIKit | iOS"],
      },
      {
        name: "Android Developer",
        role: "Android Developer",
        variants: ["Kotlin Developer", "Mobile Engineer", "Android Engineer"],
        stacks: ["Kotlin | Android | Jetpack Compose", "Java | Android SDK"],
      },
      {
        name: "React Native Developer",
        role: "React Native Developer",
        variants: ["Mobile Developer", "React Native Engineer", "JavaScript Mobile Developer"],
        stacks: ["React Native | TypeScript | iOS | Android"],
      },
    ],
  },
  {
    group: "DevOps / SRE / Platform",
    presets: [
      {
        name: "DevOps Engineer",
        role: "DevOps Engineer",
        variants: ["Cloud Engineer", "Infrastructure Engineer", "Platform Engineer", "CI/CD Engineer"],
        stacks: ["AWS | Kubernetes | Terraform | Docker", "Azure | CI/CD | Helm"],
      },
      {
        name: "Site Reliability Engineer",
        role: "Site Reliability Engineer",
        variants: ["SRE", "Reliability Engineer", "Platform Engineer", "Infrastructure Engineer"],
        stacks: ["Kubernetes | Prometheus | Terraform | Linux", "AWS | Observability | Incident Response"],
      },
      {
        name: "Platform Engineer",
        role: "Platform Engineer",
        variants: ["DevOps Engineer", "Infrastructure Engineer", "Kubernetes Engineer", "Cloud Engineer"],
        stacks: ["Kubernetes | Terraform | AWS | Go", "Docker | Helm | CI/CD"],
      },
    ],
  },
  {
    group: "Business Analysis",
    presets: [
      {
        name: "Business Analyst",
        role: "Business Analyst",
        variants: ["Systems Analyst", "Requirements Analyst", "Functional Analyst", "Product Analyst"],
        stacks: ["Requirements Analysis | BPMN | UML | Jira", "UAT | SQL | Agile | Stakeholder Management"],
      },
      {
        name: "Systems Analyst",
        role: "Systems Analyst",
        variants: ["Business Systems Analyst", "Functional Analyst", "Technical Business Analyst"],
        stacks: ["Systems Analysis | SQL | API | UML", "Requirements | Integration | Jira"],
      },
      {
        name: "Product Owner",
        role: "Product Owner",
        variants: ["Business Analyst", "Product Manager", "Agile Product Owner"],
        stacks: ["Backlog | User Stories | Agile | Scrum", "Roadmap | Stakeholders | Jira"],
      },
      {
        name: "Functional Consultant",
        role: "Functional Consultant",
        variants: ["Functional Analyst", "Business Analyst", "Implementation Consultant"],
        stacks: ["Requirements | Configuration | UAT | ERP", "Process Mapping | Stakeholder Management"],
      },
    ],
  },
  {
    group: "Data Engineering",
    presets: [
      {
        name: "Data Engineer",
        role: "Data Engineer",
        variants: ["Big Data Engineer", "ETL Developer", "Analytics Engineer", "Data Platform Engineer"],
        stacks: ["Python | SQL | Spark | Airflow", "Databricks | Kafka | AWS"],
      },
      {
        name: "Analytics Engineer",
        role: "Analytics Engineer",
        variants: ["Data Analyst Engineer", "dbt Developer", "BI Engineer"],
        stacks: ["SQL | dbt | Snowflake | BigQuery", "Python | Tableau | Looker"],
      },
    ],
  },
  {
    group: "Data / BI Analytics",
    presets: [
      {
        name: "Data Analyst",
        role: "Data Analyst",
        variants: ["BI Analyst", "Reporting Analyst", "Analytics Analyst", "Product Analyst"],
        stacks: ["SQL | Excel | Tableau | Power BI", "Python | Looker | BigQuery | Snowflake"],
      },
      {
        name: "BI Analyst",
        role: "BI Analyst",
        variants: ["Business Intelligence Analyst", "Reporting Analyst", "Data Analyst"],
        stacks: ["Power BI | Tableau | SQL | DAX", "Looker | KPI Reporting | Data Modeling"],
      },
      {
        name: "Product Analyst",
        role: "Product Analyst",
        variants: ["Data Analyst", "Growth Analyst", "Analytics Analyst"],
        stacks: ["SQL | Product Metrics | A/B Testing | Amplitude", "Mixpanel | Python | Tableau"],
      },
    ],
  },
  {
    group: "ML / AI Engineering",
    presets: [
      {
        name: "Machine Learning Engineer",
        role: "Machine Learning Engineer",
        variants: ["ML Engineer", "AI Engineer", "Machine Learning Developer", "Applied Scientist"],
        stacks: ["Python | PyTorch | TensorFlow | MLOps", "Scikit-learn | AWS | Docker"],
      },
      {
        name: "LLM Engineer",
        role: "LLM Engineer",
        variants: ["AI Engineer", "Generative AI Engineer", "NLP Engineer", "Prompt Engineer"],
        stacks: ["Python | LLM | RAG | LangChain", "OpenAI | Vector Database | MLOps"],
      },
    ],
  },
  {
    group: "Product / Project Management",
    presets: [
      {
        name: "Product Manager",
        role: "Product Manager",
        variants: ["Product Owner", "Technical Product Manager", "Product Lead"],
        stacks: ["Roadmap | Product Strategy | Discovery | Analytics", "Backlog | User Stories | B2B SaaS"],
      },
      {
        name: "Project Manager",
        role: "Project Manager",
        variants: ["IT Project Manager", "Technical Project Manager", "Program Manager"],
        stacks: ["Agile | Scrum | Jira | Delivery", "Planning | Risk Management | Stakeholders"],
      },
      {
        name: "Delivery Manager",
        role: "Delivery Manager",
        variants: ["Project Manager", "Program Manager", "Engagement Manager"],
        stacks: ["Delivery Management | Agile | Stakeholders | Roadmap", "Budget | Risk | Resource Planning"],
      },
      {
        name: "Scrum Master",
        role: "Scrum Master",
        variants: ["Agile Coach", "Agile Project Manager", "Delivery Manager"],
        stacks: ["Scrum | Agile | Jira | Facilitation", "Kanban | Team Coaching | Retrospectives"],
      },
    ],
  },
  {
    group: "Architecture / Leadership",
    presets: [
      {
        name: "Solution Architect",
        role: "Solution Architect",
        variants: ["Software Architect", "Technical Architect", "Enterprise Architect"],
        stacks: ["Cloud | Microservices | Integration | API", "AWS | Azure | Architecture | Security"],
      },
      {
        name: "Software Architect",
        role: "Software Architect",
        variants: ["Solution Architect", "Technical Architect", "Lead Software Engineer"],
        stacks: ["Architecture | Microservices | Java | Cloud", "Distributed Systems | API | Kubernetes"],
      },
      {
        name: "Engineering Manager",
        role: "Engineering Manager",
        variants: ["Software Engineering Manager", "Development Manager", "Technical Manager"],
        stacks: ["People Management | Delivery | Agile | Hiring", "Engineering Leadership | Roadmap | Stakeholders"],
      },
      {
        name: "Tech Lead",
        role: "Tech Lead",
        variants: ["Technical Lead", "Lead Developer", "Lead Software Engineer"],
        stacks: ["Architecture | Code Review | Mentoring | Delivery", "Java | Cloud | Microservices"],
      },
    ],
  },
  {
    group: "UX / Product Design",
    presets: [
      {
        name: "Product Designer",
        role: "Product Designer",
        variants: ["UX Designer", "UI/UX Designer", "Interaction Designer"],
        stacks: ["Figma | Design Systems | Prototyping", "User Research | UX | UI"],
      },
      {
        name: "UX/UI Designer",
        role: "UX/UI Designer",
        variants: ["UX Designer", "UI Designer", "Product Designer"],
        stacks: ["Figma | Wireframes | Prototyping", "Design Systems | Accessibility | User Flows"],
      },
      {
        name: "UX Researcher",
        role: "UX Researcher",
        variants: ["User Researcher", "UX Analyst", "Product Researcher"],
        stacks: ["User Interviews | Usability Testing | Research", "Surveys | Journey Mapping | Personas"],
      },
    ],
  },
  {
    group: "QA / Test Automation",
    presets: [
      {
        name: "QA Automation Engineer",
        role: "QA Automation Engineer",
        variants: ["SDET", "Test Automation Engineer", "Automation QA Engineer", "Software Test Engineer"],
        stacks: ["Java | Selenium | TestNG | API Testing", "Python | Playwright | Pytest"],
      },
      {
        name: "Manual QA Engineer",
        role: "Manual QA Engineer",
        variants: ["QA Engineer", "Software Tester", "Test Engineer"],
        stacks: ["Manual Testing | API Testing | SQL", "Jira | TestRail | Regression Testing"],
      },
    ],
  },
  {
    group: "Security",
    presets: [
      {
        name: "Application Security Engineer",
        role: "Application Security Engineer",
        variants: ["AppSec Engineer", "Security Engineer", "Product Security Engineer"],
        stacks: ["OWASP | SAST | DAST | Python", "Cloud Security | Kubernetes | Threat Modeling"],
      },
      {
        name: "Security Engineer",
        role: "Security Engineer",
        variants: ["Cybersecurity Engineer", "Cloud Security Engineer", "Infrastructure Security Engineer"],
        stacks: ["SIEM | AWS Security | IAM | Linux", "Azure Security | Incident Response"],
      },
    ],
  },
  {
    group: "ERP / Enterprise",
    presets: [
      {
        name: "SAP Developer",
        role: "SAP Developer",
        variants: ["ABAP Developer", "SAP Consultant", "SAP Technical Consultant"],
        stacks: ["SAP ABAP | SAP HANA | Fiori", "SAP BTP | OData | CDS"],
      },
      {
        name: "Salesforce Developer",
        role: "Salesforce Developer",
        variants: ["Apex Developer", "Salesforce Engineer", "Salesforce Consultant"],
        stacks: ["Salesforce | Apex | Lightning | SOQL", "Salesforce Flow | LWC | REST API"],
      },
    ],
  },
];
