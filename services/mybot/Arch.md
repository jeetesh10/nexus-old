graph TD
    subgraph User Interaction
        A[User opens app] --> B(Signs in Anonymously/with Token)
        B --> C{Firestore Ready?}
        C -- Yes --> D[Setup Firestore Listener]
        D --> E((Start listening for messages))
    end

    subgraph User Message Flow
        F[User types message]
        F --or--> G(User speaks into microphone)
        G --> F

        F --> H[User Clicks Send/Presses Enter]
        H --> I[sendMessage() called]
        I --> J[Save User Message to Firestore]
        J -- Real-time Sync --> K[Listener detects new message]
        K --> L[displayMessage(user_message)]
        L --> M[Update UI with User Message]
    end

    subgraph AI Response Flow
        J -- Awaits Completion --> N[Call getAIResponse()]
        N --> O[Send to Gemini API]
        O --> P[Receive AI text response]
        P --> Q[Save AI Message to Firestore]
        Q -- Real-time Sync --> R[Listener detects new message]
        R --> S[displayMessage(ai_response)]
        S --> T[Update UI with AI Message]
    end

    style A fill:#4CAF50,stroke:#388E3C,stroke-width:2px,color:#fff
    style G fill:#E91E63,stroke:#C2185B,stroke-width:2px,color:#fff
    style H fill:#2196F3,stroke:#1976D2,stroke-width:2px,color:#fff
    style O fill:#FF9800,stroke:#F57C00,stroke-width:2px,color:#fff
    style J fill:#FFEB3B,stroke:#FBC02D,stroke-width:2px,color:#000
    style K fill:#BDBDBD,stroke:#9E9E9E,stroke-width:2px,color:#000
    style L fill:#4CAF50,stroke:#388E3C,stroke-width:2px,color:#fff
    style Q fill:#FFEB3B,stroke:#FBC02D,stroke-width:2px,color:#000
    style R fill:#BDBDBD,stroke:#9E9E9E,stroke-width:2px,color:#000
    style S fill:#4CAF50,stroke:#388E3C,stroke-width:2px,color:#fff
