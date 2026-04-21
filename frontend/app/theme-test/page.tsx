"use client";

import { useEffect, useState } from "react";
import { Moon, Sun, CheckCircle2, XCircle, AlertCircle } from "lucide-react";

type TestResult = {
  name: string;
  status: "pass" | "fail" | "pending";
  message: string;
  requirement: string;
};

export default function ThemeTestPage() {
  const [results, setResults] = useState<TestResult[]>([]);
  const [currentTheme, setCurrentTheme] = useState<"light" | "dark">("dark");

  useEffect(() => {
    // Read current theme
    const theme = document.documentElement.classList.contains("dark") ? "dark" : "light";
    setCurrentTheme(theme);
    
    // Run tests
    runTests();
  }, []);

  const runTests = () => {
    const testResults: TestResult[] = [];

    // Test 1: Theme toggle functionality
    testResults.push({
      name: "Theme Toggle Exists",
      status: localStorage.getItem("theme") !== null ? "pass" : "fail",
      message: localStorage.getItem("theme") !== null 
        ? `Theme preference found: ${localStorage.getItem("theme")}`
        : "No theme preference in localStorage",
      requirement: "16.6, 17.5"
    });

    // Test 2: CSS Custom Properties - Light Mode
    const rootStyles = getComputedStyle(document.documentElement);
    const bgLight = rootStyles.getPropertyValue("--background").trim();
    testResults.push({
      name: "Light Mode Background Token",
      status: bgLight === "230 100% 99%" ? "pass" : "fail",
      message: `--background: ${bgLight} (expected: 230 100% 99%)`,
      requirement: "1.2"
    });

    // Test 3: CSS Custom Properties - Primary Color
    const primary = rootStyles.getPropertyValue("--primary").trim();
    testResults.push({
      name: "Primary Purple Token",
      status: primary === "253 52% 57%" ? "pass" : "fail",
      message: `--primary: ${primary} (expected: 253 52% 57% for #6C5ECF)`,
      requirement: "1.1"
    });

    // Test 4: CSS Custom Properties - Positive/Negative
    const positive = rootStyles.getPropertyValue("--positive").trim();
    const negative = rootStyles.getPropertyValue("--negative").trim();
    testResults.push({
      name: "Semantic Colors (Positive/Negative)",
      status: positive === "142 71% 45%" && negative === "0 84% 60%" ? "pass" : "fail",
      message: `--positive: ${positive}, --negative: ${negative}`,
      requirement: "1.5"
    });

    // Test 5: Sidebar Background
    const sidebar = document.querySelector('aside[style*="#12121F"]');
    testResults.push({
      name: "Sidebar Fixed Background",
      status: sidebar ? "pass" : "fail",
      message: sidebar 
        ? "Sidebar has #12121F background (theme-independent)" 
        : "Sidebar background not found or incorrect",
      requirement: "1.4, 6.1, 16.4"
    });

    // Test 6: Card Surface Class
    const cardSurface = document.querySelector(".card-surface");
    testResults.push({
      name: "Card Surface Class Exists",
      status: cardSurface ? "pass" : "fail",
      message: cardSurface 
        ? "Found .card-surface elements on page" 
        : "No .card-surface elements found",
      requirement: "3.7, 15.2"
    });

    // Test 7: Typography Classes
    const typographyClasses = [
      ".text-page-title",
      ".text-card-title", 
      ".text-body-sm",
      ".text-label-xs"
    ];
    const foundTypography = typographyClasses.filter(cls => {
      const el = document.querySelector(cls);
      return el !== null;
    });
    testResults.push({
      name: "Typography Scale Classes",
      status: foundTypography.length > 0 ? "pass" : "pending",
      message: `Found ${foundTypography.length}/4 typography classes: ${foundTypography.join(", ")}`,
      requirement: "2.1, 2.2, 2.3, 2.4, 15.5"
    });

    // Test 8: Dark Mode Class
    const hasDarkClass = document.documentElement.classList.contains("dark");
    testResults.push({
      name: "Dark Mode Class Applied",
      status: hasDarkClass ? "pass" : "pending",
      message: hasDarkClass 
        ? "Root element has .dark class" 
        : "Root element does not have .dark class (light mode active)",
      requirement: "16.5"
    });

    setResults(testResults);
  };

  const toggleTheme = () => {
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    setCurrentTheme(newTheme);
    localStorage.setItem("theme", newTheme);
    document.documentElement.classList.toggle("dark", newTheme === "dark");
    
    // Re-run tests after theme change
    setTimeout(() => runTests(), 100);
  };

  const reloadPage = () => {
    window.location.reload();
  };

  const clearLocalStorage = () => {
    localStorage.removeItem("theme");
    alert("Theme preference cleared. Page will reload.");
    window.location.reload();
  };

  const passCount = results.filter(r => r.status === "pass").length;
  const failCount = results.filter(r => r.status === "fail").length;
  const pendingCount = results.filter(r => r.status === "pending").length;

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="card-surface p-6 mb-6">
          <h1 className="text-page-title mb-4">Theme System Verification Tests</h1>
          <p className="text-body-sm text-muted-foreground mb-4">
            Task 2.3: Verify theme system functionality
          </p>
          
          {/* Test Summary */}
          <div className="flex gap-4 mb-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-[#22C55E]" />
              <span className="text-body-sm font-medium">{passCount} Passed</span>
            </div>
            <div className="flex items-center gap-2">
              <XCircle className="h-5 w-5 text-[#EF4444]" />
              <span className="text-body-sm font-medium">{failCount} Failed</span>
            </div>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-[#f59e0b]" />
              <span className="text-body-sm font-medium">{pendingCount} Pending</span>
            </div>
          </div>

          {/* Current Theme */}
          <div className="flex items-center gap-4 p-4 bg-accent/30 rounded-lg">
            <div className="flex items-center gap-2">
              {currentTheme === "dark" ? (
                <Moon className="h-5 w-5" />
              ) : (
                <Sun className="h-5 w-5" />
              )}
              <span className="text-body-sm font-medium">
                Current Theme: {currentTheme.toUpperCase()}
              </span>
            </div>
            <button
              onClick={toggleTheme}
              className="px-4 py-2 rounded-lg text-body-sm font-medium transition-colors"
              style={{ background: "#6C5ECF", color: "white" }}
            >
              Toggle Theme
            </button>
            <button
              onClick={reloadPage}
              className="px-4 py-2 rounded-lg bg-accent text-body-sm font-medium hover:bg-accent/80 transition-colors"
            >
              Reload Page
            </button>
            <button
              onClick={clearLocalStorage}
              className="px-4 py-2 rounded-lg bg-destructive text-destructive-foreground text-body-sm font-medium hover:bg-destructive/80 transition-colors"
            >
              Clear Storage
            </button>
          </div>
        </div>

        {/* Test Results */}
        <div className="space-y-3">
          {results.map((result, index) => (
            <div key={index} className="card-surface p-4">
              <div className="flex items-start gap-3">
                <div className="mt-0.5">
                  {result.status === "pass" && (
                    <CheckCircle2 className="h-5 w-5 text-[#22C55E]" />
                  )}
                  {result.status === "fail" && (
                    <XCircle className="h-5 w-5 text-[#EF4444]" />
                  )}
                  {result.status === "pending" && (
                    <AlertCircle className="h-5 w-5 text-[#f59e0b]" />
                  )}
                </div>
                <div className="flex-1">
                  <h3 className="text-card-title mb-1">{result.name}</h3>
                  <p className="text-body-sm text-muted-foreground mb-2">
                    {result.message}
                  </p>
                  <p className="text-label-xs text-muted-foreground">
                    Requirements: {result.requirement}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Manual Test Instructions */}
        <div className="card-surface p-6 mt-6">
          <h2 className="text-card-title mb-4">Manual Verification Steps</h2>
          <ol className="space-y-3 text-body-sm">
            <li className="flex gap-3">
              <span className="font-medium text-[#6C5ECF]">1.</span>
              <span>
                <strong>Theme Toggle:</strong> Click &ldquo;Toggle Theme&rdquo; button above. 
                Verify the page switches between light (#F8F9FF) and dark (#0E0E1A) backgrounds.
              </span>
            </li>
            <li className="flex gap-3">
              <span className="font-medium text-[#6C5ECF]">2.</span>
              <span>
                <strong>Persistence:</strong> Toggle theme, then click &ldquo;Reload Page&rdquo;. 
                Verify the theme persists after reload.
              </span>
            </li>
            <li className="flex gap-3">
              <span className="font-medium text-[#6C5ECF]">3.</span>
              <span>
                <strong>CSS Properties:</strong> Open DevTools, inspect root element, 
                check Computed styles for --background, --card, --primary values.
              </span>
            </li>
            <li className="flex gap-3">
              <span className="font-medium text-[#6C5ECF]">4.</span>
              <span>
                <strong>Sidebar Background:</strong> Navigate to Dashboard or any page with sidebar. 
                Verify sidebar stays #12121F in both light and dark modes.
              </span>
            </li>
            <li className="flex gap-3">
              <span className="font-medium text-[#6C5ECF]">5.</span>
              <span>
                <strong>Card Styling:</strong> In light mode, cards should have subtle shadow. 
                In dark mode, cards should have no shadow and faint white border.
              </span>
            </li>
            <li className="flex gap-3">
              <span className="font-medium text-[#6C5ECF]">6.</span>
              <span>
                <strong>Default Theme:</strong> Click &ldquo;Clear Storage&rdquo; to remove preference. 
                Verify page defaults to dark mode after reload.
              </span>
            </li>
          </ol>
        </div>

        {/* CSS Custom Properties Reference */}
        <div className="card-surface p-6 mt-6">
          <h2 className="text-card-title mb-4">CSS Custom Properties Reference</h2>
          <div className="grid grid-cols-2 gap-4 text-body-sm">
            <div>
              <h3 className="font-medium mb-2">Light Mode</h3>
              <ul className="space-y-1 text-label-xs font-mono">
                <li>--background: 230 100% 99% (#F8F9FF)</li>
                <li>--card: 0 0% 100% (#FFFFFF)</li>
                <li>--primary: 253 52% 57% (#6C5ECF)</li>
                <li>--positive: 142 71% 45% (#22C55E)</li>
                <li>--negative: 0 84% 60% (#EF4444)</li>
              </ul>
            </div>
            <div>
              <h3 className="font-medium mb-2">Dark Mode</h3>
              <ul className="space-y-1 text-label-xs font-mono">
                <li>--background: 240 22% 8% (#0E0E1A)</li>
                <li>--card: 240 22% 13% (#16162A)</li>
                <li>--primary: 253 52% 57% (#6C5ECF)</li>
                <li>--positive: 142 71% 45% (#22C55E)</li>
                <li>--negative: 0 84% 60% (#EF4444)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
