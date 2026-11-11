/**
 * Меню Ant Design получает выбранную страницу из App. Нажатие передаёт key обратно через onChange. Page — допустимые имена экранов. Это переключение JSX внутри одного URL, без react-router.
 */
import {
  DatabaseOutlined,
  UploadOutlined,
  FileTextOutlined,
  SafetyCertificateOutlined,
} from "@ant-design/icons";
import { Menu } from "antd";
export type Page = "registry" | "upload" | "methodology";
export function Navigation({
  page,
  onChange,
}: {
  page: Page;
  onChange: (page: Page) => void;
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-label">РАБОЧАЯ ОБЛАСТЬ</div>
      <nav aria-label="Основная навигация">
        <Menu
          mode="inline"
          selectedKeys={[page]}
          onClick={({ key }) => onChange(key as Page)}
          items={[
            {
              key: "upload",
              icon: <UploadOutlined />,
              label: "Загрузка данных",
            },
            {
              key: "registry",
              icon: <DatabaseOutlined />,
              label: "Реестр дефектов",
            },
            {
              key: "methodology",
              icon: <FileTextOutlined />,
              label: "Методика и справка",
            },
          ]}
        />
      </nav>
      <div className="sidebar-bottom">
        <SafetyCertificateOutlined />
        <strong>Локальная версия</strong>
        <span>Данные остаются на устройстве</span>
        <small>ВТД Аналитика · 0.1.0</small>
      </div>
    </aside>
  );
}
