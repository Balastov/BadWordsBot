import { describe, expect, it } from "vitest";
import { formatAuthError } from "./authErrors";

describe("formatAuthError", () => {
  it("maps legacy English invalid credentials", () => {
    expect(formatAuthError("Invalid credentials")).toBe("Неверный email или пароль");
  });

  it("keeps Russian backend messages", () => {
    expect(formatAuthError("Неверный email или пароль")).toBe("Неверный email или пароль");
  });

  it("falls back for unknown values", () => {
    expect(formatAuthError(undefined)).toBe("Что-то пошло не так");
  });
});
