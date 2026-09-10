/**
 * Phone validation for the public Renta Natural landing page
 * (b2c-social-lead-capture, Task 4). Pure function, no dependencies — kept
 * separate from the form component so it stays trivially testable if/when
 * this repo adopts a frontend test runner (none exists today, see
 * progress/impl_b2c_social_task4.md).
 *
 * Deliberately permissive: the backend (`_normalize_whatsapp_phone`,
 * apps/backend/services/crm_service.py) is the real source of truth for what
 * counts as a usable WhatsApp number. This only gates when the partial-capture
 * fetch fires, so it must never be stricter than the backend accepts — a
 * false negative here would silently drop a real lead who has a valid but
 * unusually formatted number.
 */

/**
 * Returns true once the input has at least 10 digits (ignoring spaces,
 * dashes, parentheses, and a leading "+"), the minimum needed for a
 * Colombian mobile number in either local (10-digit) or E.164 (+57...) form.
 */
export function isValidCapturePhone(rawPhone: string): boolean {
  const digitsOnly = rawPhone.replace(/[^0-9]/g, "");
  return digitsOnly.length >= 10;
}
