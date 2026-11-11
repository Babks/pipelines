/**
 * Контракты TypeScript существуют на этапе проверки/сборки, но не валидируют JSON в браузере. Объединения через | описывают допустимые варианты. kind/status — признаки для сужения типа. null — явно отсутствующее значение; ? — необязательное поле. Mm/Mpa/M в именах фиксируют единицы. isDemo:true допускает только демозапись. Нельзя считать успешный tsc доказательством правильности входного Excel.
 */
export type Category = "A" | "B" | "C";
export type CorrosionMode = "external" | "internal";
export type DentModel = "РМ1" | "РМ2" | "РМ3";
export type DefectKind = "single" | "group" | "dent";
export type CalculationResult =
  | { status: "not_connected"; pressureMpa: null; finalCategory: null }
  | {
      status: "missing_data";
      pressureMpa: null;
      finalCategory: null;
      missingFields: string[];
    }
  | {
      status: "awaiting_rm2";
      pressureMpa: null;
      finalCategory: null;
      preliminaryDemoCategory: Category;
    };

export interface PipeParameters {
  diameterMm: number | null;
  wallMm: number | null;
  tensileMpa: number | null;
  workingPressureMpa: number | null;
}
interface BaseDefect {
  id: string;
  projectId: string;
  sectionId: string;
  pipeNumber: string;
  positionM: number;
  clockPosition: string;
  lengthMm: number;
  widthMm: number;
  depthMm: number | null;
  pipe: PipeParameters;
  isDemo: true;
  demoCategory: Category | null;
  result: CalculationResult;
}
export interface SingleCorrosion extends BaseDefect {
  kind: "single";
  corrosionMode: CorrosionMode;
}
export interface GroupCorrosion extends BaseDefect {
  kind: "group";
  corrosionMode: CorrosionMode;
  members: SingleCorrosion[];
  effectiveGeometry: null;
  criticalCombination: null;
}
export interface Dent extends BaseDefect {
  kind: "dent";
  model: DentModel;
}
export type Defect = SingleCorrosion | GroupCorrosion | Dent;
export type DefectTab = "all" | "corrosion" | "dent";
export interface DefectFilters {
  query: string;
  pipe?: string;
  category?: Category | "unset";
  kind?: DefectKind;
  corrosionMode?: CorrosionMode;
  model?: DentModel;
}
