/**
 * Управляемая форма: value приходит из App. set<K extends keyof Filters> связывает ключ поля с типом его значения. Spread сохраняет остальные фильтры, computed key [key] заменяет один. allowClear даёт undefined. options задают пары техническое value / видимый label; список труб строится из выбранного участка.
 */
import { Button, Input, Select } from "antd";
import { SearchOutlined, UndoOutlined } from "@ant-design/icons";
import type { DefectFilters as Filters } from "../types/defect";
const options = (values: string[]) =>
  values.map((value) => ({ value, label: value }));
export function DefectFilters({
  value,
  pipes,
  onChange,
  onReset,
}: {
  value: Filters;
  pipes: string[];
  onChange: (value: Filters) => void;
  onReset: () => void;
}) {
  const set = <K extends keyof Filters>(key: K, next: Filters[K]) =>
    onChange({ ...value, [key]: next });
  return (
    <div className="filters" aria-label="Фильтры реестра">
      <label className="filter-search">
        Поиск по ID
        <Input
          aria-label="Поиск по ID"
          prefix={<SearchOutlined />}
          placeholder="Например, DEMO-0001"
          value={value.query}
          allowClear
          onChange={(e) => set("query", e.target.value)}
        />
      </label>
      <label>
        Труба
        <Select
          aria-label="Труба"
          placeholder="Все трубы"
          allowClear
          value={value.pipe}
          options={options(pipes)}
          onChange={(v) => set("pipe", v)}
        />
      </label>
      <label>
        Категория · демо
        <Select
          aria-label="Категория"
          placeholder="Все категории"
          allowClear
          value={value.category}
          options={[
            ...options(["A", "B", "C"]).map((o) => ({
              ...o,
              label: `${o.label} · демо`,
            })),
            { value: "unset", label: "Не определена" },
          ]}
          onChange={(v) => set("category", v)}
        />
      </label>
      <label>
        Тип расчёта
        <Select
          aria-label="Тип расчёта"
          placeholder="Все типы"
          allowClear
          value={value.kind}
          options={[
            { value: "single", label: "Одиночная коррозия" },
            { value: "group", label: "Групповая коррозия" },
            { value: "dent", label: "Вмятина" },
          ]}
          onChange={(v) => set("kind", v)}
        />
      </label>
      <label>
        Режим коррозии
        <Select
          aria-label="Режим коррозии"
          placeholder="Все режимы"
          allowClear
          value={value.corrosionMode}
          options={[
            { value: "external", label: "Наружная" },
            { value: "internal", label: "Внутренняя" },
          ]}
          onChange={(v) => set("corrosionMode", v)}
        />
      </label>
      <label>
        Модель вмятины
        <Select
          aria-label="Модель вмятины"
          placeholder="Все модели"
          allowClear
          value={value.model}
          options={options(["РМ1", "РМ2", "РМ3"])}
          onChange={(v) => set("model", v)}
        />
      </label>
      <Button
        className="reset-filters"
        aria-label="Сбросить"
        icon={<UndoOutlined aria-hidden />}
        onClick={onReset}
      >
        Сбросить
      </Button>
    </div>
  );
}
