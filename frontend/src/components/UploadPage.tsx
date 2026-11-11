import { Alert, Button, Descriptions, Tag, Upload } from "antd";
import {
  InboxOutlined,
  ArrowRightOutlined,
  FileExcelOutlined,
  DeleteOutlined,
} from "@ant-design/icons";
// File — браузерный объект выбранного файла. error — сообщение проверки метаданных, не отчёт чтения книги.
export interface UploadState {
  file: File | null;
  error: string | null;
}
// Проверяем только имя и size. Содержимое файла не читается; переименованный произвольный файл .xlsx может пройти эту ограниченную проверку.
export function validateFileSelection(
  file: Pick<File, "name" | "size">,
): string | null {
  // Регулярное выражение принимает расширения xls/xlsx без учёта регистра; MIME и структуру ZIP/XML не проверяет.
  if (!/\.xlsx?$/i.test(file.name))
    return "Неподдерживаемое расширение. Выберите файл .xlsx или .xls.";
  // Нулевой размер отклоняется; size задан браузером в байтах.
  if (file.size === 0) return "Файл пустой. Выберите другой файл.";
  // 50*1024*1024 — техническое ограничение размера; сообщение использует привычное МБ, фактически это 50 МиБ.
  if (file.size > 50 * 1024 * 1024)
    return "Файл больше 50 МБ. Выберите файл меньшего размера.";
  return null;
}
// beforeUpload возвращает false и останавливает автоматическую отправку Ant Design. onContinue лишь меняет экран, не импортирует файл.
export function UploadPage({
  state,
  onChange,
  onContinue,
}: {
  state: UploadState;
  onChange: (s: UploadState) => void;
  onContinue: () => void;
}) {
  return (
    <div className="upload-page">
      <div className="page-heading">
        <div>
          <div className="eyebrow">ИСТОЧНИК ДАННЫХ</div>
          <h1>Загрузка Excel</h1>
          <p>Выберите выгрузку внутритрубной диагностики</p>
        </div>
        <Tag color="blue">Демонстрационный режим</Tag>
      </div>
      <div className="upload-layout">
        <section className="surface upload-main">
          <h2>Файл диагностики</h2>
          <Upload.Dragger
            style={{ height: 240 }}
            accept=".xlsx,.xls"
            multiple={false}
            showUploadList={false}
            beforeUpload={(file) => {
              const error = validateFileSelection(file);
              onChange({ file: error ? null : file, error });
              return false;
            }}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <h3>Перетащите Excel-файл сюда</h3>
            <p>или нажмите, чтобы выбрать на устройстве</p>
            <span className="muted">.xlsx, .xls · до 50 МБ</span>
          </Upload.Dragger>
          {state.file && (
            <div className="selected-file">
              <FileExcelOutlined />
              <div>
                <strong>{state.file.name}</strong>
                <small>
                  {Math.ceil(state.file.size / 1024)} КБ · выбран локально
                </small>
              </div>
              <Button
                type="text"
                aria-label="Убрать выбранный файл"
                icon={<DeleteOutlined />}
                onClick={() => onChange({ file: null, error: null })}
              />
            </div>
          )}
          {state.error && (
            <Alert
              type="error"
              showIcon
              title="Не удалось выбрать файл"
              description={state.error}
            />
          )}
          <h2>Результат проверки</h2>
          <Alert
            showIcon
            type="warning"
            title="Проверка содержимого не выполнялась"
            description="Загрузка Excel и проверка листов ещё не подключены. Проверяются только расширение, ненулевой размер и ограничение 50 МБ. Файл не отправляется на сервер."
          />
          <Descriptions
            column={1}
            size="small"
            className="upload-checks"
            items={[
              {
                key: "file",
                label: "Файл",
                children: state.file
                  ? "Выбран, содержимое не прочитано"
                  : "Не выбран",
              },
              {
                key: "anom",
                label: "Лист anom",
                children: "Наличие и данные не проверены",
              },
              {
                key: "weld",
                label: "Лист weld",
                children: "Наличие и данные не проверены",
              },
            ]}
          />
          <div className="upload-footer">
            <span>Реестр откроется на встроенных демоданных</span>
            <Button
              type="primary"
              icon={<ArrowRightOutlined />}
              onClick={onContinue}
            >
              Перейти в реестр
            </Button>
          </div>
        </section>
        <aside className="surface upload-guide">
          <h2>Ожидаемые листы</h2>
          <div className="sheet">
            <Tag>anom</Tag>
            <h3>Аномалии</h3>
            <p>
              ID, тип, положение и геометрия дефектов. Для коррозии — записи
              CORR.
            </p>
          </div>
          <div className="sheet">
            <Tag>weld</Tag>
            <h3>Параметры труб</h3>
            <p>
              Связь с трубной секцией, диаметр, толщина стенки и характеристики
              материала.
            </p>
          </div>
          <div className="guide-note">
            В первой версии файл можно выбрать, но импорт ещё не выполняется.
            Реестр использует только демонстрационный набор.
          </div>
        </aside>
      </div>
    </div>
  );
}
