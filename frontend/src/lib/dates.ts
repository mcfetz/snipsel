export function toLocalIsoDay(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export function offsetDate(dateStr: string, days: number): string {
  const d = new Date(dateStr + 'T12:00:00'); // noon to avoid DST issues
  d.setDate(d.getDate() + days);
  return toLocalIsoDay(d);
}

export function isFutureDate(dateStr: string): boolean {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const d = new Date(dateStr + 'T00:00:00');
  return d.getTime() > today.getTime();
}

export function isExpired(dateStr: string): boolean {
  return new Date(dateStr).getTime() < Date.now();
}

export function daysFromNow(dateStr: string): string {
  const d = new Date(dateStr);
  const now = new Date();
  const diffDays = Math.round(
    (new Date(dateStr).setHours(0, 0, 0, 0) - new Date().setHours(0, 0, 0, 0)) / 86400000
  );

  if (diffDays === 0) {
    const diffMs = d.getTime() - now.getTime();
    if (diffMs > 0) {
      const hours = Math.floor(diffMs / 3600000);
      const minutes = Math.floor((diffMs % 3600000) / 60000);
      if (hours > 0) {
        return `fällig in ${hours}h ${minutes}m`;
      }
      return `fällig in ${minutes}m`;
    }
    return 'heute fällig';
  }
  if (diffDays > 0) return `in ${diffDays}d`;
  return `${-diffDays}d ago`;
}

export function formatModifiedAt(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const yesterdayStart = todayStart - 86400000;
  const itemDate = new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();

  const timeStr = d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });

  if (itemDate === todayStart) {
    return timeStr;
  }
  if (itemDate === yesterdayStart) {
    return `Yesterday, ${timeStr}`;
  }
  return d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

export function getDailyCollectionDayLabel(listForDay: string | null | undefined): string | null {
  if (!listForDay) return null;
  const todayStr = toLocalIsoDay(new Date());
  const yesterdayDate = new Date();
  yesterdayDate.setDate(yesterdayDate.getDate() - 1);
  const yesterdayStr = toLocalIsoDay(yesterdayDate);

  if (listForDay === todayStr) return 'today';
  if (listForDay === yesterdayStr) return 'yesterday';

  const weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const date = new Date(listForDay + 'T12:00:00');
  return weekdays[date.getDay()];
}
