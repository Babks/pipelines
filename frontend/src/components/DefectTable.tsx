import { Button, Empty, Table, Tag } from "antd";
import type { TableProps } from "antd";
import type { Defect, GroupCorrosion } from "../types/defect";
import { number, modeLabel } from "../utils/format";
import { CategoryBadge, StatusBadge } from "./DefectBadges";
// Вложенная таблица берёт строки прямо из group.members. Клик передаёт участника родительскому обработчику, который откроет одиночную карточку.
export function GroupMembers({
  group,
  onSelect,
}: {
  group: GroupCorrosion;
  onSelect: (d: Defect) => void;
}) {
  return (
    <div className="group-members">
      <div className="group-members-heading">
        Состав группы <strong>{group.id}</strong>
        <Tag>Демоданные</Tag>
        <span>
          {group.members.length} дефекта · принадлежность задана в примере
        </span>
      </div>
      <Table
        size="small"
        rowKey="id"
        pagination={false}
        dataSource={group.members}
        columns={[
          {
            title: "ID дефекта",
            dataIndex: "id",
            render: (_, d) => (
              <Button type="link" onClick={() => onSelect(d)}>
                {d.id}
              </Button>
            ),
          },
          {
            title: "Положение, м",
            dataIndex: "positionM",
            render: (v) => number(v, 2),
          },
          { title: "Длина, мм", dataIndex: "lengthMm" },
          { title: "Ширина, мм", dataIndex: "widthMm" },
          {
            title: "Глубина, мм",
            dataIndex: "depthMm",
            render: (v) => number(v),
          },
        ]}
      />
    </div>
  );
}
// Таблица получает УЖЕ отфильтрованные данные. Поиск выполняется в App; сортировка и разбиение на страницы выполняются компонентом Table библиотеки Ant Design.
export function DefectTable({
  defects,
  selectedId,
  onSelect,
  page,
  pageSize,
  onPageChange,
  onReset,
}: {
  defects: Defect[];
  selectedId?: string;
  onSelect: (d: Defect) => void;
  page: number;
  pageSize: number;
  onPageChange: (page: number, size: number) => void;
  onReset: () => void;
}) {
  // Фабрика числового столбца. dataIndex — имя поля записи. sorter возвращает разность; null для сравнения заменяется на -1 (по возрастанию будет первым). В данных null не изменяется.
  const numeric = (
    key: "lengthMm" | "widthMm" | "depthMm" | "positionM",
    title: string,
    width: number,
  ): NonNullable<TableProps<Defect>["columns"]>[number] => ({
    title,
    dataIndex: key,
    width,
    align: "right",
    sorter: (a, b) => (a[key] ?? -1) - (b[key] ?? -1),
    render: (v) =>
      v === null ? (
        <span className="muted">Нет данных</span>
      ) : (
        number(v, key === "positionM" ? 2 : 1)
      ),
  });
  // Декларативная схема столбцов: title — заголовок; width — CSS-пиксели; render(value,record) — оформление ячейки. _ означает неиспользуемое значение ячейки.
  const columns: TableProps<Defect>["columns"] = [
    // stopPropagation предотвращает второй вызов выбора от всплытия клика с кнопки на строку. localeCompare сравнивает строковые ID.
    {
      title: "ID",
      dataIndex: "id",
      width: 140,
      sorter: (a, b) => a.id.localeCompare(b.id),
      render: (_, d) => (
        <Button
          className="id-button"
          type="link"
          onClick={(e) => {
            e.stopPropagation();
            onSelect(d);
          }}
        >
          {d.id}
        </Button>
      ),
    },
    {
      title: "Тип",
      width: 125,
      render: (_, d) => (
        <span>
          <Tag color={d.kind === "dent" ? "purple" : "blue"}>
            {d.kind === "dent" ? "Вмятина" : "Коррозия"}
          </Tag>
          {d.kind === "group" && (
            <small className="cell-subtext">Группа · {d.members.length}</small>
          )}
        </span>
      ),
    },
    {
      title: "№ трубы",
      dataIndex: "pipeNumber",
      width: 100,
      sorter: (a, b) =>
        a.pipeNumber.localeCompare(b.pipeNumber, "ru", { numeric: true }),
    },
    numeric("positionM", "Положение, м", 140),
    { title: "Режим", width: 110, render: (_, d) => modeLabel(d) },
    {
      title: "Модель",
      width: 85,
      render: (_, d) => (d.kind === "dent" ? d.model : "—"),
    },
    numeric("lengthMm", "Длина, мм", 108),
    numeric("widthMm", "Ширина, мм", 112),
    numeric("depthMm", "Глубина, мм", 115),
    {
      title: (
        <span>
          Разруш. давление<small className="cell-subtext">МПа</small>
        </span>
      ),
      width: 155,
      render: () => (
        <span className="muted" title="Расчёт не подключён">
          —
        </span>
      ),
    },
    {
      title: "Категория",
      width: 130,
      sorter: (a, b) =>
        (a.demoCategory ?? "Z").localeCompare(b.demoCategory ?? "Z"),
      render: (_, d) => <CategoryBadge defect={d} />,
    },
    {
      title: "Статус",
      width: 210,
      render: (_, d) => <StatusBadge defect={d} />,
    },
  ];
  // rowKey=id нужен React/AntD для устойчивой идентичности строки. scroll ограничивает область таблицы; размеры — решения интерфейса, не параметры трубопровода.
  return (
    <Table<Defect>
      className="defect-table"
      rowKey="id"
      dataSource={defects}
      columns={columns}
      scroll={{ x: 1558, y: "max(240px, calc(100vh - 680px))" }}
      size="middle"
      // Выделение — CSS-класс при совпадении ID, не изменение содержимого записи.
      rowClassName={(d) => (d.id === selectedId ? "selected-row" : "")}
      onRow={(d) => ({
        onClick: () => onSelect(d),
        "aria-selected": d.id === selectedId,
      })}
      // Разворачивать можно только group. Состоянием раскрытия управляет сама библиотека, так как expandedRowKeys извне не передаётся.
      expandable={{
        rowExpandable: (d) => d.kind === "group",
        expandedRowRender: (d) =>
          d.kind === "group" ? (
            <GroupMembers group={d} onSelect={onSelect} />
          ) : null,
        columnWidth: 34,
      }}
      locale={{
        emptyText: (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="Дефекты не найдены"
          >
            <Button onClick={onReset}>Сбросить фильтры</Button>
          </Empty>
        ),
      }}
      // current/pageSize управляются App, total — число отфильтрованных объектов. Table сам выбирает строки страницы; вручную slice здесь не нужен.
      pagination={{
        current: page,
        pageSize,
        total: defects.length,
        showSizeChanger: true,
        pageSizeOptions: [10, 20, 50],
        onChange: onPageChange,
        showTotal: (total, range) =>
          `Записи ${range[0]}–${range[1]} из ${total}`,
        placement: ["bottomEnd"],
      }}
    />
  );
}
