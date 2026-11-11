/**
 * Unit-тесты чистой фильтрации: ожидаемые ID и количества взяты из фиксированного demo.ts. Проверяются комбинации и запрет трактовать предварительную B РМ3 как итоговую.
 */
import { demoDefects } from "../data/demo";
import { filterDefects } from "../utils/filters";
import type { DefectFilters } from "../types/defect";
describe("Фильтрация демоданных", () => {
  it("разделяет вкладки и возвращает полный набор без фильтров", () => {
    expect(filterDefects(demoDefects, "all", { query: "" })).toHaveLength(30);
    expect(
      filterDefects(demoDefects, "dent", { query: "" }).every(
        (d) => d.kind === "dent",
      ),
    ).toBe(true);
    expect(
      filterDefects(demoDefects, "corrosion", { query: "" }).every(
        (d) => d.kind !== "dent",
      ),
    ).toBe(true);
  });
  it("нормализует ID и находит родительскую группу по ID участника", () => {
    expect(
      filterDefects(demoDefects, "all", { query: " demo-0001 " }).map(
        (d) => d.id,
      ),
    ).toEqual(["DEMO-0001"]);
    expect(
      filterDefects(demoDefects, "all", { query: "DEMO-0002-2" }).map(
        (d) => d.id,
      ),
    ).toEqual(["DEMO-0002"]);
  });
  it.each<[Partial<DefectFilters>, string]>([
    [{ pipe: "1362" }, "DEMO-0001"],
    [{ category: "A" }, "DEMO-0001"],
    [{ kind: "group" }, "DEMO-0002"],
    [{ corrosionMode: "internal" }, "DEMO-0027"],
    [{ model: "РМ3" }, "DEMO-0006"],
    [{ category: "unset" }, "DEMO-0006"],
  ])("фильтр %j оставляет ожидаемый объект", (filter, id) => {
    const rows = filterDefects(demoDefects, "all", { query: "", ...filter });
    expect(rows.length).toBeGreaterThan(0);
    expect(rows.length).toBeLessThan(demoDefects.length);
    expect(rows.map((d) => d.id)).toContain(id);
  });
  it("комбинирует фильтры и корректно возвращает пустой список", () => {
    expect(
      filterDefects(demoDefects, "all", {
        query: "DEMO-0001",
        pipe: "1362",
        category: "A",
        kind: "single",
        corrosionMode: "external",
      }),
    ).toHaveLength(1);
    expect(
      filterDefects(demoDefects, "dent", {
        query: "",
        corrosionMode: "external",
      }),
    ).toEqual([]);
    expect(filterDefects(demoDefects, "all", { query: "unknown" })).toEqual([]);
  });
  it("не выдаёт предварительную категорию РМ3 за окончательную", () => {
    const rm3 = demoDefects.filter(
      (d) => d.kind === "dent" && d.model === "РМ3",
    );
    expect(rm3.length).toBeGreaterThan(0);
    rm3.forEach((d) => {
      expect(d.demoCategory).toBeNull();
      expect(d.result.finalCategory).toBeNull();
      expect(d.result.status).toBe("awaiting_rm2");
    });
    expect(filterDefects(rm3, "all", { query: "", category: "B" })).toEqual([]);
  });
});
