import { useMemo, useState } from "react";
import { Breadcrumb, Button, Select, Tabs, Tag } from "antd";
import { UploadOutlined, InfoCircleOutlined } from "@ant-design/icons";
import { demoDefects, projects } from "./data/demo";
import type {
  Defect,
  DefectFilters as Filters,
  DefectTab,
} from "./types/defect";
import { filterDefects, emptyFilters } from "./utils/filters";
import { Navigation, type Page } from "./components/Navigation";
import { DefectFilters } from "./components/DefectFilters";
import { DefectTable } from "./components/DefectTable";
import { DefectDrawer } from "./components/DefectDrawer";
import { UploadPage, type UploadState } from "./components/UploadPage";
import { MethodologyPage } from "./components/MethodologyPage";
import { ServiceStatus } from "./components/ServiceStatus";
// Главный компонент: владеет состоянием. Дочерние компоненты получают данные через props и сообщают о действиях через callbacks.
export default function App() {
  // Текущий экран. useState возвращает [значение, функцию изменения]; setter вызывает повторный рендер, а не перезагрузку страницы.
  const [page, setPage] = useState<Page>("registry");
  // ID выбранного демопроекта; названия и доступные участки берутся из projects в data/demo.ts.
  const [projectId, setProject] = useState("north");
  // ID участка ограничивает набор записей внутри проекта.
  const [sectionId, setSection] = useState("s1");
  // Вкладка внутри реестра: all / corrosion / dent. Это не отдельный URL.
  const [tab, setTab] = useState<DefectTab>("all");
  // Единый объект фильтров. В нём хранятся введённые пользователем значения, а не результаты расчёта.
  const [filters, setFilters] = useState<Filters>(emptyFilters);
  // Выбранная запись целиком. null означает, что пользователь ещё не выбирал дефект.
  const [selected, setSelected] = useState<Defect | null>(null);
  // Видимость отделена от selected: закрытие панели не удаляет выделение строки.
  const [drawerOpen, setDrawerOpen] = useState(false);
  // Номер страницы Ant Design, начиная с 1, а не с 0.
  const [current, setCurrent] = useState(1);
  // Количество объектов на странице; участники раскрытой группы не считаются отдельными объектами реестра.
  const [pageSize, setPageSize] = useState(10);
  // File остаётся в памяти браузера; здесь нет загрузки на сервер или чтения Excel.
  const [upload, setUpload] = useState<UploadState>({
    file: null,
    error: null,
  });
  // find возвращает проект по ID. ! — утверждение для TypeScript, НЕ проверка во время выполнения. Допущение безопасно для закрытого списка projects; при API нужно обрабатывать отсутствие.
  const project = projects.find((p) => p.id === projectId)!;
  // Первый отбор: проект И участок. useMemo кеширует результат до изменения зависимостей в квадратных скобках; не является хранилищем и не нужен для корректности.
  const scoped = useMemo(
    () =>
      demoDefects.filter(
        (d) => d.projectId === projectId && d.sectionId === sectionId,
      ),
    [projectId, sectionId],
  );
  // Второй отбор: вкладка и пользовательские фильтры. Источник — scoped, функция — utils/filters.ts. Исходный массив не изменяется.
  const filtered = useMemo(
    () => filterDefects(scoped, tab, filters),
    [scoped, tab, filters],
  );
  // map извлекает номера труб, Set убирает повторы, spread [...] превращает Set в массив. sort здесь строковый; для будущих произвольных номеров лучше числовое сравнение.
  const pipes = [...new Set(scoped.map((d) => d.pipeNumber))].sort();
  // При новом фильтре возвращаемся на страницу 1, иначе прежняя страница может отсутствовать в коротком результате.
  const updateFilters = (next: Filters) => {
    setFilters(next);
    setCurrent(1);
  };
  // Создаём новый объект пустых фильтров через spread. Сам emptyFilters не мутируем.
  const reset = () => updateFilters({ ...emptyFilters });
  // Обработчик клика: сохранить объект и открыть панель. Расчёт при выборе НЕ запускается.
  const select = (d: Defect) => {
    setSelected(d);
    setDrawerOpen(true);
  };
  // При смене проекта/участка очищаем фильтры и выбранный дефект; вкладка типа при этом сохраняется.
  const resetContext = () => {
    reset();
    setSelected(null);
    setDrawerOpen(false);
  };
  // Тернарный оператор выбирает текст по текущему экрану. Это отображение, не маршрутизация.
  const title =
    page === "registry"
      ? "Реестр дефектов"
      : page === "upload"
        ? "Загрузка данных"
        : "Методика и справка";
  // JSX описывает дерево интерфейса. value + onChange делают поля управляемыми: источник истины — React state. Ниже map превращает справочники в options для Select.
  return (
    <div className="app">
      <header className="topbar">
        <a
          href="#"
          className="brand"
          onClick={(e) => {
            e.preventDefault();
            setPage("registry");
          }}
        >
          <span className="brand-mark">В</span>
          <div>
            <strong>ВТД Аналитика</strong>
            <small className="brand-description">
              Анализ дефектов газопроводов
            </small>
          </div>
        </a>
        <div className="context-selectors">
          <label>
            Проект
            <Select
              aria-label="Проект"
              value={projectId}
              options={projects.map((p) => ({ value: p.id, label: p.name }))}
              onChange={(id) => {
                setProject(id);
                setSection(projects.find((p) => p.id === id)!.sections[0].id);
                resetContext();
              }}
            />
          </label>
          <span className="context-separator" />
          <label>
            Участок
            <Select
              aria-label="Участок"
              value={sectionId}
              options={project.sections.map((s) => ({
                value: s.id,
                label: s.name,
              }))}
              onChange={(id) => {
                setSection(id);
                resetContext();
              }}
            />
          </label>
        </div>
        <div className="topbar-right">
          <Tag color="blue">Демопроект</Tag>
          <div className="user-avatar" title="Локальный пользователь">
            ЛП
          </div>
        </div>
      </header>
      <div className="app-body">
        <Navigation page={page} onChange={setPage} />
        <main>
          <div className="workspace-meta">
            <Breadcrumb items={[{ title: "Рабочая область" }, { title }]} />
            <ServiceStatus />
          </div>
          {page === "registry" ? (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">ВНУТРИТРУБНАЯ ДИАГНОСТИКА</div>
                  <h1>
                    Общий реестр дефектов{" "}
                    <span className="heading-count">{scoped.length}</span>
                  </h1>
                  <p>
                    Список коррозионных дефектов и вмятин по выбранному участку
                  </p>
                </div>
                <Button
                  icon={<UploadOutlined />}
                  onClick={() => setPage("upload")}
                >
                  Загрузить Excel
                </Button>
              </div>
              <div className="demo-banner">
                <InfoCircleOutlined />
                <div>
                  <strong>Демонстрационный режим</strong>
                  <span>
                    Все исходные числа и категории — демоданные. Расчёт не
                    подключён.
                  </span>
                </div>
                <Tag>Этап 1</Tag>
              </div>
              <section className="surface registry">
                <Tabs
                  activeKey={tab}
                  onChange={(key) => {
                    setTab(key as DefectTab);
                    setCurrent(1);
                  }}
                  items={[
                    {
                      key: "all",
                      label: (
                        <>
                          Все дефекты{" "}
                          <span className="tab-count">{scoped.length}</span>
                        </>
                      ),
                    },
                    {
                      key: "corrosion",
                      label: (
                        <>
                          Коррозия{" "}
                          <span className="tab-count">
                            {scoped.filter((d) => d.kind !== "dent").length}
                          </span>
                        </>
                      ),
                    },
                    {
                      key: "dent",
                      label: (
                        <>
                          Вмятины{" "}
                          <span className="tab-count">
                            {scoped.filter((d) => d.kind === "dent").length}
                          </span>
                        </>
                      ),
                    },
                  ]}
                />
                <DefectFilters
                  value={filters}
                  pipes={pipes}
                  onChange={updateFilters}
                  onReset={reset}
                />
                <div className="table-caption">
                  <span>
                    Найдено объектов: <strong>{filtered.length}</strong>
                    <span className="caption-separator">/</span>
                    {scoped.length}
                  </span>
                  <span>Нажмите на строку, чтобы открыть карточку</span>
                </div>
                <DefectTable
                  defects={filtered}
                  selectedId={selected?.id}
                  onSelect={select}
                  page={current}
                  pageSize={pageSize}
                  onPageChange={(p, size) => {
                    setCurrent(size !== pageSize ? 1 : p);
                    setPageSize(size);
                  }}
                  onReset={reset}
                />
              </section>
              <div className="registry-footnote">
                Группы считаются отдельными объектами. Их состав раскрывается
                стрелкой слева от ID. Все категории в таблице —
                демонстрационные.
              </div>
            </>
          ) : page === "upload" ? (
            <UploadPage
              state={upload}
              onChange={setUpload}
              onContinue={() => setPage("registry")}
            />
          ) : (
            <MethodologyPage />
          )}
          <footer className="workspace-footer">
            <span>ВТД Аналитика</span>
            <span>Локальная рабочая среда · версия 0.1.0</span>
          </footer>
        </main>
      </div>
      <DefectDrawer
        defect={selected}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onSelect={select}
      />
    </div>
  );
}
