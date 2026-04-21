# Design Document: Design System Implementation

## Overview

This design document specifies the technical implementation of a comprehensive design system for the Finsight AI Next.js frontend application based on the existing green nature-inspired theme. The design system standardizes visual design through design tokens, reusable CSS classes, component patterns, and utility functions to ensure consistency across all pages.

The implementation builds upon the existing partial implementation in `globals.css` and `tailwind.config.ts`, completing the design system with:
- Comprehensive design token architecture
- Global CSS utility classes for cards, tables, typography, and icons
- Component refactoring patterns for all pages
- Theme toggle functionality with localStorage persistence
- Utility functions for common formatting patterns

### Design Goals

1. **Consistency**: Unified visual language across all pages and components
2. **Maintainability**: Centralized design decisions in tokens and utilities
3. **Developer Experience**: Simple, intuitive class names and helper functions
4. **Performance**: Minimal CSS overhead through Tailwind's purge mechanism
5. **Accessibility**: Proper contrast ratios and semantic HTML structure

### Technology Stack

- **Next.js 14**: App Router with React Server Components
- **Tailwind CSS 3.x**: Utility-first CSS framework
- **CSS Custom Properties**: Design token storage
- **TypeScript**: Type-safe utility functions
- **lucide-react**: Icon library for UI elements

## Architecture

### Design Token Layer

Design tokens are the atomic design decisions (colors, spacing, typography) that form the foundation of the design system. They are implemented in two layers:

1. **CSS Custom Properties** (in `globals.css`): Runtime-accessible tokens for dynamic theming
2. **Tailwind Configuration** (in `tailwind.config.ts`): Build-time tokens for utility class generation

This dual-layer approach enables:
- Dynamic theme switching via CSS custom properties
- Static utility class generation for optimal performance
- Consistent token access across CSS and Tailwind utilities

### Component Pattern Layer

Components follow a consistent pattern:
- **Structural classes**: Tailwind utilities for layout and spacing
- **Surface classes**: Custom CSS classes (`.card-surface`, `.table-rows`) for themed surfaces
- **Typography classes**: Custom classes (`.text-page-title`, `.text-card-title`) for text hierarchy
- **Utility functions**: TypeScript helpers (`formatChange`, `formatCurrency`) for data formatting

### Theme System Architecture

The theme system uses a class-based approach:
- Root element receives `.dark` class for dark mode
- CSS custom properties change values based on `.dark` presence
- Sidebar maintains fixed dark background independent of theme
- localStorage persists user preference across sessions

## Components and Interfaces

### 1. Design Token Configuration

#### CSS Custom Properties (globals.css)

```css
@layer base {
  :root {
    /* Primary purple accent */
    --primary: 253 52% 57%;               /* #6C5ECF */
    --primary-foreground: 0 0% 100%;

    /* Light mode palette */
    --background: 230 100% 99%;           /* #F8F9FF */
    --foreground: 240 15% 12%;
    --card: 0 0% 100%;                    /* #FFFFFF */
    --card-foreground: 240 15% 12%;
    --border: 230 20% 88%;
    --muted-foreground: 240 8% 48%;
    
    /* Semantic colors */
    --positive: 142 71% 45%;              /* #22C55E */
    --negative: 0 84% 60%;                /* #EF4444 */
    
    /* Spacing */
    --radius: 1rem;                       /* 16px card radius */
  }

  .dark {
    --primary: 253 52% 57%;               /* #6C5ECF */
    --primary-foreground: 0 0% 100%;

    /* Dark mode palette */
    --background: 240 22% 8%;             /* #0E0E1A */
    --foreground: 0 0% 95%;
    --card: 240 22% 13%;                  /* #16162A */
    --card-foreground: 0 0% 95%;
    --border: 240 15% 18%;
    --muted-foreground: 240 8% 55%;
  }
}
```

#### Tailwind Configuration Extension

```typescript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        // HSL-based tokens from CSS custom properties
        primary: "hsl(var(--primary))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: "hsl(var(--card))",
        border: "hsl(var(--border))",
        
        // Fixed colors (mode-independent)
        sidebar: "#12121F",
        purple: "#6C5ECF",
        positive: "#22C55E",
        negative: "#EF4444",
      },
      fontSize: {
        "page-title": ["22px", { fontWeight: "500", lineHeight: "1.3" }],
        "card-title": ["15px", { fontWeight: "500", lineHeight: "1.4" }],
        "body-sm": ["13px", { fontWeight: "400", lineHeight: "1.5" }],
        "label-xs": ["11px", { fontWeight: "400", lineHeight: "1.4" }],
      },
      spacing: {
        "kpi": "44px",  // Icon circle size
      },
      borderRadius: {
        card: "1rem",   // 16px for cards
      },
    },
  },
};
```

### 2. Global CSS Classes

#### Card Surface Class

```css
.card-surface {
  @apply bg-card rounded-2xl;
  border: 1px solid hsl(var(--border));
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.dark .card-surface {
  border: 1px solid rgba(255, 255, 255, 0.07);
  box-shadow: none;
}
```

**Usage**: Apply to any card container for consistent styling
**Behavior**: Automatically adapts border and shadow based on theme

#### Table Rows Class

```css
.table-rows tbody tr {
  border-bottom: 1px solid hsl(var(--border));
}

.table-rows tbody tr:last-child {
  border-bottom: none;
}

.table-rows tbody tr:hover {
  background: hsl(var(--accent) / 0.3);
}
```

**Usage**: Apply to `<table>` element for row-divider styling
**Behavior**: Adds borders between rows, removes border from last row, adds hover state

#### KPI Icon Circle Class

```css
.kpi-icon-circle {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
```

**Usage**: Container for icons in KPI cards
**Background**: Set inline with 10% opacity accent color (e.g., `#6C5ECF1A`)

#### Typography Classes

```css
.text-page-title  { font-size: 22px; font-weight: 500; line-height: 1.3; }
.text-card-title  { font-size: 15px; font-weight: 500; line-height: 1.4; }
.text-body-sm     { font-size: 13px; font-weight: 400; line-height: 1.5; }
.text-label-xs    { font-size: 11px; font-weight: 400; line-height: 1.4; }
```

**Usage**: Apply to text elements for consistent typography hierarchy

### 3. Component Patterns

#### KPI Card Component Pattern

```typescript
interface KpiCardProps {
  label: string;
  value: string;
  icon: React.ElementType;
  accent: string;
  change?: number | null;
  subtitle?: string;
}

function KpiCard({ label, value, icon: Icon, accent, change, subtitle }: KpiCardProps) {
  return (
    <div className="card-surface p-6">
      <div className="flex items-start justify-between mb-4">
        <p className="text-label-xs text-muted-foreground">{label}</p>
        <div 
          className="kpi-icon-circle" 
          style={{ background: accent + "1A" }}
        >
          <Icon className="h-5 w-5" style={{ color: accent }} />
        </div>
      </div>
      <p className="text-[22px] font-semibold leading-tight">{value}</p>
      {change !== null && change !== undefined ? (
        <ChangeBadge value={change} />
      ) : (
        <p className="text-label-xs text-muted-foreground mt-1.5">{subtitle}</p>
      )}
    </div>
  );
}
```

#### Percentage Badge Component Pattern

```typescript
function ChangeBadge({ value }: { value: number }) {
  const { symbol, colorClass, text } = formatChange(value);
  return (
    <span className={`text-label-xs font-medium ${colorClass}`}>
      {symbol} {text}
    </span>
  );
}
```

#### Table Component Pattern

```tsx
<div className="card-surface overflow-x-auto">
  <table className="w-full text-body-sm min-w-[700px] table-rows">
    <thead>
      <tr style={{ borderBottom: "1px solid hsl(var(--border))" }}>
        <th className="px-6 py-3 text-left text-label-xs text-muted-foreground font-medium">
          Column Header
        </th>
      </tr>
    </thead>
    <tbody>
      <tr className="hover:bg-accent/30 transition-colors">
        <td className="px-6 py-4">Cell content</td>
      </tr>
    </tbody>
  </table>
</div>
```

### 4. Utility Functions

#### formatChange Function

```typescript
// lib/utils.ts
export function formatChange(value: number): {
  symbol: "▲" | "▼";
  colorClass: string;
  text: string;
} {
  const isPositive = value >= 0;
  return {
    symbol: isPositive ? "▲" : "▼",
    colorClass: isPositive ? "text-[#22C55E]" : "text-[#EF4444]",
    text: `${Math.abs(value).toFixed(2)}%`,
  };
}
```

**Returns**: Object with symbol (triangle), color class, and formatted text
**Usage**: Consistent percentage display across all components

#### formatCurrency Function

```typescript
export function formatCurrency(value: number, currency = "INR"): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(value);
}
```

### 5. Theme Toggle Component

```typescript
// components/ui/theme-toggle.tsx
"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

export function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark">("dark");

  useEffect(() => {
    // Read from localStorage on mount
    const stored = localStorage.getItem("theme") as "light" | "dark" | null;
    const initial = stored || "dark";
    setTheme(initial);
    document.documentElement.classList.toggle("dark", initial === "dark");
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    localStorage.setItem("theme", newTheme);
    document.documentElement.classList.toggle("dark", newTheme === "dark");
  };

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-lg hover:bg-accent transition-colors"
      aria-label="Toggle theme"
    >
      {theme === "dark" ? (
        <Sun className="h-4 w-4 text-muted-foreground" />
      ) : (
        <Moon className="h-4 w-4 text-muted-foreground" />
      )}
    </button>
  );
}
```

**Placement**: Add to Sidebar component or application header
**Behavior**: Toggles `.dark` class on `<html>` element, persists to localStorage

### 6. Sidebar Component Styling

The sidebar uses the existing green nature-inspired theme with dark background and maintains consistency across the application.

**Key Features**:
- Fixed dark background independent of theme mode
- Active state: green accent background, left border, and icon color
- Inactive state: muted opacity with hover effects
- Consistent typography and spacing

## Data Models

### Theme Preference Model

```typescript
type ThemeMode = "light" | "dark";

interface ThemePreference {
  mode: ThemeMode;
  timestamp: number;
}
```

**Storage**: localStorage key `"theme"`
**Default**: `"dark"`

### Design Token Model

```typescript
interface DesignTokens {
  colors: {
    primary: string;
    background: string;
    card: string;
    border: string;
    positive: string;
    negative: string;
    sidebar: string;
  };
  typography: {
    pageTitle: { size: string; weight: string; lineHeight: string };
    cardTitle: { size: string; weight: string; lineHeight: string };
    body: { size: string; weight: string; lineHeight: string };
    label: { size: string; weight: string; lineHeight: string };
  };
  spacing: {
    cardPadding: string;
    cardRadius: string;
    iconCircleSize: string;
    gridGap: string;
  };
}
```

### Component Props Models

```typescript
interface KpiCardData {
  label: string;
  value: string;
  icon: React.ElementType;
  accent: string;
  change?: number | null;
  subtitle?: string;
}

interface TableColumn {
  key: string;
  label: string;
  align: "left" | "right" | "center";
  render?: (value: any, row: any) => React.ReactNode;
}

interface PercentageBadgeProps {
  value: number;
  size?: "sm" | "md";
}
```

## Error Handling

### Theme Toggle Error Handling

```typescript
useEffect(() => {
  try {
    const stored = localStorage.getItem("theme");
    const initial = (stored === "light" || stored === "dark") ? stored : "dark";
    setTheme(initial);
    document.documentElement.classList.toggle("dark", initial === "dark");
  } catch (error) {
    console.warn("Failed to read theme preference, defaulting to dark mode");
    setTheme("dark");
    document.documentElement.classList.add("dark");
  }
}, []);

const toggleTheme = () => {
  try {
    const newTheme = theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    localStorage.setItem("theme", newTheme);
    document.documentElement.classList.toggle("dark", newTheme === "dark");
  } catch (error) {
    console.error("Failed to save theme preference:", error);
    // Theme still changes in current session even if localStorage fails
  }
};
```

### CSS Fallbacks

```css
/* Fallback for browsers without CSS custom property support */
.card-surface {
  background: #FFFFFF;
  background: var(--card, #FFFFFF);
  border: 1px solid #E5E7EB;
  border: 1px solid hsl(var(--border), #E5E7EB);
}
```

### Missing Icon Handling

```typescript
function KpiIconCircle({ icon: Icon, accentHex }: { icon?: React.ElementType; accentHex: string }) {
  const IconComponent = Icon || TrendingUp; // Fallback icon
  return (
    <div className="kpi-icon-circle" style={{ background: accentHex + "1A" }}>
      <IconComponent className="h-5 w-5" style={{ color: accentHex }} />
    </div>
  );
}
```

## Testing Strategy

### Unit Tests

1. **Utility Function Tests** (`lib/utils.test.ts`)
   - `formatChange` returns correct symbol for positive/negative/zero values
   - `formatChange` returns correct color classes
   - `formatChange` formats percentage to 2 decimal places
   - `formatCurrency` formats INR correctly
   - `formatCurrency` handles edge cases (0, negative, very large numbers)

2. **Theme Toggle Tests** (`components/ui/theme-toggle.test.tsx`)
   - Component renders Sun icon in dark mode
   - Component renders Moon icon in light mode
   - Clicking toggle switches theme
   - localStorage is updated on theme change
   - Theme persists across component remounts
   - Defaults to dark mode when no preference exists

3. **Component Pattern Tests**
   - KPI card renders with all props
   - KPI card handles missing change value
   - Percentage badge displays correct icon and color
   - Table rows apply hover styles correctly

### Integration Tests

1. **Theme System Integration**
   - Theme toggle affects all pages
   - Sidebar maintains dark background in both themes
   - Card surfaces update styling on theme change
   - CSS custom properties update correctly

2. **Page-Level Integration**
   - Dashboard displays KPI cards with correct styling
   - Portfolio table uses row-divider pattern
   - News cards display sentiment borders correctly
   - Predictor page uses purple accent consistently

### Visual Regression Tests

1. **Snapshot Tests** (using Playwright or Chromatic)
   - Dashboard page in light mode
   - Dashboard page in dark mode
   - Portfolio table with multiple rows
   - KPI cards with positive/negative changes
   - Sidebar active/inactive states
   - News cards with different sentiments

### Accessibility Tests

1. **Color Contrast**
   - All text meets WCAG AA contrast ratios (4.5:1 for normal text, 3:1 for large text)
   - Positive/negative colors have sufficient contrast against backgrounds
   - Muted text maintains readable contrast

2. **Keyboard Navigation**
   - Theme toggle is keyboard accessible
   - Sidebar navigation items are focusable
   - Table rows are keyboard navigable
   - Focus indicators are visible

3. **Screen Reader**
   - Theme toggle has proper aria-label
   - Tables have proper semantic structure
   - Icon-only buttons have accessible labels

### Manual Testing Checklist

- [ ] Theme toggle switches between light and dark modes
- [ ] Theme preference persists after page reload
- [ ] All pages use consistent card styling
- [ ] Tables display row dividers correctly
- [ ] KPI cards show icon circles with correct size and opacity
- [ ] Percentage badges display correct arrows and colors
- [ ] Sidebar maintains dark background in both themes
- [ ] Typography hierarchy is consistent across pages
- [ ] Hover states work on interactive elements
- [ ] Responsive layout works on mobile, tablet, desktop

## Migration Strategy

### Phase 1: Foundation (Design Tokens & Global Styles)

**Files to modify**:
- `frontend/app/globals.css` - Complete design token definitions
- `frontend/tailwind.config.ts` - Extend with custom tokens
- `frontend/lib/utils.ts` - Add/update utility functions

**Tasks**:
1. Audit existing CSS custom properties
2. Add missing design tokens (positive, negative, sidebar)
3. Complete typography scale classes
4. Add `.card-surface`, `.table-rows`, `.kpi-icon-circle` classes
5. Update `formatChange` function to return object with symbol, color, text
6. Test design tokens in both light and dark modes

### Phase 2: Theme Toggle Implementation

**Files to create**:
- `frontend/components/ui/theme-toggle.tsx` - Theme toggle component
- `frontend/hooks/use-theme.ts` - Theme management hook (optional)

**Files to modify**:
- `frontend/components/ui/sidebar.tsx` - Add theme toggle button
- `frontend/app/layout.tsx` - Ensure proper theme initialization

**Tasks**:
1. Create ThemeToggle component with localStorage persistence
2. Add theme toggle to Sidebar component
3. Test theme switching across all pages
4. Verify localStorage persistence

### Phase 3: Component Refactoring

**Priority 1 - High-traffic pages**:
- `frontend/app/dashboard/page.tsx` - Already mostly compliant, minor tweaks
- `frontend/app/portfolio/page.tsx` - Update table styling
- `frontend/components/ui/sidebar.tsx` - Ensure exact Figma spec compliance

**Priority 2 - Feature pages**:
- `frontend/app/predictor/page.tsx` - Update card and button styling
- `frontend/app/screener/page.tsx` - Update table and filter card styling
- `frontend/app/news/page.tsx` - Update article card styling

**Priority 3 - Landing and auth**:
- `frontend/app/page.tsx` - Update feature cards
- `frontend/app/(auth)/login/page.tsx` - Update form styling
- `frontend/app/(auth)/signup/page.tsx` - Update form styling

**Refactoring Pattern**:
1. Replace inline styles with design tokens
2. Apply `.card-surface` to card containers
3. Apply `.table-rows` to tables
4. Use typography classes (`.text-page-title`, etc.)
5. Replace percentage display logic with `formatChange` utility
6. Use `#6C5ECF` for all primary buttons and accents
7. Ensure 16px border radius on all cards and inputs

### Phase 4: Validation & Polish

**Tasks**:
1. Visual QA pass on all pages in both themes
2. Verify responsive behavior on mobile/tablet
3. Run accessibility audit (axe DevTools)
4. Test keyboard navigation
5. Verify localStorage persistence
6. Cross-browser testing (Chrome, Firefox, Safari)
7. Performance audit (Lighthouse)

### Rollback Strategy

If issues arise during migration:
1. **Per-page rollback**: Git revert specific page changes
2. **Token rollback**: Revert `globals.css` and `tailwind.config.ts` changes
3. **Component rollback**: Revert individual component files
4. **Feature flag**: Wrap theme toggle in feature flag for gradual rollout

### Migration Validation Criteria

- [ ] All 17 requirements from requirements.md are implemented
- [ ] No visual regressions compared to Figma designs
- [ ] Theme toggle works correctly in all scenarios
- [ ] All pages use consistent design tokens
- [ ] No hardcoded colors outside of design tokens
- [ ] Accessibility audit passes with no critical issues
- [ ] Performance metrics remain within acceptable ranges
- [ ] Cross-browser compatibility verified

## File Structure

```
frontend/
├── app/
│   ├── globals.css                    # Design tokens, global classes
│   ├── layout.tsx                     # Root layout with theme initialization
│   ├── page.tsx                       # Landing page (refactor feature cards)
│   ├── dashboard/
│   │   └── page.tsx                   # Dashboard (minor tweaks)
│   ├── portfolio/
│   │   └── page.tsx                   # Portfolio (table styling)
│   ├── predictor/
│   │   └── page.tsx                   # Predictor (card/button styling)
│   ├── screener/
│   │   └── page.tsx                   # Screener (table/filter styling)
│   ├── news/
│   │   └── page.tsx                   # News (article card styling)
│   └── (auth)/
│       ├── login/page.tsx             # Login (form styling)
│       └── signup/page.tsx            # Signup (form styling)
├── components/
│   └── ui/
│       ├── sidebar.tsx                # Sidebar (ensure Figma compliance)
│       └── theme-toggle.tsx           # NEW: Theme toggle component
├── lib/
│   └── utils.ts                       # Utility functions (update formatChange)
├── tailwind.config.ts                 # Tailwind token extensions
└── package.json
```

## Implementation Notes

### CSS Custom Properties vs Tailwind Classes

**Use CSS custom properties when**:
- Value needs to change dynamically (theme switching)
- Value is used in inline styles
- Value needs to be accessed in JavaScript

**Use Tailwind classes when**:
- Static utility needed (spacing, layout)
- Performance is critical (purged at build time)
- Developer experience benefits from autocomplete

### Inline Styles vs Classes

**Use inline styles for**:
- Dynamic accent colors (KPI icon circles with 10% opacity)
- Sidebar fixed background (mode-independent)
- Active state indicators (left border color)

**Use classes for**:
- All structural layout (Tailwind utilities)
- Themed surfaces (`.card-surface`)
- Typography hierarchy (`.text-page-title`)

### Performance Considerations

1. **Tailwind Purging**: Ensure all custom classes are safelisted
2. **CSS Custom Properties**: Minimal performance impact, enables dynamic theming
3. **Icon Loading**: lucide-react tree-shakes unused icons
4. **localStorage**: Synchronous read on mount is acceptable for theme preference

### Browser Support

- **Modern browsers**: Full support (Chrome 88+, Firefox 85+, Safari 14+)
- **CSS Custom Properties**: Supported in all target browsers
- **localStorage**: Supported in all target browsers
- **Fallbacks**: Provided for older browsers where necessary

