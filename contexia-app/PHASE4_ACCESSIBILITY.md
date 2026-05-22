# Phase 4: Accessibility Audit

## Current State
- **Headings**: h2 (page level) → h3 (sections: 15) → h4 (subsections: 5)
- **ARIA Attributes**: 6 uses found (minimal coverage)
- **Focus States**: Present but not audited
- **Color Contrast**: Not audited yet

## Priority Items

### 1️⃣ Interactive Element Labels (HIGH PRIORITY)
- **Buttons without visible labels**: Add aria-label
  - Material Symbols only (icon buttons): Need labels
  - Input fields: Add labels or aria-describedby
  - Dropdowns/Selects: Add aria-label or associated label

- **Affected Components**:
  - WithdrawalSimulatorCard (input field)
  - TopBar (likely has menu buttons)
  - BottomNav (icon-only navigation)
  - Any interactive icons without text

### 2️⃣ Form Field Accessibility
- Input elements need associated `<label>` tags or aria-label
- Example: withdrawal-input field in WithdrawalSimulatorCard already has label

### 3️⃣ Heading Hierarchy Verification
- Verify h2 → h3 → h4 flow per page
- Ensure no h4 before h3
- Document valid hierarchy in each page layout

### 4️⃣ Color Contrast (WCAG AA 4.5:1)
- Check status badge colors against backgrounds
- Verify primary text colors on surface colors
- Check icon colors against container backgrounds

## Testing Tools
- WCAG Contrast Checker (browser extension)
- axe DevTools (browser extension)
- Lighthouse Accessibility audit

## Not in Scope (Phase 5)
- Keyboard navigation full audit
- Screen reader testing
- ARIA live regions
- Skip links

## Estimated Effort
- Phase 4: ~30 min
- Phase 5: ~1 hour

---

**Starting with Phase 4 now...**
