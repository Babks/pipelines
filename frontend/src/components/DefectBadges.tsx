/**
 * Визуальные индикаторы: цвет выбирается из уже заданного статуса/демокатегории. Никаких порогов глубины или давления здесь нет. РМ3 имеет приоритет и показывает «Не определена».
 */
import { Tag, Tooltip } from "antd";
import type { Defect } from "../types/defect";
export function CategoryBadge({ defect }: { defect: Defect }) {
  if (defect.result.status === "awaiting_rm2")
    return (
      <Tooltip title="Окончательная категория не определена до расчёта РМ2">
        <Tag color="orange">Не определена</Tag>
      </Tooltip>
    );
  return defect.demoCategory ? (
    <Tag color={{ A: "red", B: "gold", C: "green" }[defect.demoCategory]}>
      {defect.demoCategory} · демо
    </Tag>
  ) : (
    <span className="muted">Не определена</span>
  );
}
export function StatusBadge({ defect }: { defect: Defect }) {
  return defect.result.status === "awaiting_rm2" ? (
    <span className="status warning">
      <i />
      Ожидает расчёта РМ2
    </span>
  ) : defect.result.status === "missing_data" ? (
    <span className="status error">
      <i />
      Нет исходных данных
    </span>
  ) : (
    <span className="status">
      <i />
      Расчёт не подключён
    </span>
  );
}
