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
