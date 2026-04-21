/**
 * Theme System Verification Script
 * Task 2.3: Verify theme system functionality
 * 
 * This script tests the theme system implementation against requirements:
 * - 16.1, 16.2, 16.3, 16.4, 16.5, 16.6
 * 
 * Run with: node frontend/test-theme-system.js
 */

const fs = require('fs');
const path = require('path');

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

const results = {
  passed: 0,
  failed: 0,
  total: 0,
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function test(name, condition, requirement, details = '') {
  results.total++;
  if (condition) {
    results.passed++;
    log(`✓ ${name}`, 'green');
    if (details) log(`  ${details}`, 'cyan');
  } else {
    results.failed++;
    log(`✗ ${name}`, 'red');
    if (details) log(`  ${details}`, 'yellow');
  }
  log(`  Requirement: ${requirement}`, 'blue');
  console.log('');
}

function readFile(filePath) {
  try {
    return fs.readFileSync(path.join(__dirname, filePath), 'utf8');
  } catch (error) {
    return null;
  }
}

function checkFileExists(filePath) {
  return fs.existsSync(path.join(__dirname, filePath));
}

log('\n=== Theme System Verification Tests ===\n', 'cyan');
log('Task 2.3: Verify theme system functionality\n', 'blue');

// Test 1: Theme Toggle Component Exists
test(
  'Theme Toggle Component Exists',
  checkFileExists('components/ui/theme-toggle.tsx'),
  '17.1, 17.2',
  'File: components/ui/theme-toggle.tsx'
);

// Test 2: Theme Toggle Implementation
const themeToggleContent = readFile('components/ui/theme-toggle.tsx');
if (themeToggleContent) {
  test(
    'Theme Toggle uses localStorage',
    themeToggleContent.includes('localStorage.getItem("theme")') &&
    themeToggleContent.includes('localStorage.setItem("theme"'),
    '17.5, 17.6',
    'localStorage.getItem and setItem found'
  );

  test(
    'Theme Toggle manages .dark class',
    themeToggleContent.includes('document.documentElement.classList.toggle("dark"'),
    '16.5',
    'Toggles .dark class on document.documentElement'
  );

  test(
    'Theme Toggle shows Sun/Moon icons',
    themeToggleContent.includes('Sun') && themeToggleContent.includes('Moon'),
    '17.3, 17.4',
    'Sun and Moon icons from lucide-react'
  );

  test(
    'Theme Toggle defaults to dark mode',
    themeToggleContent.includes('|| "dark"') || themeToggleContent.includes('?? "dark"'),
    '17.7',
    'Defaults to dark when no preference exists'
  );
}

// Test 3: Global CSS - Design Tokens
const globalsCss = readFile('app/globals.css');
if (globalsCss) {
  test(
    'Light mode background token (#F8F9FF)',
    globalsCss.includes('--background: 230 100% 99%'),
    '1.2, 16.1',
    '--background: 230 100% 99% (HSL for #F8F9FF)'
  );

  test(
    'Dark mode background token (#0E0E1A)',
    globalsCss.includes('.dark') && globalsCss.match(/\.dark[\s\S]*--background: 240 22% 8%/),
    '1.2, 16.2',
    '--background: 240 22% 8% (HSL for #0E0E1A)'
  );

  test(
    'Light mode card background (#FFFFFF)',
    globalsCss.includes('--card: 0 0% 100%'),
    '1.3, 16.1',
    '--card: 0 0% 100% (HSL for #FFFFFF)'
  );

  test(
    'Dark mode card background (#16162A)',
    globalsCss.match(/\.dark[\s\S]*--card: 240 22% 13%/),
    '1.3, 16.2',
    '--card: 240 22% 13% (HSL for #16162A)'
  );

  test(
    'Primary purple color (#6C5ECF)',
    globalsCss.includes('--primary: 253 52% 57%'),
    '1.1',
    '--primary: 253 52% 57% (HSL for #6C5ECF)'
  );

  test(
    'Sidebar background token (#12121F)',
    globalsCss.includes('--sidebar: 240 22% 11%'),
    '1.4, 16.4',
    '--sidebar: 240 22% 11% (HSL for #12121F)'
  );

  test(
    'Positive color (#22C55E)',
    globalsCss.includes('--positive: 142 71% 45%'),
    '1.5',
    '--positive: 142 71% 45% (HSL for #22C55E)'
  );

  test(
    'Negative color (#EF4444)',
    globalsCss.includes('--negative: 0 84% 60%'),
    '1.5',
    '--negative: 0 84% 60% (HSL for #EF4444)'
  );
}

// Test 4: Card Surface Class
if (globalsCss) {
  test(
    'Card surface class exists',
    globalsCss.includes('.card-surface'),
    '3.7, 15.2',
    '.card-surface class defined'
  );

  test(
    'Card surface light mode styling',
    globalsCss.match(/\.card-surface[\s\S]*box-shadow: 0 1px 3px/),
    '3.3, 3.4',
    'Light mode: box-shadow and border'
  );

  test(
    'Card surface dark mode styling',
    globalsCss.match(/\.dark \.card-surface[\s\S]*box-shadow: none/),
    '3.5, 3.6',
    'Dark mode: no shadow, faint white border'
  );
}

// Test 5: Typography Classes
if (globalsCss) {
  test(
    'Typography scale classes exist',
    globalsCss.includes('.text-page-title') &&
    globalsCss.includes('.text-card-title') &&
    globalsCss.includes('.text-body-sm') &&
    globalsCss.includes('.text-label-xs'),
    '2.1, 2.2, 2.3, 2.4, 15.5',
    'All 4 typography classes defined'
  );

  test(
    'Page title typography (22px, 500 weight)',
    globalsCss.match(/\.text-page-title[\s\S]*font-size: 22px[\s\S]*font-weight: 500/),
    '2.1',
    'font-size: 22px; font-weight: 500'
  );

  test(
    'Card title typography (15px, 500 weight)',
    globalsCss.match(/\.text-card-title[\s\S]*font-size: 15px[\s\S]*font-weight: 500/),
    '2.2',
    'font-size: 15px; font-weight: 500'
  );
}

// Test 6: Sidebar Component
const sidebarContent = readFile('components/ui/sidebar.tsx');
if (sidebarContent) {
  test(
    'Sidebar uses fixed #12121F background',
    sidebarContent.includes('#12121F'),
    '6.1, 16.4',
    'Sidebar background: #12121F (theme-independent)'
  );

  test(
    'Sidebar has right border',
    sidebarContent.includes('rgba(255,255,255,0.07)') || sidebarContent.includes('rgba(255, 255, 255, 0.07)'),
    '6.2',
    'borderRight: 1px solid rgba(255,255,255,0.07)'
  );

  test(
    'Sidebar active state uses #6C5ECF',
    sidebarContent.includes('#6C5ECF'),
    '6.3, 6.4, 6.5',
    'Active nav items use #6C5ECF accent'
  );

  test(
    'Sidebar integrates ThemeToggle',
    sidebarContent.includes('ThemeToggle'),
    '17.1',
    'ThemeToggle component imported and used'
  );
}

// Test 7: Table Rows Class
if (globalsCss) {
  test(
    'Table rows class exists',
    globalsCss.includes('.table-rows'),
    '7.6, 15.3',
    '.table-rows class defined'
  );

  test(
    'Table rows border styling',
    globalsCss.match(/\.table-rows tbody tr[\s\S]*border-bottom/),
    '7.1, 7.3',
    'Row divider borders between tbody rows'
  );

  test(
    'Table last row no border',
    globalsCss.match(/\.table-rows tbody tr:last-child[\s\S]*border-bottom: none/),
    '7.4',
    'Last row has no border'
  );

  test(
    'Table hover state',
    globalsCss.match(/\.table-rows tbody tr:hover[\s\S]*background/),
    '7.5',
    'Hover state with background color'
  );
}

// Test 8: KPI Icon Circle Class
if (globalsCss) {
  test(
    'KPI icon circle class exists',
    globalsCss.includes('.kpi-icon-circle'),
    '15.4',
    '.kpi-icon-circle class defined'
  );

  test(
    'KPI icon circle size (44px)',
    globalsCss.match(/\.kpi-icon-circle[\s\S]*width: 44px[\s\S]*height: 44px/),
    '4.1',
    'width: 44px; height: 44px'
  );
}

// Test 9: Tailwind Configuration
const tailwindConfig = readFile('tailwind.config.ts');
if (tailwindConfig) {
  test(
    'Tailwind extends colors',
    tailwindConfig.includes('colors:') && tailwindConfig.includes('primary'),
    '1.6',
    'Custom colors extended in Tailwind config'
  );

  test(
    'Tailwind extends fontSize',
    tailwindConfig.includes('fontSize:'),
    '2.6',
    'Custom fontSize extended in Tailwind config'
  );
}

// Summary
log('\n=== Test Summary ===\n', 'cyan');
log(`Total Tests: ${results.total}`, 'blue');
log(`Passed: ${results.passed}`, 'green');
log(`Failed: ${results.failed}`, results.failed > 0 ? 'red' : 'green');

const passRate = ((results.passed / results.total) * 100).toFixed(1);
log(`\nPass Rate: ${passRate}%`, passRate === '100.0' ? 'green' : 'yellow');

if (results.failed === 0) {
  log('\n✓ All theme system tests passed!', 'green');
  log('Theme system is correctly implemented and ready for use.\n', 'cyan');
  process.exit(0);
} else {
  log(`\n✗ ${results.failed} test(s) failed.`, 'red');
  log('Please review the failed tests and fix the issues.\n', 'yellow');
  process.exit(1);
}
