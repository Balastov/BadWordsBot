/** Map backend auth error details to short Russian UI messages. */
export function formatAuthError(detail: unknown, fallback = 'Что-то пошло не так'): string {
  if (typeof detail !== 'string') {
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as {msg?: string};
      if (typeof first?.msg === 'string') return first.msg;
    }
    return fallback;
  }

  const known: Record<string, string> = {
    'Invalid credentials': 'Неверный email или пароль',
    'Неверный email или пароль': 'Неверный email или пароль',
    'Email or username already taken': 'Email или имя пользователя уже заняты',
    'Email или имя пользователя уже заняты': 'Email или имя пользователя уже заняты',
  };

  return known[detail] ?? detail;
}
