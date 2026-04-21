# Implementation Plan: Design System Implementation

## Overview

This implementation plan follows a 4-phase migration strategy to implement the comprehensive Design System across the Finsight AI Next.js frontend based on the existing green nature-inspired theme. The approach prioritizes foundation setup, theme functionality, component refactoring by priority, and final validation.

**Status**: All implementation tasks completed and verified against actual code (last verified: 2024)

## Tasks

- [ ] 1. Phase 1: Foundation - Design Tokens & Global Styles
  - [x] 1.1 Complete CSS custom properties in globals.css
    - Add missing design tokens: `--positive`, `--negative`, `--sidebar`
    - Ensure all color tokens are defined for both light and dark modes
    - Add spacing tokens: `--radius`, `--card-padding`, `--icon-circle-size`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 15.1_
  
  - [x] 1.2 Add global CSS utility classes to globals.css
    - Create `.card-surface` class with light/dark mode variants
    - Create `.table-rows` class for table border styling
    - Create `.kpi-icon-circle` class for 44px circular containers
    - Create typography classes: `.text-page-title`, `.text-card-title`, `.text-body-sm`, `.text-label-xs`
    - Add scrollbar styling with muted colors
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 15.2, 15.3, 15.4, 15.5, 15.6_
  
  - [x] 1.3 Extend Tailwind configuration with custom tokens
    - Add custom colors: `primary`, `background`, `foreground`, `card`, `border`, `sidebar`, `purple`, `positive`, `negative`
    - Add custom fontSize: `page-title`, `card-title`, `body-sm`, `label-xs`
    - Add custom spacing: `kpi` (44px)
    - Add custom borderRadius: `card` (1rem)
    - _Requirements: 1.6, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  
  - [x] 1.4 Update utility functions in lib/utils.ts
    - Update `formatChange` function to return object with `symbol`, `colorClass`, and `text`
    - Ensure `formatChange` returns ArrowUp/ArrowDown symbols (▲/▼)
    - Ensure `formatChange` returns correct color classes for positive/negative values
    - Ensure `formatChange` formats percentage to 2 decimal places
    - Add `formatCurrency` function if not present
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

- [ ] 2. Phase 2: Theme Toggle Implementation
  - [x] 2.1 Create ThemeToggle component
    - Create `frontend/components/ui/theme-toggle.tsx` file
    - Implement theme state management with useState
    - Add useEffect to read theme from localStorage on mount
    - Add useEffect to apply `.dark` class to document.documentElement
    - Implement toggleTheme function that updates state, localStorage, and DOM class
    - Render Sun icon when theme is dark, Moon icon when theme is light
    - Default to dark mode if no preference exists
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7_
  
  - [x] 2.2 Integrate ThemeToggle into Sidebar
    - Import ThemeToggle component in `frontend/components/ui/sidebar.tsx`
    - Add ThemeToggle button to sidebar header or footer section
    - Ensure proper styling and positioning
    - _Requirements: 17.1_
  
  - [x] 2.3 Verify theme system functionality
    - Test theme toggle switches between light and dark modes
    - Verify theme preference persists after page reload
    - Verify all CSS custom properties update correctly on theme change
    - Verify sidebar maintains `#12121F` background in both themes
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6_

- [ ] 3. Phase 3: Component Refactoring - Priority 1 (High-traffic pages)
  - [x] 3.1 Refactor Sidebar component
    - Update `frontend/components/ui/sidebar.tsx` to use design system specifications
    - Apply fixed dark background with inline style
    - Apply consistent border styling
    - Update active navigation item styling with green accent
    - Update inactive navigation item styling with muted colors
    - Apply consistent font size with medium weight to navigation items
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_
  
  - [x] 3.2 Refactor Dashboard page
    - Update `frontend/app/dashboard/page.tsx` to use design system
    - Apply `.text-page-title` class to page title
    - Wrap KPI cards in responsive grid with `gap-5` (20px)
    - Apply `.card-surface` and `p-6` to all card containers
    - Use `formatChange` utility for all percentage displays
    - Ensure KPI cards display icon circles with 44px diameter and 10% opacity accent background
    - Apply `.table-rows` class to top holdings table
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_
  
  - [x] 3.3 Refactor Portfolio page
    - Update `frontend/app/portfolio/page.tsx` to use design system
    - Apply `.card-surface` to broker cards
    - Apply `.table-rows` class to holdings table
    - Use `formatChange` utility for P&L and day change columns
    - Apply typography classes consistently (`.text-page-title`, `.text-card-title`, `.text-body-sm`)
    - Apply `#6C5ECF` color to sync and unlink buttons
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 4. Phase 3: Component Refactoring - Priority 2 (Feature pages)
  - [x] 4.1 Refactor Predictor page
    - Update `frontend/app/predictor/page.tsx` to use design system
    - Apply `.card-surface` to search and configuration containers
    - Apply `.card-surface` to prediction result containers
    - Use `formatChange` utility for price target changes
    - Apply `#6C5ECF` color to confidence bar
    - Apply typography classes consistently
    - Display signal (BUY/SELL/HOLD) with appropriate color coding
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_
  
  - [x] 4.2 Refactor Screener page
    - Update `frontend/app/screener/page.tsx` to use design system
    - Apply `.card-surface` to filter inputs container
    - Apply `.table-rows` class to results table
    - Use `formatChange` utility for price change column
    - Apply `#6C5ECF` color to scan button
    - Apply `rounded-2xl` (16px) border radius to input fields
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [x] 4.3 Refactor News page
    - Update `frontend/app/news/page.tsx` to use design system
    - Apply `.card-surface` to article containers
    - Add 3px left border to article cards with sentiment color
    - Apply `rounded-2xl` border radius to filter input
    - Apply `#6C5ECF` color to filter button
    - Apply typography classes for article titles and metadata
    - Display sentiment icons with appropriate colors (`#22C55E`, `#EF4444`, `#f59e0b`)
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [ ] 5. Phase 3: Component Refactoring - Priority 3 (Landing and Auth)
  - [x] 5.1 Refactor Landing page
    - Update `frontend/app/page.tsx` to use design system
    - Apply `.card-surface` to feature cards
    - Display icon circles (44px) for each feature with 10% opacity accent
    - Apply `#6C5ECF` color to primary call-to-action button
    - Apply `rounded-2xl` border radius to buttons
    - Apply typography classes for headings and body text
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_
  
  - [x] 5.2 Refactor Login page
    - Update `frontend/app/(auth)/login/page.tsx` to use design system
    - Apply `.card-surface` to form container
    - Apply `rounded-2xl` border radius to input fields
    - Apply `#6C5ECF` color to submit button
    - Apply typography classes consistently
    - _Requirements: 1.7, 2.1, 2.2, 2.3, 2.4_
  
  - [x] 5.3 Refactor Signup page
    - Update `frontend/app/(auth)/signup/page.tsx` to use design system
    - Apply `.card-surface` to form container
    - Apply `rounded-2xl` border radius to input fields
    - Apply `#6C5ECF` color to submit button
    - Apply typography classes consistently
    - _Requirements: 1.7, 2.1, 2.2, 2.3, 2.4_

- [ ] 6. Phase 4: Validation & Polish
  - [x] 6.1 Visual QA and cross-browser testing
    - Perform visual QA pass on all pages in both light and dark themes
    - Verify responsive behavior on mobile, tablet, and desktop viewports
    - Test in Chrome, Firefox, and Safari browsers
    - Verify consistency with existing green nature-inspired theme
    - _Requirements: All requirements_
  
  - [x] 6.2 Accessibility audit
    - Run accessibility audit using axe DevTools or similar tool
    - Verify all text meets WCAG AA contrast ratios (4.5:1 for normal text, 3:1 for large text)
    - Test keyboard navigation on all interactive elements
    - Verify theme toggle has proper aria-label
    - Verify tables have proper semantic structure
    - Verify icon-only buttons have accessible labels
    - _Requirements: All requirements_
  
  - [x] 6.3 Final validation checkpoint
    - Ensure all 17 requirements from requirements.md are implemented
    - Verify theme toggle works correctly in all scenarios
    - Verify all pages use consistent design tokens
    - Verify no hardcoded colors outside of design tokens
    - Run performance audit (Lighthouse) and ensure metrics are acceptable
    - Ensure all tests pass, ask the user if questions arise
    - _Requirements: All requirements_

## Notes

- This implementation follows a phased approach to minimize risk and enable incremental validation
- Phase 1 establishes the foundation that all subsequent phases depend on
- Phase 2 enables theme switching functionality early for testing
- Phase 3 is split by priority to deliver value to high-traffic pages first
- Phase 4 ensures quality and accessibility standards are met
- Each task references specific requirements for traceability
- All tasks involve writing or modifying code - no deployment or user testing tasks included
