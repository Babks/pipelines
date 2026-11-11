/**
 * Исходные значения берутся из props.defect и defect.pipe. Descriptions — готовая сетка подписей Ant Design; items описывает пары label/children. number() форматирует вид, не пересчитывает физическую величину.
 */
import { Alert, Descriptions } from "antd";
import type { Defect } from "../../types/defect";
import { number, modeLabel } from "../../utils/format";
export function CardData({ defect }: { defect: Defect }) {
  const d = defect;
  return (
    <div className="card-section">
      <h3>
        Исходные параметры <span>демоданные</span>
      </h3>
      {d.result.status === "missing_data" && (
        <Alert
          type="error"
          showIcon
          title="Недостаточно исходных данных"
          description={d.result.missingFields.join(", ")}
        />
      )}
      <Descriptions
        bordered
        column={2}
        size="small"
        items={[
          { key: "pipe", label: "№ трубы", children: d.pipeNumber },
          {
            key: "pos",
            label: "Положение, м",
            children: number(d.positionM, 2),
          },
          { key: "clock", label: "По окружности", children: d.clockPosition },
          { key: "mode", label: "Режим", children: modeLabel(d) },
          { key: "l", label: "Длина, мм", children: number(d.lengthMm) },
          { key: "w", label: "Ширина, мм", children: number(d.widthMm) },
          { key: "d", label: "Глубина, мм", children: number(d.depthMm) },
          {
            key: "D",
            label: "Диаметр, мм",
            children: number(d.pipe.diameterMm),
          },
          { key: "t", label: "Стенка, мм", children: number(d.pipe.wallMm) },
          {
            key: "s",
            label: "Прочность, МПа",
            children: number(d.pipe.tensileMpa),
          },
          {
            key: "p",
            label: "Рабочее давление, МПа",
            children: number(d.pipe.workingPressureMpa),
            span: 2,
          },
        ]}
      />
      <p className="muted">
        Источник: встроенный демонстрационный набор. Значения не получены из
        выбранного Excel-файла.
      </p>
    </div>
  );
}
