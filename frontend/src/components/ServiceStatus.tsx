import { useEffect, useState } from "react";
import { Button, Tooltip } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
// Единственный сетевой запрос приложения — проверка здоровья API. Список дефектов через сеть не загружается.
export function ServiceStatus() {
  const [state, setState] = useState<"loading" | "online" | "offline">(
    "loading",
  );
  // Счётчик попыток — зависимость эффекта; увеличение запускает новую проверку.
  const [attempt, retry] = useState(0);
  // Эффект выполняется после монтирования и при изменении attempt; возвращённая функция вызывается перед повторным эффектом и при удалении компонента.
  useEffect(() => {
    // AbortController отменяет fetch. Он не останавливает FastAPI и не меняет данные реестра.
    const abort = new AbortController();
    // Флаг не позволяет завершившемуся старому Promise менять уже неактуальное состояние компонента.
    let mounted = true;
    // Через 4000 мс отменяем запрос: интерфейс не должен бесконечно показывать ожидание.
    const timeout = setTimeout(() => abort.abort(), 4000);
    setState("loading");
    // Относительный /api/health проходит через proxy Vite: префикс /api удаляется, запрос попадает в FastAPI /health на 8000.
    fetch("/api/health", { signal: abort.signal })
      .then(async (r) => {
        // Успешного HTTP-кода мало: JSON должен содержать status='ok'. Ошибка HTTP, JSON или сети переводится в offline через catch.
        if (!r.ok || (await r.json()).status !== "ok")
          throw new Error("Health check failed");
        if (mounted) setState("online");
      })
      .catch(() => {
        if (mounted) setState("offline");
      })
      .finally(() => clearTimeout(timeout));
    // Уборка эффекта: снимаем флаг, удаляем таймер, отменяем запрос. В React StrictMode при разработке возможен дополнительный цикл запуска/уборки.
    return () => {
      mounted = false;
      clearTimeout(timeout);
      abort.abort();
    };
  }, [attempt]);
  return (
    <div className={`service-status ${state}`}>
      <i />
      <Tooltip
        title={
          state === "offline"
            ? "FastAPI недоступен. Демореестр продолжает работать локально."
            : "Проверка доступности FastAPI /health"
        }
      >
        <span>
          {state === "online"
            ? "Backend доступен"
            : state === "loading"
              ? "Проверка backend…"
              : "Backend недоступен"}
        </span>
      </Tooltip>
      {state === "offline" && (
        <Button
          size="small"
          type="text"
          aria-label="Повторить проверку backend"
          icon={<ReloadOutlined />}
          onClick={() => retry((n) => n + 1)}
        />
      )}
    </div>
  );
}
