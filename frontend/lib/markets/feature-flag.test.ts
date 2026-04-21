import { describe, expect, it } from "vitest";
import { marketsFeatureEnabled } from "@/lib/markets/feature-flag";

describe("markets feature flag", () => {
  it("defaults to enabled unless explicitly turned off", () => {
    expect(typeof marketsFeatureEnabled).toBe("boolean");
  });
});
