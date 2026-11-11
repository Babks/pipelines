import type { Defect, DefectFilters, DefectTab } from "../types/defect";
// Отсутствующие optional-поля равны undefined и означают «не ограничивать». Пустой query означает отсутствие поиска.
export const emptyFilters: DefectFilters = { query: "" };
// Чистая функция: получает массив и условия, возвращает новый массив. Нет сети, state, изменения исходных записей или инженерных вычислений.
export function filterDefects(
  defects: Defect[],
  tab: DefectTab,
  filters: DefectFilters,
): Defect[] {
  // Удаляем пробелы с краёв и приводим запрос к нижнему регистру. Поиск — подстрока, а не строгое равенство ID.
  const q = filters.query.trim().toLocaleLowerCase("ru");
  // filter оставляет запись только при true. Все строки условий соединены &&, поэтому выбранные фильтры действуют одновременно.
  return defects.filter(
    (d) =>
      // Вкладка all пропускает любой тип; corrosion объединяет single и group; dent пропускает только вмятины.
      (tab === "all" ||
        (tab === "corrosion" ? d.kind !== "dent" : d.kind === "dent")) &&
      // Пустой запрос пропускает запись. У группы дополнительно ищем совпадение в members.some; возвращается родительская группа, а не плоский список её участников.
      (!q ||
        d.id.toLowerCase().includes(q) ||
        (d.kind === "group" &&
          d.members.some((m) => m.id.toLowerCase().includes(q)))) &&
      // Не выбранная труба не ограничивает; выбранная сравнивается по точному строковому номеру.
      (!filters.pipe || d.pipeNumber === filters.pipe) &&
      // unset означает null. Здесь используется demoCategory, НЕ result.finalCategory и НЕ preliminaryDemoCategory.
      (!filters.category ||
        (filters.category === "unset"
          ? d.demoCategory === null
          : d.demoCategory === filters.category)) &&
      // Тип расчётного объекта: single/group/dent; это уже заданный атрибут примера, не результат определения одиночности.
      (!filters.kind || d.kind === filters.kind) &&
      // Сначала исключаем вмятины; затем TypeScript разрешает обратиться к corrosionMode у коррозии.
      (!filters.corrosionMode ||
        (d.kind !== "dent" && d.corrosionMode === filters.corrosionMode)) &&
      // Модель существует только у dent. Несовместимые фильтры честно дают пустой результат.
      (!filters.model || (d.kind === "dent" && d.model === filters.model)),
  );
}
