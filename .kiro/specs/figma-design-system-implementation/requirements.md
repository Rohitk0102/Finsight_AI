# Requirements Document

## Introduction

This document specifies the requirements for implementing a comprehensive Design System across the Finsight AI Next.js frontend application. The implementation standardizes the existing green nature-inspired visual design with specific colors, typography, spacing, and component styling to ensure consistency and improve user experience across all pages and components.

## Glossary

- **Design_System**: The collection of reusable design tokens, components, and patterns defined in Figma specifications
- **Design_Token**: A named design decision (color, spacing, typography) stored as a CSS custom property or Tailwind configuration
- **Card_Component**: A rounded rectangular container with padding, background, and border styling used throughout the application
- **KPI_Card**: A specialized card displaying key performance indicators with icon circles, values, and percentage changes
- **Sidebar**: The left navigation panel that remains visible across all authenticated pages
- **Theme_Mode**: The visual appearance mode (light or dark) that affects color schemes
- **Typography_Scale**: The hierarchical system of font sizes and weights (page title, card title, body, label)
- **Percentage_Badge**: A UI element displaying percentage changes with arrow icons and color coding
- **Table_Component**: A data display component with rows and columns following specific border styling
- **Icon_Circle**: A circular container (44px diameter) with 10% opacity background displaying an icon
- **Theme_Toggle**: A button component that allows users to switch between light and dark Theme_Mode

## Requirements

### Requirement 1: Design Token Configuration

**User Story:** As a developer, I want design tokens configured in the build system, so that consistent styling can be applied throughout the application

#### Acceptance Criteria

1. THE Design_System SHALL define primary purple color as #6C5ECF in CSS custom properties
2. THE Design_System SHALL define light mode background as #F8F9FF and dark mode background as #0E0E1A
3. THE Design_System SHALL define light mode card background as #FFFFFF and dark mode card background as #16162A
4. THE Design_System SHALL define sidebar background as #12121F independent of Theme_Mode
5. THE Design_System SHALL define positive color as #22C55E and negative color as #EF4444
6. THE Design_System SHALL extend Tailwind configuration with custom color tokens
7. THE Design_System SHALL define card border radius as 16px (rounded-2xl)

### Requirement 2: Typography System

**User Story:** As a designer, I want a consistent typography scale, so that text hierarchy is clear and readable

#### Acceptance Criteria

1. THE Typography_Scale SHALL define page title as 22px with 500 font weight
2. THE Typography_Scale SHALL define card title as 15px with 500 font weight
3. THE Typography_Scale SHALL define body text as 13px with 400 font weight
4. THE Typography_Scale SHALL define label text as 11px with 400 font weight
5. THE Typography_Scale SHALL provide CSS utility classes for each typography level
6. THE Typography_Scale SHALL provide Tailwind configuration for each typography level

### Requirement 3: Card Component Styling

**User Story:** As a user, I want visually consistent cards, so that the interface feels cohesive

#### Acceptance Criteria

1. THE Card_Component SHALL apply 16px border radius (rounded-2xl)
2. THE Card_Component SHALL apply 24px padding (p-6)
3. WHEN Theme_Mode is light, THE Card_Component SHALL apply box-shadow [0_1px_3px_rgba(0,0,0,0.06)]
4. WHEN Theme_Mode is light, THE Card_Component SHALL apply border using CSS border property
5. WHEN Theme_Mode is dark, THE Card_Component SHALL apply border as 1px solid rgba(255,255,255,0.07)
6. WHEN Theme_Mode is dark, THE Card_Component SHALL remove box-shadow
7. THE Card_Component SHALL use .card-surface CSS class for consistent application

### Requirement 4: KPI Card Implementation

**User Story:** As a user, I want KPI cards to display metrics clearly, so that I can quickly understand portfolio performance

#### Acceptance Criteria

1. THE KPI_Card SHALL display an Icon_Circle with 44px diameter
2. THE KPI_Card SHALL apply 10% opacity accent color as Icon_Circle background
3. THE KPI_Card SHALL display metric label using label text size (11px)
4. THE KPI_Card SHALL display metric value using 22px font size with 500 weight
5. WHEN a percentage change is present, THE KPI_Card SHALL display a Percentage_Badge
6. THE KPI_Card SHALL apply 24px padding (p-6)
7. THE KPI_Card SHALL use Card_Component styling

### Requirement 5: Percentage Change Display

**User Story:** As a user, I want percentage changes to be visually distinct, so that I can quickly identify gains and losses

#### Acceptance Criteria

1. WHEN percentage value is positive or zero, THE Percentage_Badge SHALL display ArrowUp icon from lucide-react
2. WHEN percentage value is negative, THE Percentage_Badge SHALL display ArrowDown icon from lucide-react
3. WHEN percentage value is positive or zero, THE Percentage_Badge SHALL apply #22C55E color
4. WHEN percentage value is negative, THE Percentage_Badge SHALL apply #EF4444 color
5. THE Percentage_Badge SHALL display absolute percentage value with 2 decimal places
6. THE Percentage_Badge SHALL use label text size (11px) with medium font weight
7. THE Percentage_Badge SHALL render icons at 12px size (h-3 w-3)

### Requirement 6: Sidebar Styling

**User Story:** As a user, I want consistent navigation, so that I can easily move between sections

#### Acceptance Criteria

1. THE Sidebar SHALL apply #12121F background color independent of Theme_Mode
2. THE Sidebar SHALL apply right border as 1px solid rgba(255,255,255,0.07)
3. WHEN a navigation item is active, THE Sidebar SHALL apply bg-[#6C5ECF]/10 background
4. WHEN a navigation item is active, THE Sidebar SHALL apply #6C5ECF text color
5. WHEN a navigation item is active, THE Sidebar SHALL display 2px left border in #6C5ECF
6. WHEN a navigation item is inactive, THE Sidebar SHALL apply text-white/50 color
7. WHEN a navigation item is inactive and hovered, THE Sidebar SHALL apply text-white/80 color
8. THE Sidebar SHALL apply 13px font size with medium weight to navigation items

### Requirement 7: Table Component Styling

**User Story:** As a user, I want data tables to be clean and readable, so that I can scan information efficiently

#### Acceptance Criteria

1. THE Table_Component SHALL apply row divider borders between tbody rows
2. THE Table_Component SHALL NOT apply outer border to table wrapper
3. THE Table_Component SHALL apply 1px solid border using CSS border color variable
4. THE Table_Component SHALL remove border from last tbody row
5. THE Table_Component SHALL apply hover state with bg-accent/30 on tbody rows
6. THE Table_Component SHALL use .table-rows CSS class for consistent styling
7. THE Table_Component SHALL apply 24px horizontal padding (px-6) to cells

### Requirement 8: Dashboard Page Implementation

**User Story:** As a user, I want the dashboard to follow the design system, so that it looks polished and professional

#### Acceptance Criteria

1. THE Dashboard_Page SHALL display page title using Typography_Scale page title style
2. THE Dashboard_Page SHALL display KPI cards in a responsive grid with 20px gap
3. THE Dashboard_Page SHALL implement KPI_Card components for portfolio metrics
4. THE Dashboard_Page SHALL display top holdings in a Table_Component
5. THE Dashboard_Page SHALL apply Card_Component styling to AI analysis cards
6. THE Dashboard_Page SHALL use Percentage_Badge for all percentage displays

### Requirement 9: Portfolio Page Implementation

**User Story:** As a user, I want the portfolio page to follow the design system, so that holdings are clearly presented

#### Acceptance Criteria

1. THE Portfolio_Page SHALL display holdings in a Table_Component
2. THE Portfolio_Page SHALL display broker cards using Card_Component styling
3. THE Portfolio_Page SHALL use Percentage_Badge for P&L and day change columns
4. THE Portfolio_Page SHALL apply Typography_Scale consistently to all text
5. THE Portfolio_Page SHALL display sync and unlink buttons with #6C5ECF accent color

### Requirement 10: Screener Page Implementation

**User Story:** As a user, I want the screener page to follow the design system, so that stock filtering is intuitive

#### Acceptance Criteria

1. THE Screener_Page SHALL display filter inputs in a Card_Component
2. THE Screener_Page SHALL display results in a Table_Component
3. THE Screener_Page SHALL use Percentage_Badge for price change column
4. THE Screener_Page SHALL apply #6C5ECF color to scan button
5. THE Screener_Page SHALL apply 16px border radius to input fields

### Requirement 11: Predictor Page Implementation

**User Story:** As a user, I want the predictor page to follow the design system, so that predictions are clearly communicated

#### Acceptance Criteria

1. THE Predictor_Page SHALL display search and configuration in a Card_Component
2. THE Predictor_Page SHALL display prediction results in Card_Component containers
3. THE Predictor_Page SHALL use Percentage_Badge for price target changes
4. THE Predictor_Page SHALL display confidence bar using #6C5ECF color
5. THE Predictor_Page SHALL apply Typography_Scale to all text elements
6. THE Predictor_Page SHALL display signal (BUY/SELL/HOLD) with appropriate color coding

### Requirement 12: News Page Implementation

**User Story:** As a user, I want the news page to follow the design system, so that articles are easy to scan

#### Acceptance Criteria

1. THE News_Page SHALL display articles in Card_Component containers
2. THE News_Page SHALL apply 3px left border to article cards with sentiment color
3. THE News_Page SHALL display filter input with 16px border radius
4. THE News_Page SHALL apply #6C5ECF color to filter button
5. THE News_Page SHALL use Typography_Scale for article titles and metadata
6. THE News_Page SHALL display sentiment icons with appropriate colors (#22C55E, #EF4444, #f59e0b)

### Requirement 13: Landing Page Implementation

**User Story:** As a visitor, I want the landing page to follow the design system, so that the product looks professional

#### Acceptance Criteria

1. THE Landing_Page SHALL display feature cards using Card_Component styling
2. THE Landing_Page SHALL display Icon_Circle (44px) for each feature with 10% opacity accent
3. THE Landing_Page SHALL apply #6C5ECF color to primary call-to-action button
4. THE Landing_Page SHALL apply 16px border radius to buttons
5. THE Landing_Page SHALL use Typography_Scale for headings and body text

### Requirement 14: Utility Function Enhancement

**User Story:** As a developer, I want utility functions for common formatting, so that code is DRY and consistent

#### Acceptance Criteria

1. THE Utility_Module SHALL provide formatChange function returning icon component, color class, and formatted text
2. THE formatChange function SHALL return ArrowUp component for positive or zero values
3. THE formatChange function SHALL return ArrowDown component for negative values
4. THE formatChange function SHALL return "text-[#22C55E]" class for positive values
5. THE formatChange function SHALL return "text-[#EF4444]" class for negative values
6. THE formatChange function SHALL format percentage with 2 decimal places

### Requirement 15: Global Styles Configuration

**User Story:** As a developer, I want global styles configured, so that design tokens are available application-wide

#### Acceptance Criteria

1. THE Global_Styles SHALL define CSS custom properties for all design tokens
2. THE Global_Styles SHALL define .card-surface class with light and dark mode variants
3. THE Global_Styles SHALL define .table-rows class for table border styling
4. THE Global_Styles SHALL define .kpi-icon-circle class for 44px circular containers
5. THE Global_Styles SHALL define typography utility classes (text-page-title, text-card-title, text-body-sm, text-label-xs)
6. THE Global_Styles SHALL configure scrollbar styling with muted colors

### Requirement 16: Theme Mode Support

**User Story:** As a user, I want the application to support light and dark modes, so that I can choose my preferred viewing experience

#### Acceptance Criteria

1. THE Application SHALL support light Theme_Mode with #F8F9FF background
2. THE Application SHALL support dark Theme_Mode with #0E0E1A background
3. WHEN Theme_Mode changes, THE Application SHALL update all Card_Component styling
4. WHEN Theme_Mode changes, THE Sidebar SHALL maintain #12121F background
5. THE Application SHALL apply .dark class to root element for dark Theme_Mode
6. THE Application SHALL persist Theme_Mode selection across sessions

### Requirement 17: Theme Toggle Component

**User Story:** As a user, I want a theme toggle button, so that I can switch between light and dark modes

#### Acceptance Criteria

1. THE Theme_Toggle SHALL display in the application header or sidebar
2. WHEN Theme_Toggle is clicked, THE Application SHALL switch Theme_Mode
3. THE Theme_Toggle SHALL display Sun icon when Theme_Mode is dark
4. THE Theme_Toggle SHALL display Moon icon when Theme_Mode is light
5. THE Theme_Toggle SHALL store Theme_Mode preference in localStorage
6. WHEN Application loads, THE Theme_Toggle SHALL read Theme_Mode from localStorage
7. IF no Theme_Mode preference exists, THE Theme_Toggle SHALL default to dark mode
