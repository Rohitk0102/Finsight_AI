export function parseBold(text: string) {
  // Use dangerouslySetInnerHTML or React string replacement for **text**
  // For safety in React, we'll return a string but replace markdown bold with <strong> tags
  return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

export function formatNumber(n: number | undefined | null): string {
  if (n === undefined || n === null) return "N/A";
  
  const absN = Math.abs(n);
  const sign = n < 0 ? "-" : "";
  
  if (absN >= 1_000_000_000_000) {
    return `${sign}${(absN / 1_000_000_000_000).toFixed(2)}T`;
  } else if (absN >= 1_000_000_000) {
    return `${sign}${(absN / 1_000_000_000).toFixed(2)}B`;
  } else if (absN >= 1_000_000) {
    return `${sign}${(absN / 1_000_000).toFixed(2)}M`;
  } else if (absN >= 1_000) {
    return `${sign}${(absN / 1_000).toFixed(2)}K`;
  } else {
    return `${sign}${absN.toFixed(2)}`;
  }
}

export function formatPrice(n: number | undefined | null): string {
  if (n === undefined || n === null) return "N/A";
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(n);
}

export function formatPercent(n: number | undefined | null): string {
  if (n === undefined || n === null) return "N/A";
  return (n > 0 ? "▲" : n < 0 ? "▼" : "") + Math.abs(n).toFixed(2) + "%";
}
