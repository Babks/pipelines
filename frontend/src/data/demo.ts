import type { Defect, SingleCorrosion } from "../types/defect";

// Единственный источник проектов/участков: вручную заданный справочник, НЕ сервер и НЕ Excel.
export const projects = [
  {
    id: "north",
    name: "Северный газопровод",
    sections: [
      { id: "s1", name: "Участок 01 · км 120–145" },
      { id: "s2", name: "Участок 02 · км 145–170" },
    ],
  },
  {
    id: "east",
    name: "Восточный газопровод",
    sections: [
      { id: "s3", name: "Участок 01 · км 0–25" },
      { id: "empty", name: "Участок 02 · нет демоданных" },
    ],
  },
];
// Фабрика синтетической записи. Все константы ниже подобраны для разнообразия интерфейса, не взяты из измерений или СТО.
const base = (index: number, sectionId = "s1") => ({
  // index начинается с 0; +1 даёт человеческую нумерацию, padStart(4,'0') создаёт DEMO-0001. Технический ID не является номером из реальной БД.
  id: `DEMO-${String(index + 1).padStart(4, "0")}`,
  projectId: sectionId === "s3" ? "east" : "north",
  sectionId,
  // % — остаток от деления: циклически повторяем пять труб и три часовые позиции. Координата — арифметическая последовательность для демонстрации сортировки.
  pipeNumber: String(1362 + (index % 5)),
  positionM: 120025.4 + index * 12.3,
  clockPosition: ["03:20", "06:10", "09:45"][index % 3],
  // Генерируем примерные размеры. toFixed возвращает строку; Number возвращает её к числу. Эти операции не являются инженерными формулами.
  lengthMm: 35 + index * 7,
  widthMm: 22 + index * 3,
  depthMm: Number((1.2 + (index % 5) * 0.4).toFixed(1)),
  // Одинаковые для примеров параметры трубы; суффиксы Mm/Mpa фиксируют единицы. Достоверность и применимость НЕ проверялись.
  pipe: {
    diameterMm: 1020,
    wallMm: 12,
    tensileMpa: 510,
    workingPressureMpa: 5.4,
  },
  // as const сохраняет литеральный тип true / A / B / C. Категория циклическая, независимо от глубины и давления: это намеренно не категорирование.
  isDemo: true as const,
  demoCategory: (["A", "B", "C"] as const)[index % 3],
  // null означает отсутствие результата, не нулевое давление. Подтверждённой категории нет даже при наличии demoCategory.
  result: {
    status: "not_connected" as const,
    pressureMpa: null,
    finalCategory: null,
  },
});
// Synthetic fixtures only. No field below is a result of an engineering algorithm.
// Создаём 30 объектов один раз при загрузке модуля. Подчёркивание — неиспользуемый аргумент; i — индекс. Генерация детерминированная, без Math.random.
export const demoDefects: Defect[] = Array.from(
  { length: 30 },
  (_, i): Defect => {
    // 24 объекта идут в s1, следующие 4 в s2, последние 2 в s3; empty не получает записей. Координаты остаются условными и не согласованы с километражом названий участков.
    const common = base(i, i < 24 ? "s1" : i < 28 ? "s2" : "s3");
    // Каждый второй объект в шестёрке — группа. Это правило демонабора, а не проверка взаимодействия.
    if (i % 6 === 1) {
      // Три участника наследуют common; поля справа от ...common заменяют одноимённые поля. Принадлежность группе задана вручную.
      const members: SingleCorrosion[] = [0, 1, 2].map((j) => ({
        ...common,
        id: `${common.id}-${j + 1}`,
        kind: "single",
        corrosionMode: "external",
        positionM: common.positionM + j * 0.08,
        lengthMm: 40 + j * 10,
        widthMm: 25 + j * 5,
        depthMm: 1.2 + j * 0.2,
      }));
      // Общий контур задан константами; effectiveGeometry и criticalCombination отсутствуют, поскольку геометрический алгоритм и перебор не выполнены.
      return {
        ...common,
        kind: "group",
        corrosionMode: "external",
        lengthMm: 220,
        widthMm: 90,
        depthMm: 1.6,
        members,
        effectiveGeometry: null,
        criticalCombination: null,
      };
    }
    // Последние три объекта каждой шестёрки — вмятины; индексы 0/1/2 выбирают РМ1/РМ2/РМ3.
    if (i % 6 >= 3) {
      const model = (["РМ1", "РМ2", "РМ3"] as const)[(i % 6) - 3];
      // Для РМ3 перезаписываем result и обнуляем demoCategory. Предварительная B находится в отдельном поле и не попадает в фильтр окончательных демокатегорий.
      return {
        ...common,
        kind: "dent",
        model,
        ...(model === "РМ3"
          ? {
              demoCategory: null,
              result: {
                status: "awaiting_rm2",
                pressureMpa: null,
                finalCategory: null,
                preliminaryDemoCategory: "B",
              },
            }
          : {}),
      };
    }
    // Оставшиеся объекты — одиночная коррозия. i===2 специально создаёт отсутствующую глубину для проверки интерфейса ошибки.
    return {
      ...common,
      kind: "single",
      corrosionMode: i % 4 === 2 ? "internal" : "external",
      ...(i === 2
        ? {
            depthMm: null,
            demoCategory: null,
            result: {
              status: "missing_data",
              pressureMpa: null,
              finalCategory: null,
              missingFields: ["Глубина дефекта"],
            },
          }
        : {}),
    };
  },
);
