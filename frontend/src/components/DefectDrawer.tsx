import { Alert, Button, Descriptions, Drawer, Tabs, Tag, Tooltip } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import type { Defect } from "../types/defect";
import { kindLabel } from "../utils/format";
import {
  SingleCorrosionData,
  SingleCorrosionCalculation,
} from "./cards/SingleCorrosionCard";
import {
  GroupCorrosionData,
  GroupCorrosionCalculation,
} from "./cards/GroupCorrosionCard";
import { DentData, DentCalculation } from "./cards/DentCard";
import { GroupMembers } from "./DefectTable";
import { CategoryBadge } from "./DefectBadges";
// Показывает отсутствие вычисленных результатов. Предварительная категория РМ3 берётся только из соответствующей ветки result.
function ResultPanel({ defect }: { defect: Defect }) {
  const pending = defect.result.status === "awaiting_rm2";
  return (
    <div className="card-section">
      <h3>Результат расчёта</h3>
      <Alert
        showIcon
        type={pending ? "warning" : "info"}
        title={
          pending
            ? "Ожидает дополнительного расчёта РМ2"
            : "Расчёт не подключён"
        }
        description="Подтверждённых расчётных результатов нет. Демокатегории нужны только для проверки интерфейса."
      />
      <Descriptions
        bordered
        column={1}
        size="small"
        items={[
          {
            key: "p",
            label: "Разрушающее давление",
            children: "Не рассчитано",
          },
          { key: "k", label: "Коэффициент запаса", children: "Не рассчитан" },
          {
            key: "category",
            label: "Окончательная категория",
            children: "Не определена",
          },
          {
            key: "demo",
            label: pending
              ? "Предварительная категория · демо"
              : "Категория для интерфейса · демо",
            children:
              defect.result.status === "awaiting_rm2" ? (
                <Tag color="orange">
                  {defect.result.preliminaryDemoCategory} · демо · не
                  окончательная
                </Tag>
              ) : (
                <CategoryBadge defect={defect} />
              ),
          },
        ]}
      />
      {defect.kind === "group" && (
        <p>Наиболее опасная комбинация: не определена.</p>
      )}
    </div>
  );
}
// Общая оболочка карточек: вход — выбранная запись и флаг open; выход — JSX. Закрытие вызывает callback App, не сбрасывая фильтры.
export function DefectDrawer({
  defect,
  open,
  onClose,
  onSelect,
}: {
  defect: Defect | null;
  open: boolean;
  onClose: () => void;
  onSelect: (d: Defect) => void;
}) {
  // Защита от отсутствия выбранной записи; null для React означает «ничего не отрисовывать».
  if (!defect) return null;
  // kind выбирает отдельный компонент данных. Это сужение discriminated union — тип позволяет передать подходящий вариант дефекта.
  const data =
    defect.kind === "group" ? (
      <GroupCorrosionData defect={defect} />
    ) : defect.kind === "dent" ? (
      <DentData defect={defect} />
    ) : (
      <SingleCorrosionData defect={defect} />
    );
  // Выбираем объяснение будущего расчёта, а не вызываем расчётный алгоритм.
  const calculation =
    defect.kind === "group" ? (
      <GroupCorrosionCalculation />
    ) : defect.kind === "dent" ? (
      <DentCalculation defect={defect} />
    ) : (
      <SingleCorrosionCalculation />
    );
  // mask=false оставляет реестр без затемнения; top=72 соответствует шапке; 692 — ширина из макета. disabled у пересчёта запрещает действие, Tooltip объясняет причину.
  return (
    <Drawer
      rootClassName="defect-drawer"
      mask={false}
      styles={{ wrapper: { top: 72 } }}
      open={open}
      onClose={onClose}
      size={692}
      title={
        <div className="drawer-title">
          <small>{kindLabel(defect)}</small>
          <strong>{defect.id}</strong>
        </div>
      }
      extra={<Tag color="blue">Демоданные</Tag>}
      footer={
        <div className="drawer-footer">
          <Button onClick={onClose}>Вернуться в реестр</Button>
          <Tooltip title="Расчётный модуль ещё не подключён">
            <span>
              <Button disabled icon={<ReloadOutlined />}>
                Пересчитать
              </Button>
            </span>
          </Tooltip>
          <span className="muted">Расчёт не подключён</span>
        </div>
      }
    >
      <div className="drawer-notice">
        Все числовые исходные параметры в карточке — демоданные.
      </div>
      <Tabs
        key={defect.id}
        defaultActiveKey="data"
        items={[
          { key: "data", label: "Данные", children: data },
          ...(defect.kind === "group"
            ? [
                {
                  key: "members",
                  label: "Состав группы",
                  children: <GroupMembers group={defect} onSelect={onSelect} />,
                },
              ]
            : []),
          { key: "calculation", label: "Расчёт", children: calculation },
          {
            key: "result",
            label: "Результат",
            children: <ResultPanel defect={defect} />,
          },
        ]}
      />
    </Drawer>
  );
}
