/**
 * Карточка одиночной коррозии: данные делегируются CardData; ссылки на СТО и текст — статическая справка. Функция расчёта здесь не вызывается.
 */
import { Alert } from "antd";
import type { SingleCorrosion } from "../../types/defect";
import { CardData } from "./CardData";
export function SingleCorrosionData({ defect }: { defect: SingleCorrosion }) {
  return <CardData defect={defect} />;
}
export function SingleCorrosionCalculation() {
  return (
    <div className="card-section">
      <h3>Одиночная коррозия</h3>
      <p>
        Планируемая методика: СТО Lamart 2-2.3-112-2007, §6.1 и §6.2;
        коэффициенты и критерий — §5.2.
      </p>
      <Alert
        type="info"
        showIcon
        title="Расчёт не подключён"
        description="Применимость методики и одиночность дефекта ещё не проверялись."
      />
      <div className="formula-placeholder">
        <strong>Формулы и подстановка значений</strong>
        <span>Появятся после подключения и проверки расчётного модуля.</span>
      </div>
    </div>
  );
}
