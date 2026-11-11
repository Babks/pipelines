/**
 * Карточка вмятины: размеры и модель приходят из демозаписи. map создаёт блоки для четырёх исходных величин. as number|null — подсказка компилятору для смешанного массива, не преобразование значения. Модели показаны span, а не кнопками: переключение расчётной модели не реализовано.
 */
import { Alert, Descriptions, Tag } from "antd";
import type { Dent } from "../../types/defect";
import { CardData } from "./CardData";
import { number } from "../../utils/format";
export function DentData({ defect }: { defect: Dent }) {
  return (
    <>
      <div className="model-line">
        Выбранная модель <Tag color="blue">{defect.model}</Tag>
        <span className="muted">Задана в демопримере</span>
      </div>
      <CardData defect={defect} />
    </>
  );
}
export function DentCalculation({ defect }: { defect: Dent }) {
  return (
    <div className="card-section">
      <h3>Расчёт вмятины</h3>
      <p className="muted">Исходные параметры · демоданные</p>
      <div className="parameter-grid">
        {[
          ["Длина вмятины", defect.lengthMm],
          ["Ширина / короткая сторона", defect.widthMm],
          ["Глубина", defect.depthMm],
          ["Диаметр трубы", defect.pipe.diameterMm],
        ].map(([label, value]) => (
          <div className="parameter-cell" key={String(label)}>
            <span>{label}</span>
            <strong>{number(value as number | null)} мм</strong>
          </div>
        ))}
      </div>
      <h3>Расчётная модель</h3>
      <div className="model-options" aria-label="Модель из демозаписи">
        {["РМ1", "РМ2", "РМ3"].map((model) => (
          <span key={model} className={model === defect.model ? "active" : ""}>
            {model}
          </span>
        ))}
      </div>
      <p className="muted">
        Модель задана в демозаписи; автоматический выбор не подключён.
      </p>
      <Alert
        type={defect.model === "РМ3" ? "warning" : "info"}
        showIcon
        title={
          defect.model === "РМ3"
            ? "Ожидает дополнительного расчёта РМ2"
            : "Расчёт не подключён"
        }
        description="Нормативные формулы и правила выбора модели будут подключены в следующем этапе."
      />
      <Descriptions
        bordered
        column={1}
        size="small"
        items={[
          {
            key: "strain",
            label: "Расчётные показатели",
            children: "Не определены",
          },
          {
            key: "pressure",
            label: "Разрушающее давление",
            children: "Расчёт не подключён",
          },
          {
            key: "method",
            label: "Нормативная методика",
            children: "Требуется утверждённый источник для РМ1 / РМ2 / РМ3",
          },
        ]}
      />
    </div>
  );
}
