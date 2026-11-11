/**
 * Карточка группы: общий контур берётся из demo.ts, эффективная геометрия и критическая комбинация не определены. Перечень этапов раздела 7 — текстовая заготовка, не реализация перебора.
 */
import { Descriptions, Alert } from "antd";
import type { GroupCorrosion } from "../../types/defect";
import { CardData } from "./CardData";
import { number } from "../../utils/format";
export function GroupCorrosionData({ defect }: { defect: GroupCorrosion }) {
  return (
    <>
      <CardData defect={defect} />
      <div className="card-section">
        <h3>Общая и эффективная геометрия</h3>
        <Descriptions
          bordered
          column={1}
          size="small"
          items={[
            {
              key: "g",
              label: "Общий контур · демо",
              children: `${number(defect.lengthMm)} × ${number(defect.widthMm)} мм`,
            },
            {
              key: "e",
              label: "Эффективная геометрия",
              children: "Не определена — расчёт не подключён",
            },
            {
              key: "c",
              label: "Наиболее опасная комбинация",
              children: "Не определена — перебор не выполнен",
            },
          ]}
        />
      </div>
    </>
  );
}
export function GroupCorrosionCalculation() {
  return (
    <div className="card-section">
      <h3>Взаимодействующие дефекты · раздел 7 СТО</h3>
      <Alert
        type="info"
        showIcon
        title="Расчёт не подключён"
        description="Состав этой группы задан в демоданных, а не определён расчётом взаимодействия."
      />
      <ol className="calculation-steps">
        <li>Разбиение на перекрывающиеся части</li>
        <li>Построение линий и проецирование</li>
        <li>Объединение пересекающихся проекций</li>
        <li>Перебор непрерывных последовательностей</li>
        <li>Расчёт и выбор минимального давления</li>
      </ol>
      <div className="formula-placeholder">
        <strong>Наиболее опасная комбинация</strong>
        <span>
          Не определена. Эффективная геометрия и результат появятся после
          расчёта.
        </span>
      </div>
    </div>
  );
}
