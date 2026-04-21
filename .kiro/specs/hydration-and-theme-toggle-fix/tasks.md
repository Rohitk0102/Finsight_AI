# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Hydration Consistency Test
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the hydration mismatch exists
  - **Scoped PBT Approach**: Scope the property to the concrete failing case - ThemeToggle component rendering with localStorage access during initial render
  - Test that ThemeToggle produces identical HTML on server and client during initial render (from Bug Condition in design)
  - The test assertions should match the Expected Behavior Properties from design (consistent server/client HTML)
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the hydration bug exists)
  - Document counterexamples found (e.g., "Server renders default icon, client renders different icon based on localStorage")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.4_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Theme Functionality Preservation
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for theme switching after component has mounted
  - Observe: clicking toggle switches between light and dark themes correctly
  - Observe: theme preference persists in localStorage across interactions
  - Observe: CSS dark mode styles apply correctly when theme changes
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.3, 3.4_

- [x] 3. Fix ThemeToggle component and add to landing page

  - [x] 3.1 Implement the fix in ThemeToggle component
    - Add mounted state: `const [mounted, setMounted] = useState(false);`
    - Set mounted to true in useEffect after component mounts
    - Defer all localStorage access to useEffect (remove from useState initialization)
    - Initialize theme state with safe default: `const [theme, setTheme] = useState<"light" | "dark">("dark");`
    - Add early return for SSR/hydration: `if (!mounted) return <div className="w-9 h-9" />;`
    - Move document.documentElement.classList manipulation to useEffect only
    - Ensure toggleTheme function remains unchanged for post-mount interactions
    - _Bug_Condition: isBugCondition(input) where input.isServerSideRender = true AND input.component = "ThemeToggle" AND input.accessesLocalStorage = true_
    - _Expected_Behavior: ThemeToggle produces identical HTML on server and client during initial render, with no hydration errors_
    - _Preservation: Theme switching, localStorage persistence, CSS application, and cross-page consistency must remain unchanged_
    - _Requirements: 2.1, 2.2, 2.4, 3.1, 3.2_

  - [x] 3.2 Add ThemeToggle to landing page navigation
    - Import ThemeToggle: `import { ThemeToggle } from "@/components/ui/theme-toggle";`
    - Add ThemeToggle component in navigation bar between "Sign In" link and "Get Started" button
    - Ensure it's visible on both mobile and desktop viewports
    - Apply appropriate styling to match navigation design
    - _Requirements: 2.3_

  - [x] 3.3 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Hydration Consistency Verification
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms hydration bug is fixed)
    - _Requirements: 2.1, 2.2, 2.4_

  - [x] 3.4 Verify preservation tests still pass
    - **Property 2: Preservation** - Theme Functionality Verification
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (theme switching, localStorage persistence, CSS application work correctly)
    - _Requirements: 2.5, 2.6, 3.1, 3.3, 3.4_

- [x] 4. Checkpoint - Ensure all tests pass
  - Verify no hydration errors appear in browser console
  - Verify ThemeToggle is visible on landing page
  - Verify theme switching works correctly on landing page
  - Verify theme preference persists across page navigations
  - Ask the user if questions arise
