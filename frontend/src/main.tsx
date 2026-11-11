/**
 * Точка входа браузера: ReactDOM монтирует App в div#root из index.html. ConfigProvider задаёт русскую локаль и общую тему Ant Design; ErrorBoundary перехватывает ошибки рендера.
 */
import React from "react";
import ReactDOM from "react-dom/client";
import { ConfigProvider } from "antd";
import ruRU from "antd/locale/ru_RU";
import App from "./Workbench";
import { ErrorBoundary } from "./components/ErrorBoundary";
import "./styles.css";
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={ruRU}
      theme={{
        token: {
          colorPrimary: "#2463eb",
          borderRadius: 6,
          fontFamily: "Inter, Segoe UI, Arial, sans-serif",
          fontSize: 14,
          colorText: "#242a35",
        },
        components: {
          Table: {
            headerBg: "#f7f8fa",
            headerColor: "#687080",
            rowHoverBg: "#f5f8ff",
          },
          Tabs: { horizontalItemGutter: 30 },
        },
      }}
    >
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </ConfigProvider>
  </React.StrictMode>,
);
