/**
 * Joins class names conditionally
 * Example: cn("btn", isActive && "btn-active") → "btn btn-active"
 */
export function cn(...classes: (string | false | null | undefined)[]) {
    return classes.filter(Boolean).join(" ");
  }
  