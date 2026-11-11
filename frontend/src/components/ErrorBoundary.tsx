/**
 * Классовый React Error Boundary: getDerivedStateFromError переключает экран на сообщение об ошибке рендера потомка. Не ловит автоматически ошибки event handlers и произвольных async callbacks; fetch обрабатывается отдельно в ServiceStatus.
 */
import { Component, type ReactNode } from "react";
import { Button, Result } from "antd";
export class ErrorBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? (
      <Result
        status="error"
        title="Не удалось отобразить приложение"
        subTitle="Обновите страницу. Выбранный файл не передавался на сервер."
        extra={
          <Button onClick={() => window.location.reload()}>
            Обновить страницу
          </Button>
        }
      />
    ) : (
      this.props.children
    );
  }
}
