---
alwaysApply: true
---
# MVP Enforcement Rules

The sets of rules MUST STRICTLY be applied to enforce MVP development to all conversations and tasks:-

-   **Code Length Limits**: Keep individual functions under 20 lines and files under 300 lines - if exceeded, look for library alternatives or simpler approaches

-   **No Custom Framework Building**: Never create your own utility libraries, helper classes, or mini-frameworks - use existing solutions even if they're not perfect fits

-   **Single-File Solutions**: When possible, implement features in single files rather than creating elaborate folder structures or module hierarchies

-   **Hardcode Configuration**: Use environment variables or simple config objects instead of building configuration management systems or admin panels

-   **No Abstraction Layers**: Avoid creating interfaces, abstract classes, or wrapper functions unless absolutely necessary - write direct implementations

-   **Copy-Paste Over Generalization**: If you need similar functionality twice, copy and modify existing code rather than creating reusable components

-   **Essential Error Handling Only**: Implement basic try-catch blocks for critical paths but skip comprehensive error handling and logging systems

-   **Minimal Data Validation**: Use simple field checks and basic validation - avoid complex validation schemas or custom validation frameworks

-   **No Custom Authentication**: Use third-party auth services (Auth0, Firebase Auth, etc.) rather than building login systems, password reset flows, or user management

-   **Skip Advanced Features**: No caching layers, queuing systems, background jobs, or microservices architecture until post-MVP

-   **Database Simplicity**: Use simple database queries and avoid migrations

-   **No Testing Infrastructure**: Avoid setting up complex testing frameworks, mocking libraries, or CI/CD pipelines.

-   **Keep Strava API Docs in focus**: Keep Strava docs and best practices in focus

-   **MVP-First Mindset**: Only plan for core features that directly validate the system hypothesis - defer all nice-to-have features

-   **Library-First Development**: Always research and recommend existing libraries, frameworks before writing custom code - aim for 80% third-party dependencies

-   **Tests Implementation**: We dont have a problem with real external data being called. Infact, thats what we intend to do via our testing ship our app quickly. We want to write absolutely minimal tests - testing only the e2e flows and core business logic unit tests. We will not write any other tests.

-   **No Premature Optimization**: Avoid performance optimizations, complex caching, complex logging , or scalability patterns until they become actual bottlenecks

-   **Quick Validation Over Polish**: Prioritize functional prototypes over polished UI/UX - basic styling and user experience is sufficient for MVP validation