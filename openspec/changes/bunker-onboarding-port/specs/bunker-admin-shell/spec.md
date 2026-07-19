## MODIFIED Requirements

### Requirement: Placeholder sections
Selecting a sidebar section with no real implementation yet (currently "Agentic OS", "Configuración") SHALL render a "coming soon" placeholder state instead of an error or blank area. ("Social Content Ops" and "Onboarding" were placeholders at the time this requirement was first written; both were subsequently implemented — see `bunker-social-content-ops-port` and `bunker-onboarding-port`.)

#### Scenario: User selects an unbuilt section
- **WHEN** the user clicks a sidebar item with no implementation yet
- **THEN** the main content area shows a placeholder indicating the section is not yet available, with no console errors and no blank/broken layout
