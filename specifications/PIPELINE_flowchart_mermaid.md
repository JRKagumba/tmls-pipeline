flowchart LR

    %% Intake
    A[Customer texts plumber] --> B[AI answers / intro]
    B --> C[Customer and AI interact by text]
    C --> T[Triage occurs here<br/>L1 = Immediate emergency<br/>L2 = 24-48 hours<br/>L3 = More than 48 hours]

    T --> D{AI call to action for Jill?}

    D -->|No - out of area or<br/>service not offered| E[AI explains / ends conversation]

    D -->|Yes| F[Determine next action]

    %% Possible actions
    F --> F1[Request more info]
    F --> F2[Call back customer]
    F --> F3[Provide quote]
    F --> F4[Book appointment]

    %% Jill service notification
    F --> G[AI notifies Jill via SMS<br/>triage level + customer info<br/>+ service intent]
    G --> H[Jill reviews in dashboard]

    %% Split by customer need
    H --> I{Customer wants quote or calendar?}

    %% Quote path
    I -->|Quote| Q1[AI generates quote]
    Q1 --> Q2[Quote sent to Jill dashboard for approval]
    Q2 --> Q3{Jill says?}

    Q3 -->|Approve| Q4[Email sent to customer]
    Q4 --> Q5{Customer approves?}
    Q5 -->|Yes| Q6[Proceed / quote accepted]
    Q5 -->|No| Q7[Jill follows up with customer]

    Q3 -->|Revise| Q8[Jill adds comment / AI regenerates quote]
    Q8 --> Q2

    Q3 -->|Reject| Q9[Jill does not want job / manual process]

    %% Calendar path - Calendly
    I -->|Calendar| C1[AI sends Calendly scheduling link to customer]
    C1 --> C2{Customer books via Calendly?}
    C2 -->|Yes - invitee.created webhook| C3[Job booked<br/>Dashboard notified<br/>booked_slot_text saved]
    C2 -->|No / canceled - invitee.canceled webhook| C4[Jill follows up / manual process]

    %% Optional connections from earlier action nodes
    F1 --> G
    F2 --> G
    F3 --> Q1
    F4 --> C1
