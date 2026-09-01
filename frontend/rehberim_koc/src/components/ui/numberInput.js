/* NumberInput'un saf mantığı — bileşenden ayrı tutuluyor ki sınanabilsin. */

export const digitsOnly = (raw) => String(raw ?? '').replace(/[^0-9]/g, '');

export const inRange = (n, min, max) =>
  Number.isFinite(n)
  && (min === undefined || n >= min)
  && (max === undefined || n <= max);

/**
 * Bir tuş vuruşundan sonraki durum: kutuda ne yazacak ve dışarı hangi sayı verilecek.
 *
 * `text` her zaman kullanıcının yazdığı ham rakamlardır — bu yüzden alan
 * boşaltılabilir ve "120" yazarken araya sıfır karışmaz. `commit` yalnız değer
 * sınırların içindeyse doludur; değilse dışarıdaki değer olduğu gibi kalır ve
 * odak çıkınca metin ona geri döner.
 */
export function nextNumberState(raw, min, max) {
  const text = digitsOnly(raw);
  if (text === '') return { text, commit: null };
  const n = Number(text);
  return { text, commit: inRange(n, min, max) ? n : null };
}
