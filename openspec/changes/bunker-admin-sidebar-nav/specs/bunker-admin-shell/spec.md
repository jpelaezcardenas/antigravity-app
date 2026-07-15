## ADDED Requirements

### Requirement: Sidebar navigation shell
The Búnker (`/app/bunker`) SHALL render a persistent left sidebar containing: a "C" logo mark, an "Admin CONTEXIA" header label, a vertical list of 6 navigation items (Dashboard, CRM/Ventas, Onboarding, Social Content Ops, Agentic OS, Configuración), and a "POWERED BY CONTEXIA" footer caption.

#### Scenario: Sidebar renders on page load
- **WHEN** a user opens `/app/bunker`
- **THEN** the sidebar is visible with all 6 nav items listed and the "Dashboard" item shown as active by default

### Requirement: Section switching without navigation
Clicking a sidebar nav item SHALL update the main content area to show that section's content without a full page reload or URL route change.

#### Scenario: User switches from Dashboard to CRM/Ventas
- **WHEN** the user clicks "CRM/Ventas" in the sidebar
- **THEN** the main content area replaces the Dashboard content with the CRM/Ventas content, and the "CRM/Ventas" nav item is visually marked active (highlighted pill), while "Dashboard" loses the active state

### Requirement: CRM/Ventas preserves existing client list
The "CRM/Ventas" section SHALL render the same client roster and stats content that previously constituted the entire `/app/bunker` page body (client cards with name/email/status/users/plan, and the "Estadísticas del Bunker" summary block), unchanged in data and substance.

#### Scenario: CRM/Ventas shows all existing clients
- **WHEN** the user selects "CRM/Ventas"
- **THEN** all client entries previously shown on `/app/bunker` (Contexia Marketing, Lavaderos L&D, Sion, Repuestos Don Álvaro, Studio 4) are visible with their existing fields, plus the stats block (client count, total users, Pro plan count, uptime)

### Requirement: Placeholder sections
Selecting "Onboarding", "Social Content Ops", "Agentic OS", or "Configuración" SHALL render a "coming soon" placeholder state instead of an error or blank area.

#### Scenario: User selects an unbuilt section
- **WHEN** the user clicks "Onboarding" (or Social Content Ops, Agentic OS, Configuración)
- **THEN** the main content area shows a placeholder indicating the section is not yet available, with no console errors and no blank/broken layout
