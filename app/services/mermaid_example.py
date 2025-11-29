"""Working Mermaid diagram examples for RAG context injection.

These examples help the LLM understand correct Mermaid syntax patterns.
"""

# Working example of a complex architecture diagram with all correct syntax patterns
WORKING_EXAMPLE = """flowchart TD
    subgraph Client
        User["User Device (Web/Mobile)"]
        User -->|Upload Photo| LoadBalancer
    end

    subgraph Infrastructure
        LoadBalancer[Load Balancer] -->|HTTPS| APIGateway
        APIGateway -->|Route based on path| AuthService
        APIGateway -->|Route based on path| CalorieService
        APIGateway -->|Route based on path| InsulinService
        CDN[CDN] -.->|Static Assets| User
        Monitoring["Monitoring & Logging"]
    end

    subgraph Auth_Service["Auth Service"]
        AuthService[Authentication Service]
        AuthService -->|Verify Credentials| UserDB["User Database"]
    end

    subgraph Calorie_Service["Calorie Service"]
        CalorieService[Calorie Calculation Service]
        CalorieService -->|Image Analysis Request| ImageProcessorQueue
        CalorieService -->|Cache Lookup| CalorieCache["Redis Cache"]
        CalorieService -->|Query| CalorieDB["Calorie Database"]
    end

    subgraph Insulin_Service["Insulin Service"]
        InsulinService[Insulin Dosage Service]
        InsulinService -->|Calorie Data| CalorieService
        InsulinService -->|User Profile Data| UserProfileDB["User Profile DB"]
        InsulinService -->|Dosage Calculation| DosageCalculator
        DosageCalculator -->|External API| GoogleAPI["Google API"]
    end

    subgraph Async_Processing["Async Image Processing"]
        ImageProcessorQueue["Message Queue"] --> ImageProcessor
        ImageProcessor["Image Processor AI/ML"] -->|Parsed Structure| CalorieService
        ImageProcessor -->|Store| ObjectStorage["Object Storage S3"]
    end

    subgraph Data_Layer["Data Layer"]
        CalorieDB
        UserDB
        UserProfileDB
    end

    CalorieService -->|Metrics| Monitoring
    InsulinService -->|Metrics| Monitoring
    AuthService -->|Metrics| Monitoring"""

# Key syntax rules demonstrated in the example
SYNTAX_RULES_SUMMARY = """
CRITICAL MERMAID SYNTAX RULES (from working example above):

1. SUBGRAPH IDs WITH SPACES - Use underscore ID with quoted label:
   CORRECT: subgraph Auth_Service["Auth Service"]
   WRONG: subgraph Auth Service

2. LABELS WITH PARENTHESES - Always use double quotes:
   CORRECT: User["User Device (Web/Mobile)"]
   WRONG: User[User Device (Web/Mobile)]

3. FLOWCHART EDGE LABELS - Use pipe syntax:
   CORRECT: A -->|label text| B
   WRONG: A --> B: label text

4. NO NESTED SUBGRAPHS - Keep subgraphs flat, don't nest them

5. MATCHING END STATEMENTS - Each subgraph needs exactly one 'end'

6. NODE IDs - No spaces, use underscores:
   CORRECT: API_Gateway, Load_Balancer
   WRONG: API Gateway, Load Balancer
"""

def get_example_context() -> str:
    """Get the full example context for injection into prompts."""
    return f"""
=== WORKING MERMAID EXAMPLE (USE AS REFERENCE) ===

{WORKING_EXAMPLE}

{SYNTAX_RULES_SUMMARY}
=== END OF EXAMPLE ===
"""

