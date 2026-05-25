flowchart LR

    %% Intake
    A[Customer texts plumber] --> B[AI answers / intro]
    B --> C[Customer and AI interact by text]
    C --> T[Triage occurs here<br/>Level 1 = Immediate<br/>Level 2 = Within 24h<br/>Level 3 = Within 24-48h]

    T --> D{AI call to action for Jill?}

    D -->|No| E[End call / end interaction]

    D -->|Yes| F[Determine next action]

    %% Possible actions
    F --> F1[Request more info]
    F --> F2[Call back customer]
    F --> F3[Provide quote]
    F --> F4[Book appointment]

    %% Jill service notification
    F --> G[AI SMSes Jill<br/>with triage level, customer info,<br/>and service intent]
    G --> H[Jill follows up with customer]

    %% Split by customer need
    H --> I{Customer wants quote or calendar?}

    %% Quote path
    I -->|Quote| Q1[AI generates quote]
    Q1 --> Q2[AI sends quote to Jill for approval]
    Q2 --> Q3{Jill says?}

    Q3 -->|Yes| Q4[Email sent to customer]
    Q4 --> Q5{Customer approves?}
    Q5 -->|Yes| Q6[Proceed / quote accepted]
    Q5 -->|No| Q7[Jill follows up with customer]

    Q3 -->|Revise| Q8[Jill revises quote]
    Q8 --> Q4

    Q3 -->|No| Q9[Jill does not want job / manual process]

    %% Calendar path
    I -->|Calendar| C1[AI looks at Jill's calendar]
    C1 --> C2[AI finds open slots<br/>for next available date/time]
    C2 --> C3{Jill says?}

    C3 -->|Yes| C4[AI sends SMS to customer]
    C4 --> C5{Customer approves?}
    C5 -->|Yes| C6[Job booked]
    C5 -->|No| C7[Jill follows up with customer]

    C3 -->|Revise| C8[Jill revises appointment options]
    C8 --> C4

    C3 -->|No| C9[Manual process / Jill follows up]

    %% Optional connections from earlier action nodes
    F1 --> G
    F2 --> G
    F3 --> Q1
    F4 --> C1