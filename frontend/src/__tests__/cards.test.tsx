/**
 * Компонентные тесты рендерят настоящие React-карточки в jsdom, имитируют клики userEvent и проверяют подписи/callbacks. vi.fn — наблюдаемая заглушка обработчика.
 */
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DefectDrawer } from "../components/DefectDrawer";
import { demoDefects } from "../data/demo";
describe("Карточки дефектов", () => {
  it.each([
    [0, "Одиночная коррозия"],
    [1, "Групповая коррозия"],
    [3, "Вмятина"],
  ] as const)("открывает вариант %s", async (index, name) => {
    render(
      <DefectDrawer
        defect={demoDefects[index]}
        open
        onClose={vi.fn()}
        onSelect={vi.fn()}
      />,
    );
    const panel = screen.getByRole("dialog");
    expect(within(panel).getByText(name)).toBeInTheDocument();
    expect(
      within(panel).getByRole("tab", { name: "Данные" }),
    ).toBeInTheDocument();
    expect(
      within(panel).getByRole("button", { name: /Пересчитать/ }),
    ).toBeDisabled();
    await userEvent.click(within(panel).getByRole("tab", { name: "Расчёт" }));
    expect(
      within(panel).getAllByText("Расчёт не подключён").length,
    ).toBeGreaterThan(0);
  });
  it("показывает участников группы и открывает выбранного участника", async () => {
    const select = vi.fn();
    render(
      <DefectDrawer
        defect={demoDefects[1]}
        open
        onClose={vi.fn()}
        onSelect={select}
      />,
    );
    await userEvent.click(screen.getByRole("tab", { name: "Состав группы" }));
    await userEvent.click(screen.getByRole("button", { name: "DEMO-0002-1" }));
    expect(select.mock.calls[0][0].id).toBe("DEMO-0002-1");
  });
  it("отделяет предварительный результат РМ3 и вызывает закрытие", async () => {
    const close = vi.fn();
    render(
      <DefectDrawer
        defect={demoDefects[5]}
        open
        onClose={close}
        onSelect={vi.fn()}
      />,
    );
    await userEvent.click(screen.getByRole("tab", { name: "Результат" }));
    expect(
      screen.getByText("Ожидает дополнительного расчёта РМ2"),
    ).toBeInTheDocument();
    expect(screen.getByText("B · демо · не окончательная")).toBeInTheDocument();
    expect(screen.getByText("Не определена")).toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("button", { name: "Вернуться в реестр" }),
    );
    expect(close).toHaveBeenCalledOnce();
  });
});
