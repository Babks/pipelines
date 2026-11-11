/**
 * Только отображение: number(null) возвращает «Нет данных»; toLocaleString форматирует число по ru-RU с ограничением дробных знаков. Исходное число не меняется. kindLabel/modeLabel переводят технические значения в подписи.
 */
import type { Defect } from "../types/defect";
export const number = (value: number | null, digits = 1) =>
  value === null
    ? "Нет данных"
    : value.toLocaleString("ru-RU", { maximumFractionDigits: digits });
export const kindLabel = (d: Defect) =>
  ({
    single: "Одиночная коррозия",
    group: "Групповая коррозия",
    dent: "Вмятина",
  })[d.kind];
export const modeLabel = (d: Defect) =>
  d.kind === "dent"
    ? "—"
    : d.corrosionMode === "external"
      ? "Наружная"
      : "Внутренняя";
