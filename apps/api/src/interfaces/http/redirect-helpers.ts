export function isRedirectAllowed(target: string, allowlist: readonly string[]): boolean {
  // Rejeitar esquemas perigosos e URLs sem protocolo explícito
  if (/^(javascript|data|vbscript):/i.test(target) || target.startsWith("//")) {
    return false;
  }
  if (target.startsWith("/")) {
    return allowlist.some((allowed) => target === allowed || target.startsWith(`${allowed}/`));
  }
  try {
    const url = new URL(target);
    // Só permitir http/https; rejeitar outros protocolos
    if (url.protocol !== "http:" && url.protocol !== "https:") {
      return false;
    }
    return allowlist.includes(url.pathname) || allowlist.some((allowed) => url.pathname.startsWith(`${allowed}/`));
  } catch {
    return false;
  }
}
